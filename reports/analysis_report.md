# Rapport Final d'Étude des Systèmes d'Attente - Moulinette

## 1. Introduction
Cette étude porte sur la modélisation et l'analyse de l'infrastructure de correction automatique ("moulinette") de l'école. Nous avons utilisé des simulations à événements discrets pour évaluer différents modèles de gestion des flux d'étudiants (Waterfall et Channels & Dams) et validé nos résultats par rapport aux modèles théoriques de la file d'attente.

---

## 2. Modèle Waterfall
Le modèle Waterfall représente le flux nominal d'un étudiant : exécution des tests (K serveurs) suivie de l'envoi du résultat au front (1 serveur).

### 2.1. Files Infinies vs Finies
- **Files Infinies** : Permettent de mesurer le temps de séjour "idéal". Sans contrainte de taille, le goulot d'étranglement se déplace vers le serveur d'envoi si le taux d'arrivée dépasse sa capacité.
- **Files Finies ($k_s, k_f$)** : 
    - Un $k_s$ faible (ex: 2) entraîne un taux de rejet élevé (~9% dans nos simulations).
    - Augmenter $k_s$ à 10 ou 20 ramène le taux de rejet à pratiquement 0% pour une charge normale.
    - Le rejet au niveau de $k_f$ génère des "pages blanches" (résultats perdus).

### 2.2. Système de Backup
L'introduction d'un backup permet de sauvegarder les résultats lorsque la file d'envoi ($k_f$) est pleine. 
- **Impact** : Réduction drastique des échecs de rendu (le "vide" perçu par l'étudiant).
- **Observation** : Le temps de séjour total peut légèrement augmenter car les résultats sont traités en différé dès qu'une place se libère, mais l'intégrité des données est préservée.

---

## 3. Channels and Dams
Ce scénario traite la mixité des populations **ING** (arrivées fréquentes) et **PREPA** (soumissions rares mais exécution plus longue).

### 3.1. Problématique
Sans régulation, la population ING sature le système, entraînant des temps d'attente inacceptables pour les PREPA qui finissent par être "noyés" dans le flux.

### 3.2. Régulation par Barrage (Dam)
Nous avons simulé un blocage périodique pour les ING ($t_b = 10$, ouvert $1/2$ du temps).
- **Avantage** : Garantit des fenêtres de traitement prioritaires. Le temps de séjour moyen chute de manière significative pour les deux populations acceptées.
- **Inconvénient** : Un taux de rejet élevé pour les ING pendant les périodes de fermeture (~66%).

### 3.3. Optimisation : Files à Priorité
La solution optimale consiste à donner une priorité plus élevée aux PREPA. En simulation, cela réduit leur temps de séjour à un minimum (~5 unités de temps) tout en permettant aux ING d'être servis en arrière-plan sans rejets systématiques.

---

## 4. Validation Théorique
Nous avons confronté nos simulations aux modèles mathématiques standards pour valider la robustesse de notre moteur de simulation.

| Modèle | Simulation (moyen) | Théorie (moyen) | Erreur Rel. |
| :--- | :--- | :--- | :--- |
| **M/M/1** | 4.61 | 5.00 | ~7.9% |
| **M/M/3** | 1.45 | 1.44 | ~0.4% |
| **M/G/1 (D)** | 3.13 | 3.00 | ~4.4% |

*Note: L'erreur sur le M/M/1 est principalement due à la variance élevée de cette configuration sur la durée de simulation choisie.*

---

## 5. Conclusion et Recommandations
1. **Dimensionnement** : Un pool de 4 serveurs d'exécution avec une file d'attente de 20 places est optimal pour la charge étudiée.
2. **Robustesse** : Le backup est indispensable pour éviter les pertes de données lors des pics de charge.
3. **Équité** : L'implémentation d'une priorité logicielle pour les populations moins fréquentes (PREPA) est préférable au blocage brutal (Dam).

---