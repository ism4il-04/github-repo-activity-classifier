# Décisions de Preprocessing (Phase 2)

| Variable | Type | Action | Justification |
| :--- | :--- | :--- | :--- |
| `avg_issue_response_hours` | numérique | Valeur `-1.0` remplacée par `NaN`, imputation médiane | La valeur `-1.0` est un code sentinelle indiquant l'absence d'issues. L'imputation médiane par défaut gère bien les distributions asymétriques. |
| `stars` | numérique | Conservation des outliers, RobustScaler | Les outliers sont des signaux valides de popularité extrême. RobustScaler atténue leur effet. |
| `forks` | numérique | Conservation des outliers, RobustScaler | Valeurs extrêmes naturelles (loi de puissance). |
| `open_issues` | numérique | Conservation des outliers, RobustScaler | Représentatif de gros projets actifs ou d'un backlog accumulé. |
| `watchers` | numérique | Conservation des outliers, RobustScaler | Signal fort pour les projets d'envergure. |
| `size_kb` | numérique | Conservation, RobustScaler | Les variations de taille sont liées à la nature des dépôts. |
| `repo_age_days` | numérique | Conservation, RobustScaler | Projets anciens vs récents sont des patterns valides. |
| `contributor_count` | numérique | Conservation, RobustScaler | Tronqué à 100 par l'API, mais reste asymétrique. |
| `engagement_rate` | numérique | Conservation, RobustScaler | Asymétrie structurelle (beaucoup de repos avec taux proche de 0). |
| `stars_forks_ratio` | numérique | Conservation, RobustScaler | Dépend fortement de la dynamique du projet (ex: forks pour contribuer vs stars pour suivre). |
| `language` | catégorielle | Imputation `most_frequent`, regroupement <1% en 'Other', One-Hot Encoding | Réduction de la cardinalité pour éviter des features très éparses et sur-apprentissage. |
| `license` | catégorielle | Imputation `most_frequent`, regroupement <1% en 'Other', One-Hot Encoding | Nombreuses licences rares qui n'apportent pas de signal statistiquement robuste. |
| `has_description` | binaire | Pas d'action (passthrough) | Prêt à l'emploi. |
| `has_homepage` | binaire | Pas d'action (passthrough) | Prêt à l'emploi. |
| `has_wiki` | binaire | Pas d'action (passthrough) | Prêt à l'emploi. |
| `has_projects` | binaire | Pas d'action (passthrough) | Prêt à l'emploi. |
| `is_fork` | binaire | Pas d'action (passthrough) | Prêt à l'emploi. |
| `days_since_last_push` | numérique | Suppression de la colonne | **Data Leakage :** Cette variable définit directement le label cible (`is_inactive`). |
| `archived` | binaire | Suppression de la colonne | **Data Leakage :** L'archivage est souvent consécutif à l'inactivité et représente un label "futur". |
| `full_name` | texte | Suppression de la colonne | Identifiant unique sans valeur prédictive. |
| `collected_at` | datetime | Suppression de la colonne | Timestamp sans variance utile pour la prédiction temporelle de chaque projet individuel. |
| `activity_score` (Nouvelle) | numérique | Création (stars + forks + watchers), RobustScaler | Indicateur composite métier de l'engagement total de la communauté. |
| `issues_per_contributor` (Nouvelle)| numérique | Création (open_issues / (contributor_count + 1)), RobustScaler | Approximation de la charge de travail par contributeur, signalant potentiellement un projet délaissé si trop élevée. |
| `age_category` (Nouvelle) | catégorielle | Création (binning repo_age_days), One-Hot Encoding | Discrétisation métier reflétant différentes phases de vie d'un projet (nouveau, jeune, mature, ancien). |
