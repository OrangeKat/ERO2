# Projet ERO2 - Analyse de la Moulinette

Ce projet vise à modéliser et analyser le système de correction automatique (moulinette) de l'école sous l'angle de la théorie des files d'attente, en comparant les résultats de simulation avec les modèles théoriques.

## 0. Modèles Théoriques
Le projet inclut des calculs théoriques pour valider les simulations :
- **M/M/1** : File à un serveur, arrivées Poisson, service exponentiel.
- **M/M/k** : File à $k$ serveurs.
- **M/G/1** : File à un serveur avec distribution de service générale (ex: constante).

## 1. Modélisation Waterfall

### Système d'attente proposé
Le modèle Waterfall peut être modélisé comme un réseau de files d'attente en série (Réseau de Jackson) :
- **Étage 1 (Exécution) :** Système **M/M/K** avec une file FIFO. Les arrivées suivent un processus de Poisson ($\lambda$), le service est exponentiel ($\mu_s$) avec $K$ serveurs.
- **Étage 2 (Envoi Front) :** Système **M/M/1** avec une file FIFO. Le taux d'arrivée est le taux de sortie de l'étage 1 (égal à $\lambda$ en régime permanent si le système est stable).

### Analyse des files finies ($k_s, k_f$)
- **Refus de push tag :** Si la file d'exécution est pleine ($k_s$), la probabilité de rejet est donnée par la formule d'Erlang-B (pour un système sans file d'attente) ou les probabilités d'état d'un système M/M/K/N.
- **Pages blanches :** Si la file de renvoi est pleine ($k_f$), le résultat est perdu, ce qui génère un retour vide pour l'étudiant.

### Solution de Back-up
- **Impact :** Le back-up permet de sauvegarder le résultat en amont. Si la file 2 est pleine, on ne perd pas la donnée, mais le temps de séjour "perçu" peut augmenter si l'utilisateur doit re-solliciter le système ou si le système retente l'envoi.
- **Avantages du back-up aléatoire :** Réduit la charge de stockage et l'overhead d'écriture systématique tout en offrant une protection statistique contre les pics de charge ponctuels.

## 2. Channels and Dams

### Problématique
La population ING (fréquente) "noie" la population PREPA (rare mais longue).

### Solutions proposées
- **Barrage (Dam) :** Introduire un blocage périodique pour la population ING permet de vider la file et de laisser la place aux PREPA.
- **Alternative (File de Priorité) :** Utiliser une file **M/M/1 avec priorité** ou **M/G/1 avec priorité**. Donner une priorité plus élevée à la population PREPA (moins fréquente) permet de réduire drastiquement leur temps de séjour sans impacter massivement la population ING en moyenne.

## Installation

### Option 1 : Avec `uv` (recommandé)

Ce projet utilise `uv` pour la gestion des dépendances et de l'environnement virtuel.

1.  **Installer uv** (si pas déjà présent) :
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Créer l'environnement et installer les dépendances** :
    ```bash
    uv venv venv
    source venv/bin/activate
    uv pip install -r requirements.txt
    ```

### Option 2 : Sans `uv` (Standard)

Si vous préférez utiliser les outils Python standards :

1.  **Créer l'environnement virtuel** :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Installer les dépendances** :
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Utilisation

### Exécuter l'étude complète
Pour lancer toutes les simulations et générer les graphiques/rapports :
```bash
python3 main.py
```

### Explorer les scénarios
Vous pouvez exécuter les scénarios individuellement :
- `scenarios/scenario1_waterfall.py` : Analyse du modèle Waterfall (files finies, backup).
- `scenarios/scenario2_channels.py` : Analyse du modèle avec populations mixtes (barrages, priorité).
- `scenarios/scenario5_comparison.py` : Comparaison simulation vs théorie pour M/M/1, M/M/k, M/G/1.

## Structure du Projet
- `src/models/` : Implémentation des formules théoriques.
- `src/simulation/` : Moteurs de simulation SimPy (Waterfall, Populations, Priority).
- `scenarios/` : Scripts d'exécution des études de cas.
- `results/` : Graphiques générés (.png).
- `reports/` : Rapport d'analyse détaillé (.md).
- `src/utils/` : Calculs statistiques.
- `src/visualization/` : Utilitaires de plotting.
