import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import glob
import os
import joblib

# --- CONFIGURATION ---
DATA_PATH = "./data"  # Ton dossier
FEATURE_COLS = ['battles', 'overallWN8', 'overallWNX', 'winrate', 'dpg',
                'assist', 'frags', 'survival', 'spots', 'cap', 'def', 'xp', 'kd']
MAX_PLAYERS = 15
BATCH_SIZE = 64
LEARNING_RATE = 0.001
EPOCHS = 100

# Dimension de l'embedding (vecteur qui représente la map)
# Une taille de 8 à 16 suffit généralement pour une cinquantaine de maps.
MAP_EMBEDDING_DIM = 10

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Hardware: {device}")

# --- 1. GESTION DES MAPS ---
# On a besoin d'un dictionnaire pour convertir l'ID du CSV en index (0, 1, 2...)
# On le remplira lors du chargement des données.
map_to_idx = {}


def get_padded_team_vector(team_df):
    """ Trie et pad les joueurs (inchangé) """
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
    return full_team.flatten()


def load_data(path):
    global map_to_idx
    files = glob.glob(os.path.join(path, "*.csv"))
    print(f"Lecture de {len(files)} fichiers...")

    X_stats_list = []
    X_maps_list = []
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
            vec1 = get_padded_team_vector(t1)
            vec2 = get_padded_team_vector(t2)
            match_stats = np.concatenate([vec1, vec2])

            target = t1['target'].iloc[0]

            X_stats_list.append(match_stats)
            X_maps_list.append(map_index)
            y_list.append(target)

        except Exception as e:
            # print(f"Erreur fichier {f}: {e}")
            continue

    print(f"Nombre de maps uniques trouvées : {len(map_to_idx)}")
    return np.array(X_stats_list), np.array(X_maps_list), np.array(y_list)


# --- 2. DATASET MODIFIÉ ---

class WotDataset(Dataset):
    def __init__(self, X_stats, X_maps, y, scaler=None, fit_scaler=False):
        self.y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)
        self.maps = torch.tensor(X_maps, dtype=torch.long)  # Les indices doivent être des entiers (Long)

        if fit_scaler:
            self.scaler = StandardScaler()
            self.X_stats = self.scaler.fit_transform(X_stats)
        else:
            self.scaler = scaler
            self.X_stats = self.scaler.transform(X_stats)

        self.X_stats = torch.tensor(self.X_stats, dtype=torch.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        # On retourne un tuple : (Stats, Map), Label
        return (self.X_stats[idx], self.maps[idx]), self.y[idx]


# --- 3. MODÈLE HYBRIDE (Stats + Embedding) ---

class WinPredictorWithMap(nn.Module):
    def __init__(self, num_maps, stats_input_size):
        super(WinPredictorWithMap, self).__init__()

        # 1. Branche pour la Map (Embedding)
        self.map_embedding = nn.Embedding(num_embeddings=num_maps, embedding_dim=MAP_EMBEDDING_DIM)

        # 2. Le réseau principal
        # L'entrée du réseau sera : Taille vecteur stats + Taille vecteur map
        combined_input_size = stats_input_size + MAP_EMBEDDING_DIM

        self.net = nn.Sequential(
            nn.Linear(combined_input_size, 1024),
            nn.BatchNorm1d(1024),
            nn.ReLU(),
            nn.Dropout(0.4),

            nn.Linear(1024, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(512, 128),
            nn.ReLU(),

            nn.Linear(128, 1)
        )

    def forward(self, x_stats, x_map):
        # A. On transforme l'index de la map en vecteur
        # x_map shape: (Batch_Size) -> embs shape: (Batch_Size, MAP_EMBEDDING_DIM)
        embs = self.map_embedding(x_map)

        # B. On concatène les stats et la map
        # dim=1 signifie qu'on colle sur la largeur (les colonnes)
        combined = torch.cat([x_stats, embs], dim=1)

        # C. Passage dans le réseau dense
        return self.net(combined)


# --- 4. ENTRAÎNEMENT ---

def train_process():
    # A. Chargement
    # X_stats: (N, 390), X_maps: (N,), y: (N,)
    X_stats, X_maps, y = load_data(DATA_PATH)

    if len(X_stats) == 0:
        print("Erreur: Pas de données.")
        return

    # Taille d'entrée stats (390)
    STATS_DIM = X_stats.shape[1]
    # Nombre de maps uniques pour dimensionner l'embedding
    NUM_MAPS = len(map_to_idx)

    # B. Split
    # On doit splitter les 3 tableaux en même temps
    X_train_s, X_test_s, X_train_m, X_test_m, y_train, y_test = train_test_split(
        X_stats, X_maps, y, test_size=0.2, random_state=42
    )

    # C. Datasets
    train_ds = WotDataset(X_train_s, X_train_m, y_train, fit_scaler=True)
    test_ds = WotDataset(X_test_s, X_test_m, y_test, scaler=train_ds.scaler, fit_scaler=False)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    # D. Modèle
    model = WinPredictorWithMap(num_maps=NUM_MAPS, stats_input_size=STATS_DIM).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print("\n--- Start Training ---")
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0

        for (stats, maps), targets in train_loader:
            # Envoi GPU (Maps doit être des entiers Long)
            stats, maps = stats.to(device), maps.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()

            # On passe les DEUX entrées au modèle
            outputs = model(stats, maps)

            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for (stats, maps), targets in test_loader:
                    stats, maps = stats.to(device), maps.to(device)
                    targets = targets.to(device)

                    outputs = model(stats, maps)
                    predicted = (torch.sigmoid(outputs) > 0.5).float()

                    total += targets.size(0)
                    correct += (predicted == targets).sum().item()

            print(
                f"Epoch {epoch + 1:03d} | Loss: {train_loss / len(train_loader):.4f} | Test Acc: {100 * correct / total:.2f}%")

    # E. Sauvegarde
    torch.save(model.state_dict(), "wot_model_map.pth")
    joblib.dump(train_ds.scaler, "scaler.pkl")
    # TRES IMPORTANT : Sauvegarder le dictionnaire des maps !
    # Sinon on ne saura pas que "Malinovka" = index 3 lors de la prédiction
    joblib.dump(map_to_idx, "map_index.pkl")
    print("Modèle et dictionnaires sauvegardés.")


if __name__ == "__main__":
    train_process()