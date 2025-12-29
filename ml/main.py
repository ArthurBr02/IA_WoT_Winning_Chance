import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, QuantileTransformer, PowerTransformer
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import glob
import os
import joblib
import random
import argparse
from typing import Optional

# --- CONFIGURATION ---
DATA_PATH = "./data"  # Ton dossier
FEATURE_COLS = ['battles', 'overallWN8', 'overallWNX', 'winrate', 'dpg',
                'assist', 'frags', 'survival', 'spots', 'cap', 'def', 'xp', 'kd']
MAX_PLAYERS = 15
BATCH_SIZE = 64
LEARNING_RATE = 0.0001
EPOCHS = 200

# Cross-validation / training tuning
N_SPLITS = 6
EARLY_STOPPING_PATIENCE = 12
WEIGHT_DECAY = 1e-4
MAX_GRAD_NORM = 1.0

# Scaling
# RobustScaler is often better than StandardScaler when features have heavy tails/outliers.
SCALER_TYPE = "robust"  # standard|robust|minmax|quantile|power

# Feature engineering (global/team deltas)
GLOBAL_FEATURES = [
    "delta_mean_wn8",
    "delta_mean_wr",
    "delta_top3_wn8",
    "delta_sum_battles",
    "delta_mean_dpg",
    "delta_mean_xp",
]
GLOBAL_SCALER_TYPE = SCALER_TYPE

# Model selection
MODEL_TYPE = "attention"  # cnn|deepset|attention

# Evaluation / logging
PRINT_EVERY = 1

# Dimension de l'embedding (vecteur qui représente la map)
# Une taille de 8 à 16 suffit généralement pour une cinquantaine de maps.
MAP_EMBEDDING_DIM = 16

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Hardware: {device}")


def seed_everything(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True


def create_scaler(scaler_type: str):
    scaler_type = (scaler_type or "").strip().lower()
    if scaler_type == "standard":
        return StandardScaler()
    if scaler_type == "robust":
        return RobustScaler(with_centering=True, with_scaling=True)
    if scaler_type == "minmax":
        return MinMaxScaler()
    if scaler_type == "quantile":
        return QuantileTransformer(output_distribution="normal", random_state=42)
    if scaler_type == "power":
        return PowerTransformer(method="yeo-johnson", standardize=True)
    raise ValueError(f"Unknown scaler_type={scaler_type}. Expected one of: standard|robust|minmax|quantile|power")


def _safe_topk_mean(s: pd.Series, k: int) -> float:
    if len(s) == 0:
        return 0.0
    return float(s.head(k).mean())


def compute_global_features(team1_df: pd.DataFrame, team2_df: pd.DataFrame) -> np.ndarray:
    """Compute engineered global features for a match: (team1 - team2)."""
    t1 = team1_df.sort_values('overallWN8', ascending=False)
    t2 = team2_df.sort_values('overallWN8', ascending=False)

    delta_mean_wn8 = float(t1['overallWN8'].mean() - t2['overallWN8'].mean())
    delta_mean_wr = float(t1['winrate'].mean() - t2['winrate'].mean())
    delta_top3_wn8 = _safe_topk_mean(t1['overallWN8'], 3) - _safe_topk_mean(t2['overallWN8'], 3)
    delta_sum_battles = float(t1['battles'].sum() - t2['battles'].sum())
    delta_mean_dpg = float(t1['dpg'].mean() - t2['dpg'].mean())
    delta_mean_xp = float(t1['xp'].mean() - t2['xp'].mean())

    return np.array(
        [
            delta_mean_wn8,
            delta_mean_wr,
            float(delta_top3_wn8),
            delta_sum_battles,
            delta_mean_dpg,
            delta_mean_xp,
        ],
        dtype=np.float32,
    )

# --- 1. GESTION DES MAPS ---
# On a besoin d'un dictionnaire pour convertir l'ID du CSV en index (0, 1, 2...)
# On le remplira lors du chargement des données.
map_to_idx = {}


def get_padded_team_matrix(team_df):
    """Trie et pad les joueurs -> (MAX_PLAYERS, num_features)."""
    sorted_team = team_df.sort_values(by='overallWN8', ascending=False)
    stats = sorted_team[FEATURE_COLS].to_numpy(dtype=np.float32)

    num_players = stats.shape[0]
    if num_players < MAX_PLAYERS:
        padding = np.zeros((MAX_PLAYERS - num_players, len(FEATURE_COLS)), dtype=np.float32)
        full_team = np.vstack([stats, padding])
    elif num_players > MAX_PLAYERS:
        full_team = stats[:MAX_PLAYERS, :]
    else:
        full_team = stats
    return full_team


def load_data(path):
    global map_to_idx
    files = sorted(glob.glob(os.path.join(path, "*.csv")))
    print(f"Lecture de {len(files)} fichiers...")

    X_stats_list = []
    X_maps_list = []
    X_global_list = []
    y_list = []

    # Pour construire l'index des maps
    current_map_idx = 0

    for f in files:
        try:
            df = pd.read_csv(f, sep=';', decimal=',')
            t1 = df[df['spawn'] == 1]
            t2 = df[df['spawn'] == 2]

            if len(t1) == 0 or len(t2) == 0: continue

            # --- TRAITEMENT DE LA MAP ---
            # On récupère l'ID de la map (colonne 'map', première ligne)
            raw_map_id = df['map'].iloc[0]

            # Si on ne connaît pas cette map, on l'ajoute au dictionnaire
            if raw_map_id not in map_to_idx:
                map_to_idx[raw_map_id] = current_map_idx
                current_map_idx += 1

            # On stocke l'index converti (ex: map 19 devient index 3)
            map_index = map_to_idx[raw_map_id]

            # --- TRAITEMENT DES JOUEURS ---
            mat1 = get_padded_team_matrix(t1)
            mat2 = get_padded_team_matrix(t2)

            # Shape: (2*MAX_PLAYERS, num_features) = (30, 13)
            match_stats = np.vstack([mat1, mat2]).astype(np.float32, copy=False)

            target = t1['target'].iloc[0]

            global_feats = compute_global_features(t1, t2)

            X_stats_list.append(match_stats)
            X_maps_list.append(map_index)
            X_global_list.append(global_feats)
            y_list.append(target)

        except Exception as e:
            # print(f"Erreur fichier {f}: {e}")
            continue

    print(f"Nombre de maps uniques trouvées : {len(map_to_idx)}")
    return np.array(X_stats_list), np.array(X_maps_list), np.array(X_global_list), np.array(y_list)


# --- 2. DATASET MODIFIÉ ---

class WotDataset(Dataset):
    def __init__(
        self,
        X_stats,
        X_maps,
        X_global,
        y,
        scaler=None,
        global_scaler=None,
        fit_scaler=False,
        scaler_type: str = SCALER_TYPE,
        global_scaler_type: str = GLOBAL_SCALER_TYPE,
    ):
        self.y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        self.maps = torch.tensor(X_maps, dtype=torch.long)  # Les indices doivent être des entiers (Long)

        # X_stats expected shape: (N, 2*MAX_PLAYERS, num_features)
        if X_stats.ndim != 3:
            raise ValueError(f"X_stats must be 3D (N, 2*MAX_PLAYERS, num_features), got shape={X_stats.shape}")

        n = X_stats.shape[0]
        flat = X_stats.reshape(n, -1)

        if fit_scaler:
            self.scaler = create_scaler(scaler_type)
            flat = self.scaler.fit_transform(flat)

            self.global_scaler = create_scaler(global_scaler_type)
            global_scaled = self.global_scaler.fit_transform(X_global)
        else:
            self.scaler = scaler
            flat = self.scaler.transform(flat)

            self.global_scaler = global_scaler
            global_scaled = self.global_scaler.transform(X_global)

        # Back to grid for CNN: (N, 1, 2*MAX_PLAYERS, num_features)
        grid = flat.reshape(n, 1, X_stats.shape[1], X_stats.shape[2]).astype(np.float32, copy=False)
        self.X_stats = torch.tensor(grid, dtype=torch.float32)
        self.X_global = torch.tensor(global_scaled.astype(np.float32, copy=False), dtype=torch.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        # On retourne un tuple : (Stats, Map), Label
        return (self.X_stats[idx], self.maps[idx], self.X_global[idx]), self.y[idx]


# --- 3. MODÈLE HYBRIDE (Stats + Embedding) ---

class WinPredictorCNNWithMap(nn.Module):
    def __init__(self, num_maps: int):
        super().__init__()

        if num_maps <= 0:
            raise ValueError(f"num_maps must be >= 1, got {num_maps}")

        # 1) Map embedding
        self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)

        # 2) CNN stats encoder: input (B, 1, 2*MAX_PLAYERS, num_features)
        self.stats_cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1)),
            nn.Dropout2d(0.10),

            nn.Conv2d(32, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1)),
            nn.Dropout2d(0.15),

            nn.Conv2d(64, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        stats_feat_dim = 128
        combined_input_size = stats_feat_dim + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)

        self.head = nn.Sequential(
            nn.Linear(combined_input_size, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(128, 1)
        )

    def forward(self, x_stats_grid: torch.Tensor, x_map: torch.Tensor, x_global: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x_stats_grid: (B, 1, H, W)
        stats_feat = self.stats_cnn(x_stats_grid).flatten(1)
        embs = self.map_embedding(x_map)
        if x_global is None:
            x_global = torch.zeros((stats_feat.size(0), len(GLOBAL_FEATURES)), device=stats_feat.device, dtype=stats_feat.dtype)
        combined = torch.cat([stats_feat, embs, x_global], dim=1)
        return self.head(combined)

class AttentionPooling(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        # Le réseau d'attention calcule un score pour chaque joueur
        self.attn_net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def forward(self, x, mask):
        # x: (Batch, Players, Features)
        # mask: (Batch, Players, 1)
        scores = self.attn_net(x)  # (B, P, 1)
        
        # On met -inf là où c'est du padding pour que le softmax donne 0
        scores = scores.masked_fill(mask == 0, -1e9)
        
        # On calcule les poids (qui somment à 1 sur l'axe des joueurs)
        weights = torch.softmax(scores, dim=1)
        
        # Somme pondérée
        return torch.sum(x * weights, dim=1)


class WinPredictorAttention(nn.Module):
    def __init__(self, num_maps, num_features):
        super().__init__()
        self.map_emb = nn.Embedding(num_maps, MAP_EMBEDDING_DIM)

        # Encoder chaque joueur individuellement (Shared MLP)
        self.player_encoder = nn.Sequential(
            nn.Linear(num_features, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Attention Pooling
        self.attn = nn.Sequential(
            nn.Linear(128, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

        # Classification finale
        # Entrée = (Team1_Emb + Team2_Emb + Diff + Map + Global)
        combined_dim = (128 * 3) + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)

        self.head = nn.Sequential(
            nn.Linear(combined_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1)
        )

    def get_team_embedding(self, x, mask):
        # x: (B, 15, F)
        enc = self.player_encoder(x)  # (B, 15, 128)

        # Calcul des scores d'attention
        scores = self.attn(enc)  # (B, 15, 1)
        scores = scores.masked_fill(mask == 0, -1e9)
        weights = torch.softmax(scores, dim=1)

        # Somme pondérée
        team_vector = torch.sum(enc * weights, dim=1)  # (B, 128)
        return team_vector

    def forward(self, x_stats, x_map, x_global):
        # Accept either (B, 1, H, W) or (B, H, W)
        if x_stats.ndim == 4:
            x_stats = x_stats.squeeze(1)

        # Sépare T1 et T2
        # x_stats shape: (B, 30, Features)
        t1 = x_stats[:, :MAX_PLAYERS, :]
        t2 = x_stats[:, MAX_PLAYERS:, :]

        # Créer les masques (si joueur est tout à 0 -> mask=0)
        m1 = (t1.abs().sum(dim=-1, keepdim=True) > 0).float()
        m2 = (t2.abs().sum(dim=-1, keepdim=True) > 0).float()

        emb1 = self.get_team_embedding(t1, m1)
        emb2 = self.get_team_embedding(t2, m2)

        map_v = self.map_emb(x_map)

        # Features d'interaction
        feat_diff = emb1 - emb2

        combined = torch.cat([emb1, emb2, feat_diff, map_v, x_global], dim=1)
        return self.head(combined)

class WinPredictorDeepSetWithMap(nn.Module):
    """DeepSets-style model for per-player tabular stats.

    - Applies a shared MLP (phi) to each player.
    - Aggregates with a permutation-invariant pooling per team (masked mean).
    - Combines both team embeddings + map embedding into a final head.
    """

    def __init__(self, num_maps: int, num_features: int = len(FEATURE_COLS)):
        super().__init__()

        if num_maps <= 0:
            raise ValueError(f"num_maps must be >= 1, got {num_maps}")

        self.num_features = int(num_features)
        self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)

        phi_dim = 128

        self.phi = nn.Sequential(
            nn.Linear(self.num_features, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.10),
            nn.Linear(128, phi_dim),
            nn.ReLU(inplace=True),
        )

        # Attention pooling per team (instead of masked mean)
        self.pool_t1 = AttentionPooling(phi_dim)
        self.pool_t2 = AttentionPooling(phi_dim)

        # Combine team representations: t1, t2, (t1-t2), (t1*t2)
        team_pair_dim = phi_dim * 4
        combined_dim = team_pair_dim + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES)

        self.head = nn.Sequential(
            nn.Linear(combined_dim, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.15),
            nn.Linear(64, 1),
        )

    def forward(self, x_stats_grid: torch.Tensor, x_map: torch.Tensor, x_global: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Accept either (B, 1, H, W) or (B, H, W)
        if x_stats_grid.ndim == 4:
            # (B, 1, H, W) -> (B, H, W)
            x = x_stats_grid.squeeze(1)
        else:
            x = x_stats_grid

        # x: (B, 2*MAX_PLAYERS, num_features)
        if x.ndim != 3:
            raise ValueError(f"Expected stats tensor with 3 dims (B, players, features), got shape={tuple(x.shape)}")

        # Padding mask: rows that are all zeros are treated as padding.
        # mask shape: (B, P, 1)
        mask = (x.abs().sum(dim=-1, keepdim=True) > 0).float()

        # Per-player embedding (shared)
        # phi expects (..., F), so flatten players
        b, p, f = x.shape
        if f != self.num_features:
            raise ValueError(f"Expected num_features={self.num_features}, got {f}")

        x_flat = x.reshape(b * p, f)
        e_flat = self.phi(x_flat)
        e = e_flat.reshape(b, p, -1)

        # Split teams
        e1, e2 = e[:, :MAX_PLAYERS, :], e[:, MAX_PLAYERS:MAX_PLAYERS * 2, :]
        m1, m2 = mask[:, :MAX_PLAYERS, :], mask[:, MAX_PLAYERS:MAX_PLAYERS * 2, :]

        # Attention pooling (mask-aware)
        t1 = self.pool_t1(e1, m1)
        t2 = self.pool_t2(e2, m2)

        pair = torch.cat([t1, t2, (t1 - t2), (t1 * t2)], dim=1)

        embs = self.map_embedding(x_map)
        if x_global is None:
            x_global = torch.zeros((pair.size(0), len(GLOBAL_FEATURES)), device=pair.device, dtype=pair.dtype)
        combined = torch.cat([pair, embs, x_global], dim=1)
        return self.head(combined)


# --- 4. ENTRAÎNEMENT ---

@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader) -> tuple[float, float]:
    model.eval()
    all_probs: list[float] = []
    all_targets: list[float] = []
    correct = 0
    total = 0

    for (stats_grid, maps, global_feats), targets in loader:
        stats_grid = stats_grid.to(device)
        maps = maps.to(device)
        global_feats = global_feats.to(device)
        targets = targets.to(device)

        logits = model(stats_grid, maps, global_feats)
        probs = torch.sigmoid(logits)
        preds = (probs > 0.5).float()

        total += targets.size(0)
        correct += (preds == targets).sum().item()

        all_probs.extend(probs.squeeze(1).detach().cpu().tolist())
        all_targets.extend(targets.squeeze(1).detach().cpu().tolist())

    acc = (correct / max(1, total))
    # roc_auc_score requires both classes present
    try:
        auc = float(roc_auc_score(all_targets, all_probs))
    except Exception:
        auc = float('nan')
    return acc, auc


def train_one_fold(
    fold: int,
    X_stats: np.ndarray,
    X_maps: np.ndarray,
    X_global: np.ndarray,
    y: np.ndarray,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    num_maps: int,
    scaler_type: str,
    global_scaler_type: str,
) -> tuple[dict, dict]:
    X_train_s, X_val_s = X_stats[train_idx], X_stats[val_idx]
    X_train_m, X_val_m = X_maps[train_idx], X_maps[val_idx]
    X_train_g, X_val_g = X_global[train_idx], X_global[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    train_ds = WotDataset(
        X_train_s,
        X_train_m,
        X_train_g,
        y_train,
        fit_scaler=True,
        scaler_type=scaler_type,
        global_scaler_type=global_scaler_type,
    )
    val_ds = WotDataset(
        X_val_s,
        X_val_m,
        X_val_g,
        y_val,
        scaler=train_ds.scaler,
        global_scaler=train_ds.global_scaler,
        fit_scaler=False,
        scaler_type=scaler_type,
        global_scaler_type=global_scaler_type,
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, drop_last=False)

    if MODEL_TYPE == "cnn":
        model = WinPredictorCNNWithMap(num_maps=num_maps).to(device)
    elif MODEL_TYPE == "deepset":
        model = WinPredictorDeepSetWithMap(num_maps=num_maps, num_features=len(FEATURE_COLS)).to(device)
    elif MODEL_TYPE == "attention":
        model = WinPredictorAttention(num_maps=num_maps, num_features=len(FEATURE_COLS)).to(device)
    else:
        raise ValueError(f"Unknown MODEL_TYPE={MODEL_TYPE}. Expected 'cnn', 'deepset' or 'attention'.")

    # Handle imbalance with pos_weight
    pos = float(np.sum(y_train == 1))
    neg = float(np.sum(y_train == 0))
    if pos > 0:
        pos_weight = torch.tensor([neg / pos], dtype=torch.float32, device=device)
    else:
        pos_weight = None

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3)

    best = {
        'epoch': -1,
        'val_auc': -1.0,
        'val_acc': 0.0,
        'state_dict': None,
        'scaler': train_ds.scaler,
        'global_scaler': train_ds.global_scaler,
    }
    epochs_no_improve = 0

    print(f"\n--- Fold {fold} ---")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0

        for (stats_grid, maps, global_feats), targets in train_loader:
            stats_grid = stats_grid.to(device)
            maps = maps.to(device)
            global_feats = global_feats.to(device)
            targets = targets.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(stats_grid, maps, global_feats)
            loss = criterion(logits, targets)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            optimizer.step()
            running_loss += float(loss.item())

        val_acc, val_auc = evaluate(model, val_loader)
        scheduler.step(val_auc if not np.isnan(val_auc) else val_acc)

        if epoch % PRINT_EVERY == 0:
            lr = optimizer.param_groups[0]['lr']
            print(f"Fold {fold} | Epoch {epoch:03d} | Loss {running_loss / max(1, len(train_loader)):.4f} | Val Acc {val_acc * 100:.2f}% | Val AUC {val_auc:.4f} | LR {lr:.2e}")

        improved = (not np.isnan(val_auc) and val_auc > best['val_auc'])
        if improved:
            best['epoch'] = epoch
            best['val_auc'] = float(val_auc)
            best['val_acc'] = float(val_acc)
            best['state_dict'] = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= EARLY_STOPPING_PATIENCE:
            print(f"Fold {fold} early stopping at epoch {epoch} (best epoch {best['epoch']}, best AUC {best['val_auc']:.4f}).")
            break

    metrics = {
        'fold': fold,
        'best_epoch': best['epoch'],
        'best_val_acc': best['val_acc'],
        'best_val_auc': best['val_auc'],
    }
    artifacts = {
        'state_dict': best['state_dict'],
        'scaler': best['scaler'],
        'global_scaler': best['global_scaler'],
    }
    return metrics, artifacts


def train_process():
    seed_everything(42)

    # A. Chargement
    # X_stats: (N, 2*MAX_PLAYERS, num_features), X_maps: (N,), X_global: (N, G), y: (N,)
    X_stats, X_maps, X_global, y = load_data(DATA_PATH)

    if len(X_stats) == 0:
        print("Erreur: Pas de données.")
        return

    num_maps = len(map_to_idx)
    if num_maps <= 0:
        print("Erreur: Pas de maps.")
        return

    # Ensure y is 0/1 ints for StratifiedKFold
    y_int = y.astype(int)

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

    fold_metrics: list[dict] = []
    best_overall = {
        'val_auc': -1.0,
        'fold': -1,
        'state_dict': None,
        'scaler': None,
        'global_scaler': None,
    }

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_stats, y_int), start=1):
        metrics, artifacts = train_one_fold(
            fold=fold,
            X_stats=X_stats,
            X_maps=X_maps,
            X_global=X_global,
            y=y_int,
            train_idx=train_idx,
            val_idx=val_idx,
            num_maps=num_maps,
            scaler_type=SCALER_TYPE,
            global_scaler_type=GLOBAL_SCALER_TYPE,
        )
        fold_metrics.append(metrics)

        if metrics['best_val_auc'] > best_overall['val_auc']:
            best_overall['val_auc'] = metrics['best_val_auc']
            best_overall['fold'] = fold
            best_overall['state_dict'] = artifacts['state_dict']
            best_overall['scaler'] = artifacts['scaler']
            best_overall['global_scaler'] = artifacts['global_scaler']

    aucs = [m['best_val_auc'] for m in fold_metrics if not np.isnan(m['best_val_auc'])]
    accs = [m['best_val_acc'] for m in fold_metrics]

    print("\n--- Cross-validation summary ---")
    for m in fold_metrics:
        print(f"Fold {m['fold']} | Best epoch {m['best_epoch']} | Best Val Acc {m['best_val_acc'] * 100:.2f}% | Best Val AUC {m['best_val_auc']:.4f}")

    if len(aucs) > 0:
        print(f"Mean Val AUC: {float(np.mean(aucs)):.4f} (+/- {float(np.std(aucs)):.4f})")
    print(f"Mean Val Acc: {float(np.mean(accs)) * 100:.2f}% (+/- {float(np.std(accs)) * 100:.2f}%)")
    print(f"Best fold: {best_overall['fold']} (AUC {best_overall['val_auc']:.4f})")

    # Save best fold model + scaler + map dict
    if best_overall['state_dict'] is None:
        print("Erreur: aucun modèle sauvegardable (state_dict None).")
        return

    torch.save(best_overall['state_dict'], "wot_model_map.pth")
    joblib.dump(
        {
            'players': best_overall['scaler'],
            'global': best_overall['global_scaler'],
            'scaler_type': SCALER_TYPE,
            'global_scaler_type': GLOBAL_SCALER_TYPE,
            'global_features': GLOBAL_FEATURES,
        },
        "scaler.pkl",
    )
    joblib.dump(map_to_idx, "map_index.pkl")
    print("Modèle (best fold), scaler et map_index sauvegardés.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WoT win chance trainer (CNN + map embedding + K-fold CV)")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--folds", type=int, default=N_SPLITS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--print-every", type=int, default=PRINT_EVERY)
    parser.add_argument("--scaler", type=str, default=SCALER_TYPE, choices=["standard", "robust", "minmax", "quantile", "power"])
    parser.add_argument("--global-scaler", type=str, default=GLOBAL_SCALER_TYPE, choices=["standard", "robust", "minmax", "quantile", "power"])
    parser.add_argument("--model", type=str, default=MODEL_TYPE, choices=["cnn", "deepset", "attention"])
    args = parser.parse_args()

    # Override globals (simple + explicit)
    EPOCHS = int(args.epochs)
    N_SPLITS = int(args.folds)
    BATCH_SIZE = int(args.batch_size)
    LEARNING_RATE = float(args.lr)
    PRINT_EVERY = int(args.print_every)
    SCALER_TYPE = str(args.scaler)
    GLOBAL_SCALER_TYPE = str(args.global_scaler)
    MODEL_TYPE = str(args.model)

    train_process()