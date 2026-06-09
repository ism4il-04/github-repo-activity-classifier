# DATASET.md — Dataset d'Activité des Dépôts GitHub

## a) Identification

| Champ | Valeur |
|---|---|
| **Nom** | Dataset d'Activité des Dépôts GitHub |
| **Auteur(s)** | Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER |
| **Date de collecte** | 2026-05-15 |
| **Version** | 1.0 |
| **Fichier** | `data/dataset.csv` |

---

## b) Source

| Champ | Valeur |
|---|---|
| **API** | GitHub REST API v2022-11-28 |
| **URL de base** | `https://api.github.com` |
| **Date d'accès** | 2026-05-15 |
| **Authentification** | Jeton d'accès personnel (Personal Access Token, lecture seule, dépôts publics) |

### Endpoints utilisés

| Endpoint | Objectif |
|---|---|
| `GET /search/repositories` | Recherche principale — retourne les métadonnées des dépôts |
| `GET /repos/{owner}/{repo}/contributors` | Nombre de contributeurs par dépôt |
| `GET /repos/{owner}/{repo}/issues` | Les 20 dernières issues fermées pour estimer le temps de réponse |
| `GET /rate_limit` | Surveillance du quota d'API |

### Stratégie d'échantillonnage

Les dépôts ont été échantillonnés selon 7 tranches d'étoiles (0–5, 6–15, 16–50, 51–200, 201–1000, 1001–5000, 5001–50000) et 10 langages de programmation (Python, JavaScript, Java, C++, Go, Ruby, Rust, TypeScript, PHP, C). Cette approche croisée et stratifiée assure une diversité quant à la taille et au niveau d'activité des dépôts, évitant ainsi le biais de sélection en faveur des dépôts populaires ou récemment actifs.

Une **collecte stratifiée en deux passes** a été utilisée pour corriger le biais structurel de l'API de recherche de GitHub, qui par défaut ne retourne que les dépôts récemment actifs (triés par `updated desc`), rendant la classe inactive invisible sans un filtre explicite `pushed:<cutoff` :
- **Passe 1 :** `pushed:<cutoff` — collecte de dépôts garantis inactifs (2 250 lignes)
- **Passe 2 :** `pushed:>cutoff` — collecte de dépôts garantis actifs (12 750 lignes)

---

## c.1) Périmètre, Population, et Biais de Collecte

### Pourquoi la population brute de GitHub est hors périmètre

GitHub héberge plus de 420 millions de dépôts. Parmi ceux-ci, des études rapportent systématiquement que 70 à 80 % sont inactifs lorsque l'on mesure la **population brute** — mais cette population inclut des millions de projets étudiants, de forks vides, d'expérimentations avec un seul commit, et d'espaces de test personnels qui ne sont jamais utilisés comme dépendances. Cette statistique n'est **pas pertinente** pour notre cas d'usage.

### Sous-population cible et filtre des étoiles

Notre dataset cible une **sous-population qualifiée** : des dépôts avec **au moins 1 étoile et au moins 30 jours d'existence**. Cela agit comme un filtre de visibilité minimal — un dépôt avec au moins une étoile a été remarqué par au moins une personne autre que le propriétaire, ce qui en fait un candidat plausible pour être utilisé comme dépendance ou projet de référence.

Ce filtre est appliqué implicitement via la plage minimale d'étoiles `stars:0..5` (les dépôts ayant ≥ 0 étoiles sont collectés, mais le script exclut les dépôts créés il y a moins de 30 jours) et explicitement via le filtre d'âge `repo_age_days >= 30`.

### Déséquilibre des classes — validation empirique

Sur cette sous-population qualifiée, le taux d'inactivité de 15 % est **validé empiriquement par la littérature académique** :

| Source | Résultat | Pertinence |
|---|---|---|
| Avelino et al. (2019), MSR — *doi.org/10.1109/MSR.2019.00059* | ~16 % des 1 932 projets GitHub populaires sont classifiés comme abandonnés | Validation directe de notre cible de 15 % sur une population qualifiée similaire |

### Correction du biais structurel de l'API de Recherche GitHub

Sans la stratégie en deux passes, l'interrogation de l'API de Recherche de GitHub avec le tri par défaut (`sort=updated, order=desc`) renvoie des résultats massivement biaisés vers les dépôts récemment actifs. En pratique, cela a produit **0 % de dépôts inactifs** lors des premiers tests. Le filtre `pushed:<cutoff` dans la Passe 1 cible directement la sous-population inactive, garantissant que le dataset reflète la véritable distribution de la population qualifiée plutôt qu'un artefact de l'algorithme de classement de l'API.

---

## c) Description

### Définition du problème

Ce dataset supporte une tâche de **classification supervisée binaire** : prédire si un dépôt GitHub **utilisé comme dépendance** (≥ 1 étoile, ≥ 30 jours d'existence) deviendra **inactif** (aucun push de code depuis plus de 180 jours). Cela est formulé comme un label d'état présent — un dépôt est étiqueté inactif s'il n'a pas reçu de push au cours des 180 derniers jours au moment de la collecte.

**Population cible :** Dépôts publics GitHub avec **au moins 1 étoile et au moins 30 jours d'existence** — un proxy pour les bibliothèques et outils qui sont réellement visibles et potentiellement utilisés comme dépendances en production. Cela exclut délibérément les projets étudiants, les forks vides, les dépôts de test et les expérimentations abandonnées qui constituent la majorité des plus de 420 millions de dépôts bruts de GitHub, mais qui sont hors périmètre pour l'évaluation des risques liés aux dépendances.

**Valeur métier :** Les gestionnaires de dépendances open source, les outils de développement et les équipes de sécurité ont besoin de signaler les bibliothèques potentiellement abandonnées avant qu'elles ne deviennent des risques dans les logiciels en production.

### Dimensions du dataset

| Propriété | Valeur |
|---|---|
| Nombre de lignes | 15 000 |
| Nombre de features | 19 (11 numériques, 2 catégorielles, 6 binaires) |
| Variable cible | `is_inactive` |
| Classe minoritaire (inactif) | ~15 % (déséquilibre naturel) |

---

### Schéma des features

| Feature | Type | Description | Plage / Valeurs |
|---|---|---|---|
| `stars` | numérique (int) | Total des étoiles GitHub | 0 – 500 000+ |
| `forks` | numérique (int) | Total des forks | 0 – 100 000+ |
| `open_issues` | numérique (int) | Issues ouvertes + PRs au moment de la collecte | 0 – 10 000+ |
| `watchers` | numérique (int) | Nombre de watchers | 0 – 500 000+ |
| `size_kb` | numérique (int) | Taille du dépôt en kilooctets | 0 – 500 000+ |
| `repo_age_days` | numérique (int) | Jours écoulés depuis la création du dépôt | 30 – 5 000+ |
| `days_since_last_push` | numérique (int) | Jours écoulés depuis le dernier git push | 0 – 3 000+ |
| `contributor_count` | numérique (int) | Nombre de contributeurs distincts (plafonné à 100 dans le script) | 1 – 100+ |
| `avg_issue_response_hours` | numérique (float) | Temps moyen de fermeture des 20 dernières issues (heures) ; -1.0 si aucune issue | -1.0 – 10 000+ |
| `engagement_rate` | numérique (float) | (stars + forks) / repo_age_days — proxy de l'intérêt soutenu | 0.0 – 50.0+ |
| `stars_forks_ratio` | numérique (float) | stars / max(forks, 1) | 0.1 – 1 000+ |
| `language` | catégorielle | Langage de programmation principal | Python, JavaScript, Java, … Inconnu |
| `license` | catégorielle | Nom de la licence | MIT, Apache-2.0, GPL-3.0, None, … |
| `has_description` | binaire (0/1) | Si le dépôt possède une description non vide | 0, 1 |
| `has_homepage` | binaire (0/1) | Si une URL de page d'accueil est définie | 0, 1 |
| `has_wiki` | binaire (0/1) | Si la fonctionnalité Wiki GitHub est activée | 0, 1 |
| `has_projects` | binaire (0/1) | Si GitHub Projects est activé | 0, 1 |
| `is_fork` | binaire (0/1) | Si ce dépôt est un fork | 0, 1 |
| `archived` | binaire (0/1) | Si le dépôt est officiellement archivé | 0, 1 |

### Variable cible

| Variable | Type | Description |
|---|---|---|
| `is_inactive` | binaire (0/1) | **1** = aucun push dans les 180 derniers jours (inactif / potentiellement abandonné) ; **0** = mis à jour dans les 180 derniers jours (actif) |

> **Note :** `days_since_last_push` et `archived` sont fortement corrélées avec la variable cible. Elles doivent être **supprimées avant la modélisation** pour éviter les fuites de données (data leakage) — elles sont incluses dans le dataset uniquement à des fins de documentation et d'EDA. Les colonnes d'identifiants `full_name` et `collected_at` doivent également être exclues de la matrice de caractéristiques.

### Distribution des classes

> | Classe | Nombre | % |
|---|---|---|
> | 0 — actif | 12 750 | 85.0 % |
> | 1 — inactif | 2 250 | 15.0 % |

*(Voir le graphique en barres dans `notebooks/01_discovery.ipynb` et `data/class_distribution.png`)*

---

## d) Limites connues

- `contributor_count` est plafonné à 100 par l'appel de l'API à une seule page du script ; les dépôts ayant plus de contributeurs afficheront 100.
- `avg_issue_response_hours` vaut `-1.0` pour les dépôts n'ayant aucune issue fermée — à traiter comme une catégorie de valeur manquante.
- Le seuil de 180 jours est un choix de conception ; il peut être modifié dans `data_collection.py` pour changer la définition de l'inactivité.
- L'API de Recherche de GitHub n'expose pas directement la fréquence des commits ; `engagement_rate` en est une approximation.
- Les dépôts de moins de 30 jours d'âge sont exclus pour éviter de classer comme inactifs des dépôts véritablement nouveaux.
