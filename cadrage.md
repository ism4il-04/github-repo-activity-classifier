# Fiche de cadrage — Phase 1
## Prédiction d'inactivité de dépôts GitHub open source

**Établissement :** ENSA Tétouan  
**Module :** Machine Learning — 2ème année Cycle Ingénieurs GI  
**Professeur :** Pr. Y. EL YOUNOUSSI  
**Année universitaire :** 2025-2026  
**Auteur(s) :** Ismail LYAMANI, Abdellatif OUMHELLA, Mohammed Aymane SABER  
**Date :** 2026-05-15

---

## 1. Domaine métier et question business

**Domaine :** Génie logiciel — gestion des dépendances open source

**Question métier :**
> Peut-on prédire si un **dépôt GitHub utilisé comme dépendance** (≥ 1 étoile, ≥ 30 jours d'existence) deviendra **inactif ou abandonné dans les 6 prochains mois**, à partir des métadonnées disponibles publiquement aujourd'hui ?

**Population cible :** Les dépôts GitHub publics avec **au moins une étoile et 30 jours d'existence** — proxy des bibliothèques et outils réellement visibles et potentiellement utilisés comme dépendances en production. Cette définition exclut intentionnellement les projets étudiants, forks vides, dépôts de test ou expérimentaux qui constituent la majorité brute des 420M+ repos GitHub mais sont hors scope métier.

**Contexte :** Des milliers d'entreprises et de développeurs dépendent de bibliothèques open source dans leurs projets. Un dépôt abandonné représente un risque réel : absence de correctifs de sécurité, incompatibilités futures, et perte de support. Détecter ces dépôts à risque *avant* qu'ils n'impactent la production est un besoin concret pour les outils d'analyse de dépendances (ex : Snyk, Dependabot, Socket.dev).

---

## 2. Objectifs métiers quantifiés

| # | Objectif métier | Critère de succès |
|---|---|---|
| 1 | Identifier au moins 80% des dépôts qui seront abandonnés | Rappel (recall) ≥ 0,80 sur la classe inactive |
| 2 | Limiter les fausses alertes pour ne pas surcharger les équipes | Précision (precision) ≥ 0,50 sur la classe inactive |
| 3 | Produire un modèle interprétable pour justifier les alertes | Utilisation de features explicables (pas de boîte noire totale) |

---

## 3. Traduction métier → ML

| Objectif métier | Objectif ML | Métrique principale | Seuil cible |
|---|---|---|---|
| Détecter 80% des dépôts qui seront abandonnés | Maximiser le rappel sur la classe 1 (inactive) | **Recall (classe 1)** | ≥ 0,80 |
| Limiter les faux positifs à un niveau acceptable | Maintenir une précision raisonnable sur la classe 1 | **Precision (classe 1)** | ≥ 0,50 |
| Équilibre entre les deux objectifs précédents | Maximiser le F1-score sur la classe 1 | **F1-score (classe 1)** | ≥ 0,65 |
| Évaluer la qualité globale du modèle sur données déséquilibrées | Maximiser l'aire sous la courbe Précision-Rappel | **PR-AUC** | ≥ 0,70 |

> **Métrique principale retenue : Recall sur la classe inactive (1)**  
> Justification : voir section 4 — le coût d'un faux négatif est structurellement plus élevé.

---

## 4. Analyse du coût asymétrique (faux positif vs faux négatif)

### Définitions dans notre contexte

| Erreur | Description | Conséquence concrète |
|---|---|---|
| **Faux négatif (FN)** | Le modèle prédit "actif" alors que le dépôt sera abandonné | L'équipe continue d'utiliser une dépendance à risque → vulnérabilité de sécurité non corrigée, incompatibilité future, dette technique |
| **Faux positif (FP)** | Le modèle prédit "inactif" alors que le dépôt est en réalité actif | Une alerte inutile est générée → l'équipe passe du temps à vérifier et conclut que tout va bien |

### Estimation des coûts

| Type d'erreur | Coût estimé | Justification |
|---|---|---|
| **Faux négatif** | **Élevé** — 5 000 € à 50 000 €+ | Incident de sécurité sur dépendance non maintenue : audit, patch d'urgence, downtime, atteinte à la réputation |
| **Faux positif** | **Faible** — 30 à 120 € | Vérification humaine : ~30 min d'un ingénieur pour confirmer que le dépôt est actif |

**Ratio asymétrique estimé : FN coûte ~50× à 400× plus cher qu'un FP.**

### Références

| # | Source | Donnée utilisée |
|---|---|---|
| [1] | IBM Security — *Cost of a Data Breach Report 2023* — `ibm.com/reports/data-breach` | Coût moyen d'une violation de données : **4,45 M$** |
| [2] | Sonatype — *State of the Software Supply Chain 2023* — `sonatype.com/state-of-the-software-supply-chain` | 245 000+ packages malveillants ; coût de remédiation Log4Shell / event-stream : **10 000 $ – 500 000 $** par organisation |
| [3] | Snyk — *State of Open Source Security 2023* — `snyk.io/reports/open-source-security` | 84% des codebases contiennent des vulnérabilités transitives ; cas Equifax (Apache Struts) : règlement **575 M$** |
| [4] | Calcul interne — salaire moyen ingénieur logiciel (Glassdoor / Indeed MENA 2023 : ~150–250 k MAD/an ≈ 14–23 €/h) | 30 min × 14–23 €/h + overhead (context switching, documentation) = **30–120 €** |

### Conséquences sur les choix ML

- La métrique principale est le **recall** (minimiser les FN).
- On accepte une précision modérée (≥ 0,50) pour maximiser la couverture.
- Le **seuil de décision** sera abaissé en dessous de 0,5 lors du tuning (Phase 2-3).
- Les métriques refusées comme principale métrique : accuracy seule (trop optimiste sur données déséquilibrées), ROC-AUC seule.

---

## 5. Variable cible et définition de l'inactivité

**Définition adoptée :**
> Un dépôt est considéré **inactif (label = 1)** si sa date de dernier push (`pushed_at`) est antérieure de plus de **180 jours** à la date de collecte.

**Justification du seuil de 180 jours :**
- Assez court pour être actionnable (6 mois ≈ un cycle de projet)
- Assez long pour exclure les dépôts en pause temporaire (vacances, sprint terminé)
- Ce seuil est mesurable aujourd'hui, sans attendre le futur

| Label | Valeur | Condition |
|---|---|---|
| Actif | 0 | `days_since_last_push` ≤ 180 |
| Inactif | 1 | `days_since_last_push` > 180 |

---

## 6. Source de données

| Champ | Valeur |
|---|---|
| **API principale** | GitHub REST API v2022-11-28 |
| **Authentification** | Personal Access Token (lecture seule, repos publics) |
| **Quota** | 5 000 requêtes/heure avec token authentifié |
| **Script de collecte** | `src/data_collection.py` |

### Stratégie d'échantillonnage

**Périmètre de la collecte :** Seuls les dépôts avec **au moins une étoile** (`stars:>=1`) et **au moins 30 jours d'existence** sont collectés. Ce filtre définit la sous-population métier réelle : les projets ayant une visibilité minimale et susceptibles d'être utilisés comme dépendances. Les dépôts sans étoile (projets personnels, tests, forks vides) en sont explicitement exclus.

Les dépôts sont ensuite collectés en croisant **7 tranches d'étoiles** × **10 langages de programmation**, afin d'obtenir une distribution diversifiée et représentative — et non biaisée vers les projets très populaires.

La collecte utilise un **échantillonnage stratifié en deux passes** pour corriger le biais structurel de l'API GitHub :
- **Passe 1 :** 2 250 dépôts inactifs (`pushed:<cutoff`) — classe minoritaire garantie
- **Passe 2 :** 12 750 dépôts actifs (`pushed:>cutoff`) — classe majoritaire garantie

> **Note :** Sans la stratégie en deux passes, le tri par défaut de l'API (`updated desc`) retourne quasi-exclusivement des dépôts récemment actifs, rendant la classe inactive invisible dans les résultats de recherche.

**Justification du ratio 15% / 85% — validation par la littérature :**  
Le ratio de 15% d'inactifs n'est ni artificiel ni arbitraire. Il reflète la réalité mesurée sur la **sous-population qualifiée** (dépôts avec visibilité minimale), distincte de la population brute GitHub. Avelino et al. (2019) [5], dans une étude sur 1 932 projets GitHub populaires publiée à la *Mining Software Repositories* (MSR) conference, mesurent **~16% de projets abandonnés** — ce qui valide directement notre cible de 15%. Le ratio est conforme à la contrainte du projet (5–25%) et reflète un scénario réaliste de déploiement.

| [5] | Avelino, G. et al. — *"A Novel Approach for Estimating Truck Factors"*, MSR 2019 — `doi.org/10.1109/MSR.2019.00059` | ~16% de projets GitHub populaires abandonnés sur 1 932 projets analysés |

---

## 7. Features sélectionnées

| Feature | Type | Justification métier |
|---|---|---|
| `stars` | Numérique | Indicateur de popularité et d'intérêt communautaire |
| `forks` | Numérique | Mesure l'utilisation dérivée et l'engagement actif |
| `open_issues` | Numérique | Un nombre élevé sans résolution peut indiquer l'abandon |
| `watchers` | Numérique | Nombre de watchers — proxy d'intérêt passif soutenu |
| `contributor_count` | Numérique | Un dépôt avec 1 seul contributeur est plus fragile |
| `engagement_rate` | Numérique (dérivé) | (stars + forks) / âge — proxy de l'intérêt soutenu |
| `repo_age_days` | Numérique | Les dépôts très anciens ont des patterns différents |
| `size_kb` | Numérique | Proxy de la maturité et du volume de travail |
| `avg_issue_response_hours` | Numérique | Un temps de réponse élevé signale une maintenance passive |
| `stars_forks_ratio` | Numérique (dérivé) | Distingue les projets admirés vs. réellement utilisés |
| `language` | Catégorielle | Certains langages ont des écosystèmes plus actifs |
| `license` | Catégorielle | Les dépôts sans licence sont souvent abandonnés |
| `has_description` | Binaire | Signal de soin apporté à la documentation |
| `has_homepage` | Binaire | Signal de projet sérieux et maintenu |
| `has_wiki` | Binaire | Signal de documentation active |
| `has_projects` | Binaire | Signal de gestion de projet active |
| `is_fork` | Binaire | Les forks ont des patterns d'activité différents |

> **Features à exclure du modèle (data leakage) :**  
> `days_since_last_push` (encode directement le label), `archived` (décision post-hoc), `full_name`, `collected_at`.

---

## 8. Métriques retenues

| Métrique | Statut | Justification |
|---|---|---|
| **Recall (classe 1)** | ✅ Principale | Minimise les FN — coût asymétrique justifié section 4 |
| **F1-score (classe 1)** | ✅ Secondaire | Équilibre recall et précision |
| **PR-AUC** | ✅ Secondaire | Robuste au déséquilibre, évalue la courbe complète |
| **Precision (classe 1)** | ✅ Tertiaire | Contrôle le taux de fausses alertes |
| Accuracy seule | ❌ Refusée | Trompeuse sur données déséquilibrées |
| ROC-AUC seule | ❌ Refusée comme principale | Trop optimiste quand classe négative domine |
