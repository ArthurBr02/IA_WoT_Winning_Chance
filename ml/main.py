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
# Player numeric features (per-row). Strings are handled separately (embeddings).
# Note: tankId is intentionally ignored (indicative only, not a ranking feature).
PLAYER_NUMERIC_COLS = [
    'battles', 'overallWN8', 'overallWNX', 'winrate', 'dpg',
    'assist', 'frags', 'survival', 'spots', 'cap', 'def', 'xp', 'kd',
    # tank-level stats
    'tankWN8', 'tankWNX', 'tankWinrate', 'tankDpg', 'tankAssist', 'tankKpg',
    'tankDmgRatio', 'tankSurvival', 'tankXp', 'tankHitratio', 'tankSpots',
    'tankArmoreff', 'tankMoe', 'tankMastery', 'tankKd',
]

PLAYER_CATEGORICAL_COLS = ['tankRole', 'tankVehicleClass', 'tankNation']

# Backward-compatible alias (old name used in several places)
FEATURE_COLS = PLAYER_NUMERIC_COLS
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

# Categorical embeddings (per-player)
ROLE_EMBEDDING_DIM = 4
VEHICLE_CLASS_EMBEDDING_DIM = 4
NATION_EMBEDDING_DIM = 4

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
    needed = ['overallWN8', 'winrate', 'battles', 'dpg', 'xp']
    team1_df = _ensure_columns(team1_df, needed, default=0.0)
    team2_df = _ensure_columns(team2_df, needed, default=0.0)

    t1 = team1_df.sort_values('overallWN8', ascending=False)
    t2 = team2_df.sort_values('overallWN8', ascending=False)

    # Ensure numeric operations are safe
    for c in needed:
        t1[c] = pd.to_numeric(t1[c], errors='coerce').fillna(0.0)
        t2[c] = pd.to_numeric(t2[c], errors='coerce').fillna(0.0)

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

# Categorical vocabularies (0 reserved for PAD/UNK)
role_to_idx = {}
vehicle_class_to_idx = {}
nation_to_idx = {}


def _cat_to_index(value, mapping: dict) -> int:
    """Maps a raw categorical value to an integer index.

    Index 0 is reserved for PAD/UNK.
    New categories discovered during training are added with indices starting at 1.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    s = str(value).strip()
    if s == "" or s.lower() in {"null", "none", "nan"}:
        return 0
    if s not in mapping:
        mapping[s] = len(mapping) + 1
    return int(mapping[s])


def _ensure_columns(df: pd.DataFrame, cols: list[str], default=0.0) -> pd.DataFrame:
    """Ensure columns exist; if missing, create them with a default value."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        for c in missing:
            df[c] = default
    return df


def get_padded_team_data(team_df: pd.DataFrame):
    """Sort players and pad/truncate to MAX_PLAYERS.

    Returns:
      - numeric_stats: (MAX_PLAYERS, num_numeric_features)
      - cat_indices: (MAX_PLAYERS, 3) for (role, vehicleClass, nation)
    """
    global role_to_idx, vehicle_class_to_idx, nation_to_idx

    team_df = _ensure_columns(team_df, PLAYER_NUMERIC_COLS, default=0.0)
    team_df = _ensure_columns(team_df, PLAYER_CATEGORICAL_COLS, default=None)

    sorted_team = team_df.sort_values(by='overallWN8', ascending=False)

    numeric = sorted_team[PLAYER_NUMERIC_COLS].copy()
    numeric = numeric.apply(pd.to_numeric, errors='coerce').fillna(0.0)
    stats = numeric.to_numpy(dtype=np.float32, copy=False)

    # Categories (string/object) -> indices
    roles = [_cat_to_index(v, role_to_idx) for v in sorted_team['tankRole'].tolist()]
    vclasses = [_cat_to_index(v, vehicle_class_to_idx) for v in sorted_team['tankVehicleClass'].tolist()]
    nations = [_cat_to_index(v, nation_to_idx) for v in sorted_team['tankNation'].tolist()]
    cats = np.stack([roles, vclasses, nations], axis=1).astype(np.int64, copy=False)

    num_players = stats.shape[0]
    if num_players < MAX_PLAYERS:
        padding_stats = np.zeros((MAX_PLAYERS - num_players, len(PLAYER_NUMERIC_COLS)), dtype=np.float32)
        stats_full = np.vstack([stats, padding_stats])
        padding_cats = np.zeros((MAX_PLAYERS - num_players, 3), dtype=np.int64)
        cats_full = np.vstack([cats, padding_cats])
    elif num_players > MAX_PLAYERS:
        stats_full = stats[:MAX_PLAYERS, :]
        cats_full = cats[:MAX_PLAYERS, :]
    else:
        stats_full = stats
        cats_full = cats

    return stats_full, cats_full


def load_data(path):
    global map_to_idx, role_to_idx, vehicle_class_to_idx, nation_to_idx
    files = sorted(glob.glob(os.path.join(path, "*.csv")))
    print(f"Lecture de {len(files)} fichiers...")

    X_stats_list = []
    X_maps_list = []
    X_global_list = []
    X_cats_list = []
    y_list = []

    # Pour construire l'index des maps
    current_map_idx = 0

    for f in files:
        try:
            df = pd.read_csv(
                f,
                sep=';',
                decimal=',',
                na_values=['null', 'NULL', 'None', 'none', 'nan', 'NaN', ''],
                keep_default_na=True,
            )

            # Robust typing for key columns
            if 'spawn' in df.columns:
                df['spawn'] = pd.to_numeric(df['spawn'], errors='coerce')
            if 'target' in df.columns:
                df['target'] = pd.to_numeric(df['target'], errors='coerce')

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
            mat1, cat1 = get_padded_team_data(t1)
            mat2, cat2 = get_padded_team_data(t2)

            # Shape: (2*MAX_PLAYERS, num_features) = (30, 13)
            match_stats = np.vstack([mat1, mat2]).astype(np.float32, copy=False)
            match_cats = np.vstack([cat1, cat2]).astype(np.int64, copy=False)

            target = int(t1['target'].iloc[0])

            global_feats = compute_global_features(t1, t2)

            X_stats_list.append(match_stats)
            X_maps_list.append(map_index)
            X_global_list.append(global_feats)
            X_cats_list.append(match_cats)
            y_list.append(target)

        except Exception as e:
            # print(f"Erreur fichier {f}: {e}")
            continue

    print(f"Nombre de maps uniques trouvées : {len(map_to_idx)}")
    print(
        "Vocabulaires catégories | "
        f"roles={len(role_to_idx)} | vehicleClass={len(vehicle_class_to_idx)} | nation={len(nation_to_idx)}"
    )
    return (
        np.array(X_stats_list),
        np.array(X_maps_list),
        np.array(X_global_list),
        np.array(X_cats_list),
        np.array(y_list),
    )


# --- 2. DATASET MODIFIÉ ---

class WotDataset(Dataset):
    def __init__(
        self,
        X_stats,
        X_maps,
        X_global,
        X_cats,
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

        if X_cats is None:
            raise ValueError("X_cats is required with the new dataset format (categorical tank fields).")
        if X_cats.ndim != 3 or X_cats.shape[1] != X_stats.shape[1] or X_cats.shape[2] != 3:
            raise ValueError(
                f"X_cats must be (N, 2*MAX_PLAYERS, 3), got shape={getattr(X_cats, 'shape', None)}"
            )

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
        self.X_cats = torch.tensor(X_cats.astype(np.int64, copy=False), dtype=torch.long)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        # On retourne un tuple : (Stats, Map), Label
        return (self.X_stats[idx], self.maps[idx], self.X_global[idx], self.X_cats[idx]), self.y[idx]


# --- 3. MODÈLE HYBRIDE (Stats + Embedding) ---

class WinPredictorCNNWithMap(nn.Module):
    def __init__(self, num_maps: int, num_roles: int, num_vehicle_classes: int, num_nations: int):
        super().__init__()

        if num_maps <= 0:
            raise ValueError(f"num_maps must be >= 1, got {num_maps}")

        # 1) Map embedding
        self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)

        # 1b) Per-player categorical embeddings, pooled to a fixed-size vector
        self.role_emb = nn.Embedding(num_embeddings=max(1, num_roles), embedding_dim=ROLE_EMBEDDING_DIM)
        self.vclass_emb = nn.Embedding(num_embeddings=max(1, num_vehicle_classes), embedding_dim=VEHICLE_CLASS_EMBEDDING_DIM)
        self.nation_emb = nn.Embedding(num_embeddings=max(1, num_nations), embedding_dim=NATION_EMBEDDING_DIM)

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
        cat_feat_dim = ROLE_EMBEDDING_DIM + VEHICLE_CLASS_EMBEDDING_DIM + NATION_EMBEDDING_DIM
        combined_input_size = stats_feat_dim + MAP_EMBEDDING_DIM + len(GLOBAL_FEATURES) + cat_feat_dim

        self.head = nn.Sequential(
            nn.Linear(combined_input_size, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(128, 1)
        )

    def forward(
        self,
        x_stats_grid: torch.Tensor,
        x_map: torch.Tensor,
        x_global: Optional[torch.Tensor] = None,
        x_cats: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # x_stats_grid: (B, 1, H, W)
        stats_feat = self.stats_cnn(x_stats_grid).flatten(1)
        embs = self.map_embedding(x_map)
        if x_global is None:
            x_global = torch.zeros((stats_feat.size(0), len(GLOBAL_FEATURES)), device=stats_feat.device, dtype=stats_feat.dtype)
        if x_cats is None:
            cat_feat = torch.zeros(
                (stats_feat.size(0), ROLE_EMBEDDING_DIM + VEHICLE_CLASS_EMBEDDING_DIM + NATION_EMBEDDING_DIM),
                device=stats_feat.device,
                dtype=stats_feat.dtype,
            )
        else:
            # x_cats: (B, 2*MAX_PLAYERS, 3) -> average pooling over players (ignores padding=0)
            roles = x_cats[:, :, 0]
            vclasses = x_cats[:, :, 1]
            nations = x_cats[:, :, 2]
            mask = (x_cats.sum(dim=-1) > 0).float().unsqueeze(-1)  # (B, P, 1)
            denom = mask.sum(dim=1).clamp_min(1.0)
            r = self.role_emb(roles)
            vc = self.vclass_emb(vclasses)
            na = self.nation_emb(nations)
            pooled = ((torch.cat([r, vc, na], dim=-1) * mask).sum(dim=1) / denom)
            cat_feat = pooled

        combined = torch.cat([stats_feat, embs, x_global, cat_feat], dim=1)
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
    def __init__(self, num_maps, num_features, num_roles: int, num_vehicle_classes: int, num_nations: int):
        super().__init__()
        self.map_emb = nn.Embedding(num_maps, MAP_EMBEDDING_DIM)

        # Per-player categorical embeddings (concatenated to numeric features)
        self.role_emb = nn.Embedding(num_embeddings=max(1, num_roles), embedding_dim=ROLE_EMBEDDING_DIM)
        self.vclass_emb = nn.Embedding(num_embeddings=max(1, num_vehicle_classes), embedding_dim=VEHICLE_CLASS_EMBEDDING_DIM)
        self.nation_emb = nn.Embedding(num_embeddings=max(1, num_nations), embedding_dim=NATION_EMBEDDING_DIM)

        self.num_numeric_features = int(num_features)
        self.num_cat_features = ROLE_EMBEDDING_DIM + VEHICLE_CLASS_EMBEDDING_DIM + NATION_EMBEDDING_DIM

        # Encoder chaque joueur individuellement (Shared MLP)
        self.player_encoder = nn.Sequential(
            nn.Linear(self.num_numeric_features + self.num_cat_features, 128),
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

    def forward(self, x_stats, x_map, x_global, x_cats: Optional[torch.Tensor] = None):
        # Accept either (B, 1, H, W) or (B, H, W)
        if x_stats.ndim == 4:
            x_stats = x_stats.squeeze(1)

        # x_stats: (B, 30, num_numeric)
        if x_cats is None:
            # Provide empty embeddings if categories not provided
            b = x_stats.size(0)
            x_cat_emb = torch.zeros(
                (b, x_stats.size(1), self.num_cat_features),
                device=x_stats.device,
                dtype=x_stats.dtype,
            )
        else:
            # x_cats: (B, 30, 3)
            roles = x_cats[:, :, 0]
            vclasses = x_cats[:, :, 1]
            nations = x_cats[:, :, 2]
            x_cat_emb = torch.cat([
                self.role_emb(roles),
                self.vclass_emb(vclasses),
                self.nation_emb(nations),
            ], dim=-1)

        x_stats = torch.cat([x_stats, x_cat_emb], dim=-1)

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

    def __init__(
        self,
        num_maps: int,
        num_features: int = len(FEATURE_COLS),
        num_roles: int = 1,
        num_vehicle_classes: int = 1,
        num_nations: int = 1,
    ):
        super().__init__()

        if num_maps <= 0:
            raise ValueError(f"num_maps must be >= 1, got {num_maps}")

        self.num_features = int(num_features)
        self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)

        # Per-player categorical embeddings (concatenated to numeric features)
        self.role_emb = nn.Embedding(num_embeddings=max(1, num_roles), embedding_dim=ROLE_EMBEDDING_DIM)
        self.vclass_emb = nn.Embedding(num_embeddings=max(1, num_vehicle_classes), embedding_dim=VEHICLE_CLASS_EMBEDDING_DIM)
        self.nation_emb = nn.Embedding(num_embeddings=max(1, num_nations), embedding_dim=NATION_EMBEDDING_DIM)
        self.num_cat_features = ROLE_EMBEDDING_DIM + VEHICLE_CLASS_EMBEDDING_DIM + NATION_EMBEDDING_DIM

        phi_dim = 128

        self.phi = nn.Sequential(
            nn.Linear(self.num_features + self.num_cat_features, 128),
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

    def forward(
        self,
        x_stats_grid: torch.Tensor,
        x_map: torch.Tensor,
        x_global: Optional[torch.Tensor] = None,
        x_cats: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # Accept either (B, 1, H, W) or (B, H, W)
        if x_stats_grid.ndim == 4:
            # (B, 1, H, W) -> (B, H, W)
            x = x_stats_grid.squeeze(1)
        else:
            x = x_stats_grid

        # x: (B, 2*MAX_PLAYERS, num_numeric_features)
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

        if x_cats is None:
            cat_emb = torch.zeros(
                (b, p, self.num_cat_features),
                device=x.device,
                dtype=x.dtype,
            )
        else:
            roles = x_cats[:, :, 0]
            vclasses = x_cats[:, :, 1]
            nations = x_cats[:, :, 2]
            cat_emb = torch.cat([
                self.role_emb(roles),
                self.vclass_emb(vclasses),
                self.nation_emb(nations),
            ], dim=-1)

        x_full = torch.cat([x, cat_emb], dim=-1)
        x_flat = x_full.reshape(b * p, f + self.num_cat_features)
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

    for (stats_grid, maps, global_feats, cats), targets in loader:
        stats_grid = stats_grid.to(device)
        maps = maps.to(device)
        global_feats = global_feats.to(device)
        cats = cats.to(device)
        targets = targets.to(device)

        logits = model(stats_grid, maps, global_feats, cats)
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
    X_cats: np.ndarray,
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
    X_train_c, X_val_c = X_cats[train_idx], X_cats[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    train_ds = WotDataset(
        X_train_s,
        X_train_m,
        X_train_g,
        X_train_c,
        y_train,
        fit_scaler=True,
        scaler_type=scaler_type,
        global_scaler_type=global_scaler_type,
    )
    val_ds = WotDataset(
        X_val_s,
        X_val_m,
        X_val_g,
        X_val_c,
        y_val,
        scaler=train_ds.scaler,
        global_scaler=train_ds.global_scaler,
        fit_scaler=False,
        scaler_type=scaler_type,
        global_scaler_type=global_scaler_type,
    )

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, drop_last=False)

    num_roles = len(role_to_idx) + 1
    num_vehicle_classes = len(vehicle_class_to_idx) + 1
    num_nations = len(nation_to_idx) + 1

    if MODEL_TYPE == "cnn":
        model = WinPredictorCNNWithMap(
            num_maps=num_maps,
            num_roles=num_roles,
            num_vehicle_classes=num_vehicle_classes,
            num_nations=num_nations,
        ).to(device)
    elif MODEL_TYPE == "deepset":
        model = WinPredictorDeepSetWithMap(
            num_maps=num_maps,
            num_features=len(FEATURE_COLS),
            num_roles=num_roles,
            num_vehicle_classes=num_vehicle_classes,
            num_nations=num_nations,
        ).to(device)
    elif MODEL_TYPE == "attention":
        model = WinPredictorAttention(
            num_maps=num_maps,
            num_features=len(FEATURE_COLS),
            num_roles=num_roles,
            num_vehicle_classes=num_vehicle_classes,
            num_nations=num_nations,
        ).to(device)
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
        # Primary selection score: AUC when available else Acc
        'score': float('-inf'),
        'state_dict': None,
        'scaler': train_ds.scaler,
        'global_scaler': train_ds.global_scaler,
    }
    epochs_no_improve = 0

    print(f"\n--- Fold {fold} ---")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0

        for (stats_grid, maps, global_feats, cats), targets in train_loader:
            stats_grid = stats_grid.to(device)
            maps = maps.to(device)
            global_feats = global_feats.to(device)
            cats = cats.to(device)
            targets = targets.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(stats_grid, maps, global_feats, cats)
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

        score = float(val_auc) if not np.isnan(val_auc) else float(val_acc)

        # Improve on score; if tied, prefer higher accuracy.
        improved = (score > best['score']) or (score == best['score'] and float(val_acc) > best['val_acc'])
        if improved:
            best['epoch'] = epoch
            best['val_auc'] = float(val_auc)
            best['val_acc'] = float(val_acc)
            best['score'] = float(score)
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
        'best_score': best['score'],
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
    # X_stats: (N, 2*MAX_PLAYERS, num_features), X_maps: (N,), X_global: (N, G), X_cats: (N, 2*MAX_PLAYERS, 3), y: (N,)
    X_stats, X_maps, X_global, X_cats, y = load_data(DATA_PATH)

    if len(X_stats) == 0:
        print("Erreur: Pas de données.")
        return

    num_maps = len(map_to_idx)
    if num_maps <= 0:
        print("Erreur: Pas de maps.")
        return

    # Ensure y is 0/1 ints for StratifiedKFold
    y_int = y.astype(int)

    # StratifiedKFold constraint: n_splits <= n_samples and <= min(class_counts)
    n_samples = int(len(y_int))
    class_counts = np.bincount(y_int.astype(int), minlength=2)
    min_class = int(class_counts.min()) if class_counts.size > 0 else 0
    effective_splits = int(min(N_SPLITS, n_samples, min_class))

    if effective_splits < 2:
        raise ValueError(
            f"Not enough data to run StratifiedKFold: n_samples={n_samples}, class_counts={class_counts.tolist()}, requested n_splits={N_SPLITS}. "
            "Collect more battles or use fewer folds via --folds."
        )

    if effective_splits != int(N_SPLITS):
        print(
            f"Adjusting n_splits from {N_SPLITS} to {effective_splits} "
            f"(n_samples={n_samples}, class_counts={class_counts.tolist()})."
        )

    skf = StratifiedKFold(n_splits=effective_splits, shuffle=True, random_state=42)

    fold_metrics: list[dict] = []
    best_overall = {
        'val_auc': float('nan'),
        'val_acc': 0.0,
        'score': float('-inf'),
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
            X_cats=X_cats,
            y=y_int,
            train_idx=train_idx,
            val_idx=val_idx,
            num_maps=num_maps,
            scaler_type=SCALER_TYPE,
            global_scaler_type=GLOBAL_SCALER_TYPE,
        )
        fold_metrics.append(metrics)

        m_auc = metrics['best_val_auc']
        m_acc = metrics['best_val_acc']
        m_score = metrics.get('best_score', float(m_auc) if not np.isnan(m_auc) else float(m_acc))

        better = (m_score > best_overall['score']) or (m_score == best_overall['score'] and float(m_acc) > float(best_overall['val_acc']))
        if better:
            best_overall['score'] = float(m_score)
            best_overall['val_auc'] = float(m_auc)
            best_overall['val_acc'] = float(m_acc)
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

    if not np.isnan(best_overall['val_auc']):
        print(f"Best fold: {best_overall['fold']} (AUC {best_overall['val_auc']:.4f}, Acc {best_overall['val_acc'] * 100:.2f}%)")
    else:
        print(f"Best fold: {best_overall['fold']} (Acc {best_overall['val_acc'] * 100:.2f}%)")

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
            'player_numeric_cols': PLAYER_NUMERIC_COLS,
            'player_categorical_cols': PLAYER_CATEGORICAL_COLS,
            'categorical_mappings': {
                'tankRole': role_to_idx,
                'tankVehicleClass': vehicle_class_to_idx,
                'tankNation': nation_to_idx,
            },
            'categorical_embedding_dims': {
                'tankRole': ROLE_EMBEDDING_DIM,
                'tankVehicleClass': VEHICLE_CLASS_EMBEDDING_DIM,
                'tankNation': NATION_EMBEDDING_DIM,
            },
        },
        "scaler.pkl",
    )
    joblib.dump(map_to_idx, "map_index.pkl")
    joblib.dump(
        {
            'tankRole': role_to_idx,
            'tankVehicleClass': vehicle_class_to_idx,
            'tankNation': nation_to_idx,
        },
        "categorical_index.pkl",
    )
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