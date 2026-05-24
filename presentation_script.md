# Script de Présentation — Phase 1
## Prédiction d'inactivité de dépôts GitHub open source
**Durée totale : ~10 minutes | 9 diapositives**

> 💡 **Convention :**
> - *[action]* = geste ou pointeur sur la diapo
> - `→` = transition vers la diapo suivante

---

## 🎯 Diapositive 1 — Page de garde *(30 secondes)*

*[afficher la diapo titre]*

Bonjour à tous.

Nous sommes **Ismail LYAMANI**, **Abdellatif OUMHELLA** et **Mohammed Aymane SABER**, étudiants en 2ème année cycle ingénieurs Génie Informatique à l'ENSA Tétouan.

Aujourd'hui, nous vous présentons notre projet de Machine Learning — Phase 1 — qui porte sur la **prédiction d'inactivité de dépôts GitHub open source**.

---
`→ passer à la diapo 2`

> *"Commençons par définir le problème métier que nous cherchons à résoudre."*

---

## 🏢 Diapositive 2 — Sujet & Question métier *(1 minute 30s)*

*[pointer la question métier dans l'encadré]*

Notre question métier est :
> **"Peut-on prédire si un dépôt GitHub utilisé comme dépendance — c'est-à-dire avec au moins une étoile et 30 jours d'existence — deviendra inactif dans les 6 prochains mois, à partir de ses métadonnées publiques ?"**

Pourquoi cette question est-elle importante ?

Des milliers d'entreprises dépendent quotidiennement de bibliothèques open source. Ces bibliothèques peuvent être abandonnées à tout moment.

*[pointer le tableau des risques]*

Les conséquences sont concrètes :
- Les vulnérabilités de sécurité ne sont plus corrigées
- La bibliothèque devient incompatible avec les nouvelles versions
- L'équipe accumule une dette technique difficile à résorber

*[pointer les logos Snyk, Dependabot, Socket.dev]*

Des outils comme Snyk, Dependabot ou Socket.dev cherchent à alerter les équipes avant qu'il ne soit trop tard. Notre modèle fait la même chose — mais de manière **prédictive**, avant même que l'abandon soit officiel.

---
`→ passer à la diapo 3`

> *"Voyons maintenant la source de données que nous avons utilisée."*

---

## 🔌 Diapositive 3 — Source de données : API, quota et endpoints *(1 minute)*

*[pointer le tableau API]*

Pour constituer notre dataset, nous avons utilisé l'**API REST GitHub**, version 2022-11-28.

Avec un token authentifié, elle offre **5 000 requêtes par heure** — ce qui est largement suffisant pour notre volume.

Nous interrogeons **quatre endpoints principaux** :

- **`/search/repositories`** — pour récupérer les métadonnées de chaque dépôt : étoiles, forks, dates, langage, licence…
- **`/repos/{owner}/{repo}/contributors`** — pour compter le nombre de contributeurs distincts
- **`/repos/{owner}/{repo}/issues`** — pour calculer le temps de réponse moyen aux issues fermées
- **`/rate_limit`** — pour surveiller le quota restant avant chaque requête et éviter les erreurs 429

Ces quatre endpoints sont combinés pour construire les 19 features du dataset.

---
`→ passer à la diapo 4`

> *"Maintenant, voyons comment notre script gère concrètement cette collecte."*

---

## ⚙️ Diapositive 4 — Script de collecte *(2 minutes)*

*[pointer le schéma des 2 passes]*

Le premier défi que nous avons rencontré : quand on cherche des dépôts avec le tri par défaut de l'API, elle retourne **uniquement des dépôts récemment actifs**. Résultat lors de notre premier test : **0% d'inactifs** sur 12 000 lignes collectées.

Pour corriger ça, nous avons d'abord défini un **périmètre précis** : uniquement les dépôts avec au moins une étoile et au moins 30 jours d'existence — c'est-à-dire les projets réellement visibles et potentiellement utilisés comme dépendances en production.

Ensuite, nous avons mis en place une stratégie de **collecte en deux passes** :
- **Passe 1** — filtre `pushed:<date` — collecte **2 250 dépôts inactifs** garantis
- **Passe 2** — filtre `pushed:>date` — collecte **12 750 dépôts actifs** garantis

Pour assurer la **diversité**, nous croisons **7 tranches d'étoiles × 10 langages** — Python, JavaScript, Java, C++, Go, Ruby, Rust, TypeScript, PHP et C — pour éviter tout biais vers les projets populaires ou récents.

*[pointer la liste robustesse]*

Le script intègre également quatre mécanismes de robustesse :

- **Gestion du rate limiting** — vérifie le quota avant chaque requête et attend la réinitialisation si nécessaire
- **Détection d'expiration du token** — si le token expire en cours de route, le script s'arrête proprement avec un message clair et reprend au même point avec un nouveau token
- **Checkpoint toutes les 500 lignes** — la progression est sauvegardée dans un fichier cache JSON pour reprendre sans perte de données
- **Reprise automatique** — au redémarrage, le script charge le cache et continue exactement là où il s'est arrêté

*[montrer capture du terminal ou lancer la démo]*

Voici un exemple de l'exécution réelle avec la barre de progression.

---
`→ passer à la diapo 5`

> *"Grâce à ce script, nous avons constitué un dataset complet. Voyons sa structure."*

---

## 📊 Diapositive 5 — Dataset : vue d'ensemble *(1 minute 30s)*

*[pointer les 4 KPI cards]*

Notre dataset contient **15 000 dépôts GitHub**, avec **19 features** et une variable cible binaire `is_inactive`. La classe minoritaire représente **15%** des données.

*[pointer les badges de features par groupe]*

Les 19 features se répartissent en trois groupes :

**Numériques — 11 features** : étoiles, forks, watchers, open issues, taille du repo, âge, nombre de contributeurs, taux d'engagement, ratio étoiles/forks, temps de réponse moyen aux issues, et jours depuis le dernier push.

**Catégorielles — 2 features** : le langage de programmation et le type de licence.

**Binaires — 6 features** : présence d'une description, d'une homepage, d'un wiki, de GitHub Projects, si le repo est un fork, et s'il est archivé.

*[pointer l'encadré rouge]*

Avant la modélisation, **4 colonnes seront obligatoirement supprimées** pour éviter la fuite de données :
- `days_since_last_push` → encode directement le label
- `archived` → décision post-hoc, pas prédictive
- `full_name` et `collected_at` → simples identifiants

Il reste donc **17 features exploitables** pour entraîner le modèle.

---
`→ passer à la diapo 6`

> *"Regardons maintenant la distribution de la variable cible — c'est une contrainte clé du projet."*

---

## 📈 Diapositive 6 — Distribution de la variable cible *(1 minute 30s)*

*[pointer le mini tableau de validation]*

Notre dataset contient **12 750 dépôts actifs** — 85% — et **2 250 dépôts inactifs** — 15%.

Ce ratio de 15% satisfait la contrainte du projet : la classe minoritaire doit être entre 5% et 25%.

*[pointer class_distribution.png]*

Ce graphique confirme visuellement le déséquilibre naturel : la classe active est clairement majoritaire, ce qui reflète la réalité des dépôts GitHub visibles en production.

*[pointer language_distribution.png]*

Ce second graphique montre la distribution par langage. Le taux d'inactivité varie selon les langages, ce qui en fait une feature discriminante intéressante pour notre modèle.

Une question naturelle : ce 15%, est-ce **artificiel** ?

Non. Notre population cible n'est pas la population brute de GitHub — qui contient 420 millions de dépôts incluant projets étudiants, forks vides et tests abandonnés, où l'inactivité dépasse 70%.

Notre population est **qualifiée** : dépôts ≥ 1 étoile, ≥ 30 jours. Sur cette sous-population, Avelino et al. (2019) — une étude publiée à la conférence MSR sur 1 932 projets GitHub populaires — mesurent **~16% d'abandon**. Cela valide directement notre cible de 15%.

---
`→ passer à la diapo 7`

> *"Le dataset est validé. Voyons maintenant comment nous avons traduit notre objectif métier en métriques mesurables."*

---

## ⚖️ Diapositive 7 — Traduction métier → ML *(2 minutes)*

*[pointer le tableau de traduction]*

Voici notre tableau de traduction métier vers ML :

- **Détecter 80% des dépôts abandonnés** → maximiser le **Recall** sur la classe inactive, seuil ≥ 0,80
- **Limiter les fausses alertes** → maintenir une **Precision** ≥ 0,50
- **Équilibrer les deux** → **F1-score** ≥ 0,65
- **Évaluation globale sur données déséquilibrées** → **PR-AUC** ≥ 0,70

*[pointer le schéma FN vs FP]*

Pourquoi le **Recall** comme métrique principale ?

Regardons les deux types d'erreurs :

Un **faux négatif** — notre modèle dit "actif" alors que le dépôt est abandonné. L'équipe continue d'utiliser une dépendance à risque. Quand une faille est découverte plus tard : audit de sécurité, patch d'urgence, downtime. Selon IBM Security et Sonatype, le coût se situe entre **5 000 et 50 000 euros**.

Un **faux positif** — fausse alerte sur un dépôt actif. Un ingénieur vérifie en 30 minutes et confirme que tout va bien. Coût : **30 à 120 euros**.

*[pointer la flèche → RECALL]*

Le faux négatif coûte **50 à 400 fois plus cher**. On maximise donc le Recall — on préfère générer quelques fausses alertes plutôt que de laisser passer un dépôt véritablement abandonné.

*[pointer les badges métriques refusées]*

C'est aussi pourquoi nous refusons l'accuracy seule : un modèle qui prédirait "actif" pour tout le monde aurait déjà **85% d'accuracy** sans rien apprendre du tout.

---
`→ passer à la diapo 8`

> *"Pour conclure, faisons le bilan de ce que nous avons accompli en Phase 1."*

---

## ✅ Diapositive 8 — Conclusion *(30 secondes)*

*[pointer les 4 achievement cards]*

En Phase 1, nous avons livré quatre éléments :

- 🗄️ **Dataset** — 15 000 lignes, 19 features, déséquilibre validé à 15%, conforme à toutes les contraintes du projet
- 🌍 **Diversité** — 10 langages de programmation × 7 tranches d'étoiles, garantissant une représentativité réelle de l'écosystème
- 📄 **Documentation** — `DATASET.md` avec schéma complet, justifications et limitations ; `cadrage.md` avec objectifs métiers, traduction ML et analyse du coût asymétrique
- ⚙️ **Script** — reproductible, résumable, robuste, avec gestion automatique du rate limiting et checkpoint toutes les 500 lignes

En Phase 2, nous passerons à la modélisation :
1. Prétraitement — encodage, normalisation, gestion des valeurs sentinelles
2. Feature engineering — sélection et suppression des fuites de données
3. Modélisation — Logistic Regression, Random Forest, XGBoost
4. Évaluation — Recall ≥ 0,80 · F1 ≥ 0,65 · PR-AUC ≥ 0,70

---
`→ passer à la diapo 9`

---

## 🙏 Diapositive 9 — Merci *(5 secondes)*

*[regarder le professeur et l'audience]*

Merci pour votre attention. Nous sommes disponibles pour répondre à vos questions.

---


## ❓ Questions probables du professeur & réponses préparées

**Q : Pourquoi 180 jours comme seuil d'inactivité ?**
> 180 jours ≈ 6 mois, soit un cycle de projet standard. Assez long pour exclure les pauses temporaires, assez court pour être actionnable. Ce seuil est paramétrable dans le script.

**Q : N'avez-vous pas forcé le déséquilibre ?**
> Non. Nous avons utilisé l'échantillonnage stratifié uniquement pour corriger le biais de l'API GitHub, qui retourne 0% d'inactifs par défaut. Le déséquilibre de 15% reflète la réalité mesurée sur notre sous-population qualifiée.

**Q : Mais 70-80% des repos GitHub sont inactifs — pourquoi seulement 15% chez vous ?**
> Ce chiffre concerne la population brute : 420M+ dépôts incluant projets étudiants et forks vides. Notre population est qualifiée (≥ 1 étoile, ≥ 30 jours). Sur cette sous-population, Avelino et al. (2019) mesurent ~16% d'abandon — ce qui valide directement notre ratio.

**Q : Pourquoi exclure `days_since_last_push` ?**
> Cette feature encode directement le label — si on connaît le nombre de jours depuis le dernier push, on n'a plus besoin de prédire. C'est de la fuite de données. Elle reste dans le dataset pour l'EDA mais sera supprimée avant modélisation.

**Q : Pourquoi le Recall et pas le F1 comme métrique principale ?**
> L'asymétrie des coûts FN/FP justifie de prioriser le Recall. Un FN coûte 50 à 400× plus cher qu'un FP dans notre contexte. Le F1 est une métrique secondaire importante, mais ne doit pas être la principale.

**Q : Comment allez-vous gérer les -1.0 dans `avg_issue_response_hours` ?**
> Ce sont des valeurs sentinelles signifiant "aucune issue fermée disponible". En Phase 2 : création d'une feature binaire `has_no_issues` + remplacement par la médiane des repos avec issues.
