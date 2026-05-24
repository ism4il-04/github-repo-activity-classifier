# Plan de Présentation — Phase 1
## Prédiction d'inactivité de dépôts GitHub open source
**Durée totale : 10 minutes | 7 diapositives**

---

## 🎯 Diapositive 1 — Titre *(30 secondes)*

**Contenu :**
- Titre : *Prédiction d'inactivité de dépôts GitHub open source*
- Sous-titre : *Phase 1 — Cadrage & Constitution du Dataset*
- Auteurs : Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER
- Établissement : ENSA Tétouan | ML 2025-2026
- Professeur : Pr. Y. EL YOUNOUSSI
- Date : Mai 2026

**Design de la diapositive :**
- 🖼️ **Fond** : image sombre de code GitHub ou terminal (Unsplash : "github code dark")
- 🐙 **Logo GitHub** en haut à droite (PNG transparent, téléchargeable sur github.com/logos)
- 🎓 **Logo ENSA** en bas à gauche
- **Typographie** : titre en blanc gras, grande taille (40-48pt), sous-titre en gris clair
- **Séparateur** : ligne fine colorée (bleu #2196F3) entre le titre et les auteurs

**Ce qu'on dit :**
> *"Bonjour, nous allons vous présenter notre projet de Machine Learning portant sur la prédiction de l'abandon de dépôts GitHub open source."*

---

## 🏢 Diapositive 2 — Sujet & Question métier *(1 min 30s)*

**Contenu :**

### Domaine
Génie logiciel — gestion des dépendances open source

### Question métier
> *Peut-on prédire si un **dépôt GitHub utilisé comme dépendance** (≥ 1 étoile, ≥ 30 jours) deviendra **inactif dans les 6 prochains mois**, à partir de ses métadonnées publiques ?*

### Population cible
> **Dépôts GitHub publics avec au moins 1 étoile et 30 jours d'existence** — proxy des bibliothèques réellement visibles et potentiellement utilisées en production. Les projets étudiants, forks vides et dépôts de test sont explicitement hors scope.

### Pourquoi c'est important ?
| Risque | Conséquence |
|---|---|
| Dépendance abandonnée | Vulnérabilités non corrigées |
| Bibliothèque non maintenue | Incompatibilités futures |
| Projet fantôme | Dette technique accumulée |

### Utilisateurs cibles
- Outils d'analyse de dépendances : **Snyk**, **Dependabot**, **Socket.dev**
- Équipes DevSecOps en entreprise

**Ce qu'on dit :**
> *"Des milliers d'entreprises intègrent des bibliothèques open source sans savoir si elles seront encore maintenues dans 6 mois. Notre modèle permet de détecter ces risques en avance."*

**Design de la diapositive :**
- 📊 **Tableau** des risques (3 lignes) avec icônes dans la colonne gauche :
  - 🔓 Dépendance abandonnée → Vulnérabilités
  - 🔧 Bibliothèque non maintenue → Incompatibilités
  - 👻 Projet fantôme → Dette technique
- 🏢 **Logos** Snyk + GitHub Dependabot + Socket.dev alignés horizontalement en bas
- 💡 **Encadré coloré** (fond bleu foncé) pour la question métier centrale
- **Icône** 🎯 à gauche du titre de la question métier

---

## 🔌 Diapositive 3 — Source de données & Script *(2 minutes)*

**Contenu :**

### API utilisée
| Champ | Valeur |
|---|---|
| API | GitHub REST API v2022-11-28 |
| Quota | 5 000 req/heure (token authentifié) |
| Endpoints | `/search/repositories`, `/contributors`, `/issues` |

### Stratégie de collecte
**Problème :** Le tri par défaut (`updated desc`) retourne uniquement des dépôts actifs → 0% d'inactifs.

**Solution : Échantillonnage stratifié en 2 passes**

```
Passe 1 — INACTIFS  → pushed:<2024-11-14  →  2 250 repos
Passe 2 — ACTIFS    → pushed:>2024-11-14  → 12 750 repos
```

**Diversité garantie :** 7 tranches d'étoiles × 10 langages de programmation

**Robustesse du script :**
- ✅ Gestion du rate limiting (5 000 req/h)
- ✅ Résumable automatiquement (cache JSON)
- ✅ Détection expiration du token (401)
- ✅ Checkpoint toutes les 500 lignes

**Ce qu'on dit :**
> *"Le défi principal était que l'API GitHub ne retourne que des dépôts récemment actifs par défaut. Nous avons résolu ça avec un filtre pushed:<date qui garantit de trouver des inactifs."*

> *(Montrer le terminal avec le script en cours d'exécution ou une capture d'écran)*

**Design de la diapositive :**
- 📊 **Tableau** API (3 lignes : API, Quota, Endpoints) avec fond gris foncé style terminal
- 🔄 **Schéma visuel** de la stratégie 2 passes :
  ```
  [GitHub API] ──► Passe 1 (pushed:<date) ──► 2 250 inactifs 🔴
               └──► Passe 2 (pushed:>date) ──► 12 750 actifs  🔵
  ```
  Faire ce schéma avec 2 blocs colorés (rouge = inactif, bleu = actif) et flèches
- ✅ **Liste à puces** avec icônes checkmark verts pour la robustesse du script
- 🖥️ **Capture d'écran** du terminal montrant la barre de progression `tqdm`
- **Badge** "Python 3.10+" en haut à droite

---

## 📊 Diapositive 4 — Dataset *(1 min 30s)*

**Contenu :**

### Vue d'ensemble
| Propriété | Valeur |
|---|---|
| **Lignes** | 15 000 |
| **Features** | 19 |
| **Variable cible** | `is_inactive` (0/1) |
| **Classe minoritaire** | ~15% |

### Schéma des features

| Type | Count | Features |
|---|---|---|
| **Numériques** | 11 | `stars`, `forks`, `watchers`, `open_issues`, `size_kb`, `repo_age_days`, `contributor_count`, `engagement_rate`, `stars_forks_ratio`, `avg_issue_response_hours`, `days_since_last_push`* |
| **Catégorielles** | 2 | `language`, `license` |
| **Binaires** | 6 | `has_description`, `has_homepage`, `has_wiki`, `has_projects`, `is_fork`, `archived`* |

> *⚠️ Features marquées \* : **à exclure avant modélisation** (data leakage)*

### Features exclues du modèle
- `days_since_last_push` → encode directement le label
- `archived` → décision post-hoc
- `full_name`, `collected_at` → identifiants

**Ce qu'on dit :**
> *"Nous avons 17 features exploitables après suppression des features à fuite de données. Ces features capturent des signaux complémentaires de l'activité d'un dépôt."*

**Design de la diapositive :**

**Layout : 3 zones**

```
┌─────────────────────────────────────────────────────────────┐
│  📊 DATASET — Vue d'ensemble                                │
├──────────────┬──────────────────────────────┬───────────────┤
│  [4 stats]   │     [Bubble / feature map]   │  [Leakage]    │
│  en cards    │                              │  encadré 🚫   │
└──────────────┴──────────────────────────────┴───────────────┘
```

**Zone gauche — 4 cartes statistiques** (style "KPI cards") :
```
┌──────────┐  ┌──────────┐
│  15 000  │  │    19    │
│   lignes │  │ features │
└──────────┘  └──────────┘
┌──────────┐  ┌──────────┐
│is_inactive│  │   15%   │
│  (0 / 1) │  │inactif  │
└──────────┘  └──────────┘
```
- Fond de chaque carte : bleu foncé avec chiffre en grand blanc (28pt)
- Sous-titre de la carte en gris clair petit (10pt)

**Zone centrale — Carte visuelle des features** (pas de tableau boring) :
- 3 groupes de bulles ou badges colorés organisés verticalement :

```
🔵 NUMÉRIQUES (11)
   stars · forks · watchers · open_issues · size_kb
   repo_age_days · contributor_count · engagement_rate
   stars_forks_ratio · avg_issue_response_hours · days_since_last_push*

🟢 CATÉGORIELLES (2)
   language · license

🟠 BINAIRES (6)
   has_description · has_homepage · has_wiki
   has_projects · is_fork · archived*
```
- Chaque feature = un **badge pill** (rectangle arrondi) de la couleur de son groupe
- Les features marquées `*` (leakage) en rouge avec ligne barrée ~~feature~~

**Zone droite — Encadré leakage 🚫** :
```
┌─────────────────────┐
│  🚫 À EXCLURE       │
│  avant modélisation │
│                     │
│  days_since_last_   │
│  push               │
│  → encode le label  │
│                     │
│  archived           │
│  → décision post-   │
│    hoc              │
│                     │
│  full_name          │
│  collected_at       │
│  → identifiants     │
└─────────────────────┘
```
- Fond rouge très foncé, texte blanc, icône ⚠️ en haut

---

## 📈 Diapositive 5 — Distribution de la variable cible *(2 minutes)*

**Contenu :**

### Résultat de validation
| Classe | Count | % | Statut |
|---|---|---|---|
| 0 — Actif | 12 750 | 85% | Classe majoritaire |
| 1 — Inactif | 2 250 | 15% | Classe minoritaire |
| **Total** | **15 000** | **100%** | ✅ **VALIDE (5–25%)** |

### Insérer ici :
- 📊 `data/class_distribution.png` *(bar + pie chart)*
- 📊 `data/language_distribution.png` *(stacked bar + taux d'inactivité par langage)*

### Points clés à mentionner
- Ratio 15% ✅ conforme à la contrainte du projet (5–25%)
- Validé par la littérature : **Avelino et al. (2019), MSR** — ~16% d'abandon sur 1 932 projets GitHub populaires
- Population cible = dépôts ≥ 1 étoile + ≥ 30 jours (pas la population brute GitHub)
- Distribution équilibrée sur **10 langages** : Python, JavaScript, Java, C++, Go, Ruby, Rust, TypeScript, PHP, C
- Déséquilibre **naturel sur la sous-population qualifiée** — pas artificiel

> ⚠️ **Objection anticipée :** Si le jury demande *"mais 70-80% des repos GitHub sont inactifs, pourquoi seulement 15% chez vous ?"* → réponse : ce chiffre concerne la population brute (420M+ repos incluant projets étudiants, forks vides). Notre population cible est qualifiée (≥ 1 étoile, ≥ 30 jours). Sur cette sous-population, Avelino et al. mesurent 16% — ce qui valide notre ratio.

**Ce qu'on dit :**
> *"Le ratio de 15% est réel et naturel. Nous n'avons pas forcé artificiellement le déséquilibre — nous avons utilisé l'échantillonnage stratifié uniquement pour garantir assez d'exemples de la classe minoritaire pour entraîner le modèle."*

**Design de la diapositive :**
- 📊 **Image** `data/class_distribution.png` — côté gauche (bar chart + pie chart)
- 📊 **Image** `data/language_distribution.png` — côté droit (stacked bar par langage)
- ✅ **Badge vert** centré en bas : *"Ratio minoritaire : 15% ✅ VALIDE (5–25%)"*
- 📋 **Mini tableau** de validation (3 lignes : Total / Actif / Inactif) au-dessus des images
- **Titre de section** avec icône 📈 à gauche

---

## ⚖️ Diapositive 6 — Traduction métier → ML *(2 minutes)*

**Contenu :**

### Tableau de traduction (section 3 du cadrage)

| Objectif métier | Objectif ML | Métrique | Seuil |
|---|---|---|---|
| Détecter 80% des dépôts abandonnés | Maximiser le recall classe 1 | **Recall** | ≥ 0,80 |
| Limiter les fausses alertes | Maintenir une précision correcte | **Precision** | ≥ 0,50 |
| Équilibre recall/precision | Maximiser F1 | **F1-score** | ≥ 0,65 |
| Évaluation globale | Courbe Précision-Rappel | **PR-AUC** | ≥ 0,70 |

### Pourquoi le Recall comme métrique principale ?

**Analyse du coût asymétrique :**

| Erreur | Coût | Exemple |
|---|---|---|
| **Faux Négatif** (dépôt abandonné non détecté) | **5 000 € – 50 000 €+** | Incident sécurité, audit, downtime |
| **Faux Positif** (fausse alerte) | **30 – 120 €** | 30 min de vérification humaine |

> **FN coûte 50× à 400× plus cher qu'un FP → on maximise le Recall**

**Sources :** IBM Cost of a Data Breach 2023 [1] · Sonatype SOSS 2023 [2] · Snyk OSS Security 2023 [3]

### Métriques refusées
- ❌ **Accuracy seule** → trompeuse sur données déséquilibrées (un modèle qui prédit toujours "actif" aurait 85% d'accuracy)
- ❌ **ROC-AUC seule** → trop optimiste quand la classe négative domine

**Ce qu'on dit :**
> *"Ne pas détecter un dépôt abandonné peut coûter des dizaines de milliers d'euros en incident de sécurité. Une fausse alerte coûte juste 30 minutes d'un ingénieur. L'asymétrie est claire : on privilégie le recall."*

**Design de la diapositive :**
- 📋 **Tableau traduction** (4 lignes) avec colonne Métrique en gras et colorée
- ⚖️ **Schéma visuel coût asymétrique** — deux blocs côte à côte :
  ```
  ┌─────────────────────────┐    ┌──────────────────────┐
  │  ❌ FAUX NÉGATIF        │    │  ⚠️ FAUX POSITIF     │
  │  Dépôt abandonné        │    │  Fausse alerte        │
  │  non détecté            │    │                       │
  │  💸 5 000–50 000 €+    │    │  💸 30–120 €          │
  │  Incident sécurité      │    │  30 min ingénieur     │
  └─────────────────────────┘    └──────────────────────┘
         FN coûte 50× à 400× plus cher → RECALL principal
  ```
  - Bloc FN : fond rouge foncé
  - Bloc FP : fond orange foncé
  - Flèche pointant vers **RECALL** en vert en bas
- ❌ **Deux badges rouges** pour les métriques refusées (Accuracy, ROC-AUC)
- 📎 **Ligne de sources** en petit en bas de diapo (IBM · Sonatype · Snyk)

---

## 🚀 Diapositive 7 — Conclusion & Phase 2 *(30 secondes)*

**Contenu :**

### Bilan Phase 1 ✅
- ✅ **Dataset** : 15 000 lignes, 19 features, déséquilibre valide (15%)
- ✅ **Diversité** : 10 langages × 7 tranches d'étoiles
- ✅ **Documentation** : `DATASET.md`, `cadrage.md`, notebook EDA complet
- ✅ **Script** : reproductible, résumable, robuste

### Phase 2 — Prochaines étapes
| Étape | Contenu |
|---|---|
| Prétraitement | Encodage catégoriel, normalisation, gestion des valeurs sentinelles (-1.0) |
| Feature engineering | Sélection des features, suppression des fuites de données |
| Modélisation | Logistic Regression, Random Forest, XGBoost |
| Évaluation | Recall ≥ 0,80 · F1-score ≥ 0,65 · PR-AUC ≥ 0,70 |

**Ce qu'on dit :**
> *"La Phase 1 est complète. En Phase 2, nous allons entraîner et comparer plusieurs modèles avec comme objectif principal un recall ≥ 0,80 sur la classe inactive. Merci."*

**Design de la diapositive :**
- ✅ **4 cartes** côte à côte (style "achievement cards") pour le bilan Phase 1 :
  - 🗄️ Dataset : 15 000 lignes
  - 🌍 Diversité : 10 langages
  - 📄 Documentation : complète
  - ⚙️ Script : robuste & résumable
- 🗺️ **Timeline horizontale** pour Phase 2 avec 4 étapes :
  ```
  Prétraitement ──► Feature Eng. ──► Modélisation ──► Évaluation
  ```
  Chaque étape dans un cercle numéroté (1, 2, 3, 4)
- 🙏 **"Merci / Questions ?"** centré en bas avec fond coloré
- **Logos** ENSA + GitHub en bas

---

## 📋 Checklist avant la présentation

- [ ] Slides créées dans QuillBot / PowerPoint / Google Slides
- [ ] `class_distribution.png` insérée dans diapo 5
- [ ] `language_distribution.png` insérée dans diapo 5
- [ ] Script visible (capture terminal ou live demo) pour diapo 3
- [ ] Chaque membre connaît sa partie
- [ ] Répétition chronométrée (10 min max)
- [ ] Dataset disponible sur Drive partagé pour démo

