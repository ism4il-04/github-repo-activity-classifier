"""
RepoGuard — Streamlit dashboard for GitHub repository inactivity detection.

Set USE_MOCK_API=false and API_URL to connect to the live FastAPI backend.
"""

from __future__ import annotations

import io
import os
import random
import time
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import streamlit as st

# ── Configuration ────────────────────────────────────────────────────────────
USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() in ("1", "true", "yes")
API_URL = os.getenv("API_URL", "http://localhost:8000")
ICON_PATH = Path(__file__).parent / "repoguard_icon.png"

STATIC_MODEL_INFO: dict[str, Any] = {
    "model_name": "Gradient Boosting",
    "strategy_imbalance": "scale_pos_weight",
    "optimal_threshold": 0.05,
    "test_metrics": {
        "default_threshold_metrics": {
            "accuracy": 0.912,
            "precision": 0.487,
            "recall": 0.623,
            "f1": 0.547,
            "pr_auc": 0.581,
            "roc_auc": 0.934,
        },
        "optimal_threshold_metrics": {
            "accuracy": 0.891,
            "recall": 0.976,
            "f1": 0.412,
            "pr_auc": 0.581,
        },
    },
    "business_costs": {
        "cost_default": 663_360,
        "cost_optimal": 96_920,
        "cost_reduction_pct": 85.4,
    },
}

PROG_LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "Go",
    "Ruby", "Rust", "TypeScript", "PHP", "C", "Other",
]
LICENSES = [
    "MIT License", "Apache License 2.0",
    "GNU General Public License v3.0", "GNU General Public License v2.0",
    'BSD 3-Clause "New" or "Revised" License',
    "Mozilla Public License 2.0", "GNU Affero General Public License v3.0", "Other",
]

# ── Internationalization (EN / FR) ───────────────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "RepoGuard — Activity Classifier",
        "sidebar_subtitle": "GitHub Activity Classifier",
        "lang_label": "Language / Langue",
        "api_online": "API Online",
        "api_offline": "API Offline",
        "demo_mode": "Demo mode — mock predictions enabled",
        "model_label": "Model",
        "label_recall": "Recall",
        "footer_caption": "ENSA Tétouan · ML 2025–2026",
        "hero_title": "Repository Risk Dashboard",
        "hero_subtitle": "Predict inactivity risk for open-source repositories using public GitHub metadata.",
        "hero_badge": "Gradient Boosting",
        "tab_single": "Single Prediction",
        "tab_batch": "Batch Prediction",
        "tab_context": "Model Context",
        "section_input": "Input",
        "input_card_title": "Repository features",
        "input_card_sub": "Enter GitHub metadata to run a single detection.",
        "field_stars": "Stars",
        "field_forks": "Forks",
        "field_watchers": "Watchers",
        "field_open_issues": "Open issues",
        "field_contributors": "Contributors",
        "field_contributors_help": "Use -1 if unknown (GitHub caps at 100).",
        "field_size_kb": "Size (KB)",
        "field_age_days": "Age (days)",
        "field_engagement_rate": "Engagement rate",
        "field_stars_forks_ratio": "Stars / forks ratio",
        "field_avg_issue_response": "Avg. issue response (h)",
        "field_primary_language": "Primary language",
        "field_license": "License",
        "section_flags": "Flags",
        "flag_description": "Has description",
        "flag_wiki": "Wiki enabled",
        "flag_fork": "Is a fork",
        "flag_homepage": "Has homepage",
        "flag_projects": "Projects enabled",
        "btn_detect": "Detect",
        "how_it_works_title": "How it works",
        "how_it_works_body": (
            "The model scores inactivity probability against an optimal threshold "
            "(τ* = 5%) tuned for supply-chain risk — favoring recall over precision."
        ),
        "api_offline_error": "API is offline. Start with: `uvicorn app.api:app --port 8000`",
        "spinner_detect": "Running detection model…",
        "section_result": "Result",
        "alert_inactive_high": (
            "**Inactive repository detected** — abandonment probability **{prob:.1f}%**. "
            "Review before adopting as a dependency."
        ),
        "alert_inactive_other": (
            "**Possible inactivity** — probability **{prob:.1f}%** ({conf} confidence). "
            "Manual review recommended."
        ),
        "alert_active_borderline": (
            "**Active** with borderline signal — probability **{prob:.1f}%** ({conf} confidence). "
            "Monitor periodically."
        ),
        "alert_active_ok": (
            "**Repository appears active** — inactivity probability **{prob:.1f}%** ({conf} confidence)."
        ),
        "metric_inactivity_prob": "Inactivity probability",
        "metric_threshold": "Decision threshold (τ*)",
        "metric_confidence": "Confidence",
        "metric_verdict": "Verdict",
        "verdict_actif": "Active",
        "verdict_inactif": "Inactive",
        "delta_risk": "Risk",
        "delta_ok": "OK",
        "conf_high": "High",
        "conf_medium": "Medium",
        "conf_low": "Low",
        "api_error": "API error ({code}): {detail}",
        "api_unreachable": "Cannot reach API at {url}: {err}",
        "prediction_failed": "Prediction failed: {err}",
        "section_batch_upload": "Batch upload",
        "batch_dataset_title": "Dataset",
        "batch_dataset_sub": "Upload a CSV with one repository per row.",
        "batch_upload_help": "Required columns match the single-prediction form fields.",
        "required_columns": "Required columns",
        "preview_rows": "Preview · {n:,} rows",
        "btn_batch_run": "Run batch detection",
        "batch_api_offline": "API is offline. Start the backend first.",
        "progress_init": "Initializing batch pipeline…",
        "progress_upload": "Uploading to API…",
        "progress_complete": "Complete",
        "batch_complete": "Batch complete",
        "spinner_batch": "Processing {n:,} repositories…",
        "section_summary": "Summary",
        "metric_total": "Total",
        "metric_active": "Active",
        "metric_inactive": "Inactive",
        "metric_alert_rate": "Alert rate",
        "section_results": "Results",
        "col_stars": "Stars",
        "col_language": "Language",
        "col_inactivity_prob": "Inactivity prob.",
        "col_prediction": "Prediction",
        "col_prediction_help": "actif = maintained · inactif = at risk",
        "col_confidence": "Confidence",
        "btn_download": "Download results CSV",
        "file_process_error": "Could not process file: {err}",
        "mission_eyebrow": "Mission",
        "mission_title": "Supply-chain inactivity detection",
        "mission_body": (
            "Abandoned open-source dependencies expose teams to unpatched CVEs and "
            "breaking changes. RepoGuard flags repositories using only public GitHub "
            "signals — no clone or commit history required."
        ),
        "expander_architecture": "Architecture & feature pipeline",
        "architecture_body": """
**Pipeline (CRISP-DM)**
1. GitHub REST metadata extraction
2. Feature engineering (engagement rate, maturity bins, license/language encoding)
3. `HistGradientBoostingClassifier` with `scale_pos_weight`
4. Threshold optimization via asymmetric business cost (FN ≫ FP)

**Inputs:** 15 raw + derived features per repository.

**Output:** `actif` / `inactif` + calibrated probability vs. τ* = 0.05.
""",
        "expander_faq": "FAQ",
        "faq_body": """
**Why τ* = 5% and not 50%?**  
A missed inactive repo (false negative) costs ~167× more than a false alert.
Lowering the threshold maximizes recall for security audits.

**Can I use this without the API?**  
Set `USE_MOCK_API=true` (default) to explore the UI with simulated responses.

**What file format for batch mode?**  
CSV with the same columns as the single-prediction form.
""",
        "section_test_perf": "Test-set performance",
        "metric_accuracy": "Accuracy",
        "metric_f1": "F1-Score",
        "metric_roc_auc": "ROC-AUC",
        "metric_precision": "Precision",
        "metric_recall_default": "Recall (τ=0.50)",
        "metric_pr_auc": "PR-AUC",
        "section_deployed_threshold": "Deployed threshold (τ*)",
        "metric_optimal_tau": "Optimal τ*",
        "metric_recall_tau": "Recall @ τ*",
        "cost_reduction_eyebrow": "Business cost reduction",
        "cost_savings_text": (
            'Estimated savings: <strong style="color:#4ade80">{pct:.1f}%</strong> '
            "on held-out test set."
        ),
        "expander_costs": "Asymmetric error costs",
        "costs_body": """
| Error | Impact | Est. cost |
|-------|--------|-----------|
| **False negative** | Inactive repo marked active — no alert | ~10,000 EUR |
| **False positive** | Unnecessary manual review (~30 min) | ~60 EUR |

The classifier is tuned to minimize expected business cost, not raw accuracy.
""",
        "upload_csv_label": "Drop CSV here",
    },
    "fr": {
        "page_title": "RepoGuard — Classificateur d'activité",
        "sidebar_subtitle": "Classificateur d'activité GitHub",
        "lang_label": "Langue / Language",
        "api_online": "API en ligne",
        "api_offline": "API hors ligne",
        "demo_mode": "Mode démo — prédictions simulées activées",
        "model_label": "Modèle",
        "label_recall": "Rappel",
        "footer_caption": "ENSA Tétouan · ML 2025–2026",
        "hero_title": "Tableau de bord des risques dépôt",
        "hero_subtitle": (
            "Estimez le risque d'inactivité des dépôts open source à partir "
            "des métadonnées publiques GitHub."
        ),
        "hero_badge": "Gradient Boosting",
        "tab_single": "Prédiction unitaire",
        "tab_batch": "Prédiction par lot",
        "tab_context": "Contexte du modèle",
        "section_input": "Saisie",
        "input_card_title": "Caractéristiques du dépôt",
        "input_card_sub": "Saisissez les métadonnées GitHub pour lancer une détection.",
        "field_stars": "Étoiles",
        "field_forks": "Forks",
        "field_watchers": "Observateurs",
        "field_open_issues": "Issues ouvertes",
        "field_contributors": "Contributeurs",
        "field_contributors_help": "Utilisez -1 si inconnu (plafond GitHub : 100).",
        "field_size_kb": "Taille (Ko)",
        "field_age_days": "Âge (jours)",
        "field_engagement_rate": "Taux d'engagement",
        "field_stars_forks_ratio": "Ratio étoiles / forks",
        "field_avg_issue_response": "Délai moy. de réponse issues (h)",
        "field_primary_language": "Langage principal",
        "field_license": "Licence",
        "section_flags": "Indicateurs",
        "flag_description": "Description renseignée",
        "flag_wiki": "Wiki activé",
        "flag_fork": "Est un fork",
        "flag_homepage": "Page d'accueil",
        "flag_projects": "Projets activés",
        "btn_detect": "Détecter",
        "how_it_works_title": "Fonctionnement",
        "how_it_works_body": (
            "Le modèle estime la probabilité d'inactivité par rapport au seuil optimal "
            "(τ* = 5 %), calibré pour la chaîne d'approvisionnement — priorité au rappel."
        ),
        "api_offline_error": "API hors ligne. Démarrez avec : `uvicorn app.api:app --port 8000`",
        "spinner_detect": "Exécution du modèle de détection…",
        "section_result": "Résultat",
        "alert_inactive_high": (
            "**Dépôt inactif détecté** — probabilité d'abandon **{prob:.1f} %**. "
            "Vérifiez avant d'utiliser comme dépendance."
        ),
        "alert_inactive_other": (
            "**Inactivité possible** — probabilité **{prob:.1f} %** (confiance {conf}). "
            "Revue manuelle recommandée."
        ),
        "alert_active_borderline": (
            "**Actif** avec signal limite — probabilité **{prob:.1f} %** (confiance {conf}). "
            "Surveillez périodiquement."
        ),
        "alert_active_ok": (
            "**Dépôt semble actif** — probabilité d'inactivité **{prob:.1f} %** (confiance {conf})."
        ),
        "metric_inactivity_prob": "Probabilité d'inactivité",
        "metric_threshold": "Seuil de décision (τ*)",
        "metric_confidence": "Confiance",
        "metric_verdict": "Verdict",
        "verdict_actif": "Actif",
        "verdict_inactif": "Inactif",
        "delta_risk": "Risque",
        "delta_ok": "OK",
        "conf_high": "Élevée",
        "conf_medium": "Moyenne",
        "conf_low": "Faible",
        "api_error": "Erreur API ({code}) : {detail}",
        "api_unreachable": "Impossible de joindre l'API à {url} : {err}",
        "prediction_failed": "Échec de la prédiction : {err}",
        "section_batch_upload": "Import par lot",
        "batch_dataset_title": "Jeu de données",
        "batch_dataset_sub": "Importez un CSV avec un dépôt par ligne.",
        "batch_upload_help": "Les colonnes requises correspondent au formulaire unitaire.",
        "required_columns": "Colonnes requises",
        "preview_rows": "Aperçu · {n:,} lignes",
        "btn_batch_run": "Lancer la détection par lot",
        "batch_api_offline": "API hors ligne. Démarrez d'abord le backend.",
        "progress_init": "Initialisation du pipeline par lot…",
        "progress_upload": "Envoi vers l'API…",
        "progress_complete": "Terminé",
        "batch_complete": "Lot terminé",
        "spinner_batch": "Traitement de {n:,} dépôts…",
        "section_summary": "Synthèse",
        "metric_total": "Total",
        "metric_active": "Actifs",
        "metric_inactive": "Inactifs",
        "metric_alert_rate": "Taux d'alerte",
        "section_results": "Résultats",
        "col_stars": "Étoiles",
        "col_language": "Langage",
        "col_inactivity_prob": "Prob. inactivité",
        "col_prediction": "Prédiction",
        "col_prediction_help": "actif = maintenu · inactif = à risque",
        "col_confidence": "Confiance",
        "btn_download": "Télécharger le CSV des résultats",
        "file_process_error": "Impossible de traiter le fichier : {err}",
        "mission_eyebrow": "Mission",
        "mission_title": "Détection d'inactivité en chaîne d'approvisionnement",
        "mission_body": (
            "Les dépendances open source abandonnées exposent aux CVE non corrigées "
            "et aux ruptures de compatibilité. RepoGuard signale les dépôts à partir "
            "des seuls signaux GitHub publics — sans clonage ni historique de commits."
        ),
        "expander_architecture": "Architecture et pipeline de features",
        "architecture_body": """
**Pipeline (CRISP-DM)**
1. Extraction des métadonnées via l'API REST GitHub
2. Feature engineering (taux d'engagement, classes de maturité, encodage licence/langage)
3. `HistGradientBoostingClassifier` avec `scale_pos_weight`
4. Optimisation du seuil via coût métier asymétrique (FN ≫ FP)

**Entrées :** 15 features brutes et dérivées par dépôt.

**Sortie :** `actif` / `inactif` + probabilité calibrée vs. τ* = 0,05.
""",
        "expander_faq": "FAQ",
        "faq_body": """
**Pourquoi τ* = 5 % et non 50 % ?**  
Un dépôt inactif non détecté (faux négatif) coûte ~167× plus qu'une fausse alerte.
Abaisser le seuil maximise le rappel pour les audits de sécurité.

**Utiliser l'interface sans API ?**  
Définissez `USE_MOCK_API=true` (par défaut) pour des réponses simulées.

**Format pour le mode lot ?**  
CSV avec les mêmes colonnes que le formulaire unitaire.
""",
        "section_test_perf": "Performances sur le jeu de test",
        "metric_accuracy": "Exactitude",
        "metric_f1": "F1-Score",
        "metric_roc_auc": "ROC-AUC",
        "metric_precision": "Précision",
        "metric_recall_default": "Rappel (τ=0,50)",
        "metric_pr_auc": "PR-AUC",
        "section_deployed_threshold": "Seuil déployé (τ*)",
        "metric_optimal_tau": "τ* optimal",
        "metric_recall_tau": "Rappel @ τ*",
        "cost_reduction_eyebrow": "Réduction du coût métier",
        "cost_savings_text": (
            'Économie estimée : <strong style="color:#4ade80">{pct:.1f} %</strong> '
            "sur le jeu de test."
        ),
        "expander_costs": "Coûts d'erreur asymétriques",
        "costs_body": """
| Erreur | Impact | Coût est. |
|--------|--------|-----------|
| **Faux négatif** | Inactif classé actif — pas d'alerte | ~10 000 EUR |
| **Faux positif** | Alerte inutile — revue manuelle (~30 min) | ~60 EUR |

Le classifieur minimise le coût métier attendu, pas l'exactitude brute.
""",
        "upload_csv_label": "Déposer un CSV ici",
    },
}

_CONFIDENCE_KEYS = {"High": "conf_high", "Medium": "conf_medium", "Low": "conf_low"}


def init_i18n() -> None:
    if "lang" not in st.session_state:
        default = os.getenv("APP_LANG", "en").lower()
        st.session_state.lang = default if default in TRANSLATIONS else "en"


def t(key: str, **kwargs: Any) -> str:
    lang = st.session_state.get("lang", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
    return text.format(**kwargs) if kwargs else text


def t_confidence(conf: str) -> str:
    return t(_CONFIDENCE_KEYS.get(conf, "conf_low"))


# ── Page config ──────────────────────────────────────────────────────────────
init_i18n()
_page_icon = str(ICON_PATH) if ICON_PATH.exists() else "🛡️"
st.set_page_config(
    page_title=t("page_title"),
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-deep:     #070b14;
  --bg-base:     #0c1222;
  --glass:       rgba(18, 27, 48, 0.55);
  --glass-hover: rgba(24, 36, 62, 0.72);
  --glass-border:rgba(255, 255, 255, 0.08);
  --glass-blur:  18px;
  --accent:      #3b82f6;
  --accent-soft: rgba(59, 130, 246, 0.15);
  --accent-glow: rgba(59, 130, 246, 0.35);
  --success:     #22c55e;
  --warning:     #f59e0b;
  --danger:      #ef4444;
  --text:        #f1f5f9;
  --text-muted:  #94a3b8;
  --text-dim:    #64748b;
  --radius-lg:   16px;
  --radius-md:   12px;
  --radius-sm:   8px;
  --shadow:      0 8px 32px rgba(0, 0, 0, 0.35);
}

html, body, [class*="css"] {
  font-family: 'DM Sans', system-ui, sans-serif !important;
}

.stApp {
  background:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(59, 130, 246, 0.12), transparent),
    radial-gradient(ellipse 60% 40% at 90% 10%, rgba(139, 92, 246, 0.08), transparent),
    var(--bg-deep) !important;
  color: var(--text);
}

.block-container {
  padding-top: 1.25rem !important;
  max-width: 1180px !important;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }
[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar glass */
[data-testid="stSidebar"] {
  background: rgba(10, 15, 28, 0.85) !important;
  backdrop-filter: blur(var(--glass-blur));
  border-right: 1px solid var(--glass-border);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 4px;
  gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  padding: 0.5rem 1.25rem !important;
  transition: color 0.2s, background 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; }
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  color: #fff !important;
  box-shadow: 0 4px 20px var(--accent-glow) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.75rem !important; }

/* Glass cards (HTML) */
.glass-card {
  background: var(--glass);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem 1.75rem;
  box-shadow: var(--shadow);
  margin-bottom: 1rem;
}
.glass-card-sm {
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md);
}
.card-eyebrow {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.35rem;
}
.card-title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text);
  margin: 0 0 0.35rem;
}
.card-sub {
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.55;
  margin: 0;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--accent-soft);
  border: 1px solid rgba(59, 130, 246, 0.35);
  color: #93c5fd;
  margin-left: 0.5rem;
  vertical-align: middle;
}
.section-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin: 0 0 0.75rem;
}
.upload-hint {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.6;
}
.upload-hint strong { color: var(--text); }
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}
.status-pill.offline {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}
.status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-up { animation: fadeUp 0.4s ease both; }

/* Buttons */
.stButton > button[kind="primary"],
.stFormSubmitButton > button {
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.65rem 1.5rem !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.01em !important;
  transition: transform 0.15s, box-shadow 0.2s !important;
  box-shadow: 0 4px 24px var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 32px var(--accent-glow) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--glass) !important;
  color: var(--text) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-sm) !important;
}
.stDownloadButton > button {
  background: var(--glass) !important;
  backdrop-filter: blur(12px) !important;
  color: #93c5fd !important;
  border: 1px solid rgba(59, 130, 246, 0.35) !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--accent) !important;
  box-shadow: 0 0 20px var(--accent-glow) !important;
  transform: translateY(-1px) !important;
}

/* Inputs */
.stNumberInput input, .stTextInput input,
.stTextArea textarea, div[data-baseweb="select"] > div {
  background: rgba(7, 11, 20, 0.6) !important;
  border: 1px solid var(--glass-border) !important;
  color: var(--text) !important;
  border-radius: var(--radius-sm) !important;
}
.stNumberInput input:focus, .stTextInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
label[data-testid="stWidgetLabel"] p {
  color: var(--text-muted) !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
}

/* Metrics */
[data-testid="metric-container"] {
  background: var(--glass) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.15rem !important;
  box-shadow: var(--shadow) !important;
}
[data-testid="stMetricLabel"] p { color: var(--text-muted) !important; font-size: 0.78rem !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--glass) !important;
  backdrop-filter: blur(12px) !important;
  border: 2px dashed rgba(148, 163, 184, 0.25) !important;
  border-radius: var(--radius-lg) !important;
  padding: 0.5rem !important;
  transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
  background: var(--glass-hover) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  overflow: hidden;
}

/* Expander */
.streamlit-expanderHeader {
  background: var(--glass) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
}
details[data-testid="stExpander"] {
  background: transparent !important;
  border: none !important;
}

/* Progress */
.stProgress > div > div {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
  border-radius: 999px !important;
}
.stProgress > div {
  background: rgba(255,255,255,0.06) !important;
  border-radius: 999px !important;
}

/* Alerts — subtle glass tint */
[data-testid="stAlert"] {
  border-radius: var(--radius-md) !important;
  backdrop-filter: blur(8px);
}

code, .mono { font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }

/* Header row: title left, language right */
div[data-testid="stHorizontalBlock"]:has(.hero-header-row) {
  align-items: center !important;
  margin-bottom: 0 !important;
}
div[data-testid="column"]:has(.lang-switch-col) {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-end !important;
  justify-content: center !important;
}
div[data-testid="column"]:has(.lang-switch-col) [data-testid="stRadio"] > div {
  gap: 0.35rem !important;
  flex-wrap: nowrap !important;
}
div[data-testid="column"]:has(.lang-switch-col) [data-testid="stRadio"] label {
  background: var(--glass) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.35rem 0.85rem !important;
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  transition: all 0.15s !important;
}
div[data-testid="column"]:has(.lang-switch-col) [data-testid="stRadio"] label:hover {
  border-color: var(--accent) !important;
}
div[data-testid="column"]:has(.lang-switch-col) [data-testid="stRadio"] div[aria-checked="true"] label {
  background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  border-color: transparent !important;
  color: #fff !important;
}
div[data-testid="column"]:has(.lang-switch-col) .lang-switch-col {
  display: none;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── API layer (mock + live) ──────────────────────────────────────────────────
def _confidence_label(prob: float, threshold: float) -> str:
    margin = abs(prob - threshold)
    if margin >= 0.25:
        return "High"
    if margin >= 0.10:
        return "Medium"
    return "Low"


def mock_predict_single(payload: dict[str, Any]) -> dict[str, Any]:
    time.sleep(0.85)
    random.seed(hash(tuple(sorted(payload.items()))) % (2**32))
    prob = round(random.uniform(0.02, 0.97), 4)
    threshold = STATIC_MODEL_INFO["optimal_threshold"]
    pred = "inactif" if prob >= threshold else "actif"
    return {
        "prediction": pred,
        "probability": prob,
        "threshold": threshold,
        "confidence": _confidence_label(prob, threshold),
    }


def mock_predict_batch(df: pd.DataFrame, progress_bar: Any) -> pd.DataFrame:
    n = len(df)
    rows: list[dict[str, Any]] = []
    threshold = STATIC_MODEL_INFO["optimal_threshold"]

    for i, (_, row) in enumerate(df.iterrows()):
        time.sleep(0.04)
        prob = round(random.uniform(0.01, 0.99), 4)
        pred = "inactif" if prob >= threshold else "actif"
        rows.append({
            **row.to_dict(),
            "probability_inactive": prob,
            "prediction": pred,
            "confidence": _confidence_label(prob, threshold),
        })
        if progress_bar is not None:
            progress_bar.progress(min((i + 1) / n, 1.0))

    return pd.DataFrame(rows)


def mock_health() -> bool:
    return True


def mock_model_info() -> dict[str, Any]:
    return STATIC_MODEL_INFO


@st.cache_data(ttl=30)
def fetch_model_info_live() -> dict[str, Any] | None:
    try:
        r = httpx.get(f"{API_URL}/model/info", timeout=4.0)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def api_health() -> bool:
    if USE_MOCK_API:
        return mock_health()
    try:
        r = httpx.get(f"{API_URL}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def fetch_model_info() -> dict[str, Any] | None:
    if USE_MOCK_API:
        return mock_model_info()
    return fetch_model_info_live()


def predict_single(payload: dict[str, Any]) -> dict[str, Any]:
    if USE_MOCK_API:
        return mock_predict_single(payload)
    r = httpx.post(f"{API_URL}/predict", json=payload, timeout=10.0)
    r.raise_for_status()
    return r.json()


def predict_batch_csv(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if USE_MOCK_API:
        df = pd.read_csv(io.BytesIO(file_bytes))
        return df

    files = {"file": (filename, file_bytes, "text/csv")}
    r = httpx.post(f"{API_URL}/predict/batch", files=files, timeout=120.0)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))


def render_result_alert(res: dict[str, Any]) -> None:
    pred = res["prediction"]
    prob = res["probability"] * 100
    conf = t_confidence(res["confidence"])
    is_inactive = pred == "inactif"
    conf_key = res["confidence"]

    if is_inactive and conf_key == "High":
        st.error(t("alert_inactive_high", prob=prob))
    elif is_inactive:
        st.warning(t("alert_inactive_other", prob=prob, conf=conf))
    elif conf_key == "Low":
        st.warning(t("alert_active_borderline", prob=prob, conf=conf))
    else:
        st.success(t("alert_active_ok", prob=prob, conf=conf))


# ── Sidebar ──────────────────────────────────────────────────────────────────
online = api_health()
model_info = fetch_model_info() or STATIC_MODEL_INFO
m_def = model_info.get("test_metrics", {}).get("default_threshold_metrics", {})
tau = model_info.get("optimal_threshold", 0.05)

with st.sidebar:
    if ICON_PATH.exists():
        st.image(str(ICON_PATH), width=48)
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem">
          <div style="font-size:1.15rem;font-weight:700;color:#f1f5f9">RepoGuard</div>
          <div style="font-size:0.75rem;color:#64748b">{t('sidebar_subtitle')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    pill_cls = "" if online else " offline"
    pill_lbl = t("api_online") if online else t("api_offline")
    st.markdown(
        f'<span class="status-pill{pill_cls}"><span class="status-dot"></span>{pill_lbl}</span>',
        unsafe_allow_html=True,
    )
    if USE_MOCK_API:
        st.caption(t("demo_mode"))

    st.markdown(
        f"""
        <div class="glass-card glass-card-sm" style="margin-top:1rem">
          <div class="card-eyebrow">{t('model_label')}</div>
          <div style="font-weight:600;color:#f1f5f9">{model_info.get('model_name', '—')}</div>
          <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.25rem">
            τ* = {tau} · {t('label_recall')} {m_def.get('recall', 0):.3f}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption(t("footer_caption"))

# ── Header + language (same row) ─────────────────────────────────────────────
_header_left, _header_right = st.columns([5, 1], gap="medium", vertical_alignment="center")
with _header_left:
    st.markdown('<div class="hero-header-row"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="fade-up">
          <h1 style="font-size:1.75rem;font-weight:700;letter-spacing:-0.03em;margin:0;color:#f1f5f9">
            {t('hero_title')}
            <span class="hero-badge">{t('hero_badge')}</span>
          </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
with _header_right:
    st.markdown('<div class="lang-switch-col"></div>', unsafe_allow_html=True)
    st.radio(
        t("lang_label"),
        options=["en", "fr"],
        format_func=lambda code: "EN" if code == "en" else "FR",
        horizontal=True,
        key="lang",
        index=0 if st.session_state.get("lang", "en") == "en" else 1,
        label_visibility="collapsed",
    )

st.markdown(
    f"""
    <p class="card-sub fade-up" style="margin:0.5rem 0 0.75rem;max-width:640px">
      {t('hero_subtitle')}
    </p>
    """,
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_context = st.tabs(
    [t("tab_single"), t("tab_batch"), t("tab_context")]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Single Prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab_single:
    col_input, col_spacer = st.columns([2, 1], gap="large")

    with col_input:
        st.markdown(f'<p class="section-label">{t("section_input")}</p>', unsafe_allow_html=True)
        with st.container(border=False):
            st.markdown(
                f'<div class="glass-card" style="margin-bottom:0">'
                f'<div class="card-eyebrow">{t("input_card_title")}</div>'
                f'<p class="card-sub">{t("input_card_sub")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            with st.form("single_predict_form", border=False):
                r1a, r1b, r1c = st.columns(3)
                with r1a:
                    stars = st.number_input(t("field_stars"), min_value=0, value=8, step=1)
                    forks = st.number_input(t("field_forks"), min_value=0, value=2, step=1)
                    watchers = st.number_input(t("field_watchers"), min_value=0, value=8, step=1)
                with r1b:
                    open_issues = st.number_input(t("field_open_issues"), min_value=0, value=1, step=1)
                    contributor_count = st.number_input(
                        t("field_contributors"), min_value=-1, value=3, step=1,
                        help=t("field_contributors_help"),
                    )
                    size_kb = st.number_input(t("field_size_kb"), min_value=0.0, value=1500.0, step=100.0)
                with r1c:
                    repo_age_days = st.number_input(t("field_age_days"), min_value=30, value=600, step=10)
                    engagement_rate = st.number_input(
                        t("field_engagement_rate"), min_value=0.0, value=0.016, format="%.5f",
                    )
                    stars_forks_ratio = st.number_input(
                        t("field_stars_forks_ratio"), min_value=0.0, value=4.0, format="%.2f",
                    )

                r2a, r2b = st.columns(2)
                with r2a:
                    avg_issue_response_hours = st.number_input(
                        t("field_avg_issue_response"), min_value=-1.0, value=24.0, step=1.0,
                    )
                    language = st.selectbox(t("field_primary_language"), PROG_LANGUAGES)
                with r2b:
                    license_name = st.selectbox(t("field_license"), LICENSES)
                    st.markdown(
                        f'<p class="section-label" style="margin-top:0.5rem">{t("section_flags")}</p>',
                        unsafe_allow_html=True,
                    )
                    f1, f2 = st.columns(2)
                    with f1:
                        has_description = st.checkbox(t("flag_description"), value=True)
                        has_wiki = st.checkbox(t("flag_wiki"), value=True)
                        is_fork = st.checkbox(t("flag_fork"), value=False)
                    with f2:
                        has_homepage = st.checkbox(t("flag_homepage"), value=False)
                        has_projects = st.checkbox(t("flag_projects"), value=False)

                st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
                detect = st.form_submit_button(
                    t("btn_detect"), type="primary", use_container_width=True,
                )

    with col_spacer:
        st.markdown(
            f"""
            <div class="glass-card glass-card-sm fade-up" style="margin-top:1.85rem">
              <div class="card-eyebrow">{t('how_it_works_title')}</div>
              <p class="card-sub">{t('how_it_works_body')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if detect:
        if not online and not USE_MOCK_API:
            st.error(t("api_offline_error"))
        else:
            payload = {
                "stars": stars,
                "forks": forks,
                "open_issues": open_issues,
                "watchers": watchers,
                "size_kb": size_kb,
                "repo_age_days": repo_age_days,
                "contributor_count": contributor_count,
                "avg_issue_response_hours": (
                    None if avg_issue_response_hours == -1.0 else avg_issue_response_hours
                ),
                "engagement_rate": engagement_rate,
                "stars_forks_ratio": stars_forks_ratio,
                "language": language,
                "license": license_name,
                "has_description": has_description,
                "has_homepage": has_homepage,
                "has_wiki": has_wiki,
                "has_projects": has_projects,
                "is_fork": is_fork,
            }
            try:
                with st.spinner(t("spinner_detect")):
                    res = predict_single(payload)

                st.markdown(
                    f'<p class="section-label" style="margin-top:1.25rem">{t("section_result")}</p>',
                    unsafe_allow_html=True,
                )
                render_result_alert(res)

                prob = res["probability"]
                threshold = res["threshold"]
                inactive_prob_pct = prob * 100
                verdict = t("verdict_inactif") if res["prediction"] == "inactif" else t("verdict_actif")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("metric_inactivity_prob"), f"{inactive_prob_pct:.1f}%")
                m2.metric(t("metric_threshold"), f"{threshold * 100:.0f}%")
                m3.metric(t("metric_confidence"), t_confidence(res["confidence"]))
                m4.metric(
                    t("metric_verdict"),
                    verdict,
                    delta=t("delta_risk") if res["prediction"] == "inactif" else t("delta_ok"),
                    delta_color="inverse" if res["prediction"] == "inactif" else "normal",
                )

            except httpx.HTTPStatusError as e:
                st.error(t("api_error", code=e.response.status_code, detail=e.response.text))
            except httpx.RequestError as e:
                st.error(t("api_unreachable", url=API_URL, err=e))
            except Exception as e:
                st.error(t("prediction_failed", err=e))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Batch Prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab_batch:
    st.markdown(f'<p class="section-label">{t("section_batch_upload")}</p>', unsafe_allow_html=True)

    upload_col, info_col = st.columns([3, 2], gap="large")

    with upload_col:
        with st.container():
            st.markdown(
                f"""
                <div class="glass-card" style="padding-bottom:0.5rem;margin-bottom:0.75rem">
                  <div class="card-eyebrow">{t('batch_dataset_title')}</div>
                  <p class="card-sub">{t('batch_dataset_sub')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader(
                t("upload_csv_label"),
                type=["csv"],
                label_visibility="collapsed",
                help=t("batch_upload_help"),
            )

    with info_col:
        st.markdown(
            f"""
            <div class="glass-card glass-card-sm">
              <div class="card-eyebrow">{t('required_columns')}</div>
              <p class="card-sub mono" style="font-size:0.72rem;margin-top:0.5rem">
                stars, forks, open_issues, watchers, size_kb, repo_age_days,
                contributor_count, avg_issue_response_hours, engagement_rate,
                stars_forks_ratio, language, license, has_description,
                has_homepage, has_wiki, has_projects, is_fork
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if uploaded is not None:
        try:
            raw_bytes = uploaded.getvalue()
            df_preview = pd.read_csv(io.BytesIO(raw_bytes))

            st.markdown(
                f'<p class="section-label">{t("preview_rows", n=len(df_preview))}</p>',
                unsafe_allow_html=True,
            )
            st.dataframe(df_preview.head(8), use_container_width=True, hide_index=True)

            run_batch = st.button(
                t("btn_batch_run"),
                type="primary",
                use_container_width=False,
                key="batch_run",
            )

            if run_batch:
                if not online and not USE_MOCK_API:
                    st.error(t("batch_api_offline"))
                else:
                    progress = st.progress(0.0, text=t("progress_init"))

                    with st.spinner(t("spinner_batch", n=len(df_preview))):
                        if USE_MOCK_API:
                            df_out = mock_predict_batch(df_preview, progress)
                        else:
                            progress.progress(0.35, text=t("progress_upload"))
                            df_out = predict_batch_csv(raw_bytes, uploaded.name)
                            progress.progress(1.0, text=t("progress_complete"))

                    progress.progress(1.0, text=t("batch_complete"))
                    time.sleep(0.15)
                    progress.empty()

                    total = len(df_out)
                    inactifs = int((df_out["prediction"] == "inactif").sum()) if "prediction" in df_out else 0
                    actifs = total - inactifs

                    st.markdown(f'<p class="section-label">{t("section_summary")}</p>', unsafe_allow_html=True)
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric(t("metric_total"), f"{total:,}")
                    s2.metric(t("metric_active"), f"{actifs:,}", f"{actifs / total * 100:.1f}%" if total else "—")
                    s3.metric(
                        t("metric_inactive"), f"{inactifs:,}",
                        f"{inactifs / total * 100:.1f}%" if total else "—",
                        delta_color="inverse",
                    )
                    s4.metric(t("metric_alert_rate"), f"{inactifs / total * 100:.1f}%" if total else "—")

                    st.markdown(f'<p class="section-label">{t("section_results")}</p>', unsafe_allow_html=True)

                    display_cols = [
                        c for c in [
                            "stars", "language", "probability_inactive",
                            "prediction", "confidence",
                        ]
                        if c in df_out.columns
                    ]
                    sort_df = df_out
                    if "probability_inactive" in df_out.columns:
                        sort_df = df_out.sort_values("probability_inactive", ascending=False)

                    table_df = sort_df[display_cols] if display_cols else sort_df
                    if "confidence" in table_df.columns:
                        table_df = table_df.copy()
                        table_df["confidence"] = table_df["confidence"].map(
                            lambda c: t_confidence(c) if c in _CONFIDENCE_KEYS else c
                        )

                    st.dataframe(
                        table_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "stars": st.column_config.NumberColumn(t("col_stars"), format="%d"),
                            "language": st.column_config.TextColumn(t("col_language")),
                            "probability_inactive": st.column_config.ProgressColumn(
                                t("col_inactivity_prob"),
                                min_value=0,
                                max_value=1,
                                format="%.2f",
                            ),
                            "prediction": st.column_config.TextColumn(
                                t("col_prediction"),
                                help=t("col_prediction_help"),
                            ),
                            "confidence": st.column_config.TextColumn(t("col_confidence")),
                        },
                    )

                    st.download_button(
                        label=t("btn_download"),
                        data=df_out.to_csv(index=False).encode("utf-8"),
                        file_name=f"repoguard_{uploaded.name}",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                    )

        except Exception as exc:
            st.error(t("file_process_error", err=exc))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Model Context
# ══════════════════════════════════════════════════════════════════════════════
with tab_context:
    info = model_info
    metrics_def = info.get("test_metrics", {}).get("default_threshold_metrics", {})
    metrics_opt = info.get("test_metrics", {}).get("optimal_threshold_metrics", {})
    costs = info.get("business_costs", {})

    dash_left, dash_right = st.columns([5, 4], gap="large")

    with dash_left:
        st.markdown(
            f"""
            <div class="glass-card fade-up">
              <div class="card-eyebrow">{t('mission_eyebrow')}</div>
              <h2 class="card-title">{t('mission_title')}</h2>
              <p class="card-sub">{t('mission_body')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(t("expander_architecture"), expanded=False):
            st.markdown(t("architecture_body"))

        with st.expander(t("expander_faq"), expanded=False):
            st.markdown(t("faq_body"))

    with dash_right:
        st.markdown(f'<p class="section-label">{t("section_test_perf")}</p>', unsafe_allow_html=True)

        row1_a, row1_b, row1_c = st.columns(3)
        row1_a.metric(t("metric_accuracy"), f"{metrics_def.get('accuracy', 0):.3f}")
        row1_b.metric(t("metric_f1"), f"{metrics_def.get('f1', 0):.3f}")
        row1_c.metric(t("metric_roc_auc"), f"{metrics_def.get('roc_auc', 0):.3f}")

        row2_a, row2_b, row2_c = st.columns(3)
        row2_a.metric(t("metric_precision"), f"{metrics_def.get('precision', 0):.3f}")
        row2_b.metric(t("metric_recall_default"), f"{metrics_def.get('recall', 0):.3f}")
        row2_c.metric(t("metric_pr_auc"), f"{metrics_def.get('pr_auc', 0):.3f}")

        st.markdown(
            f'<p class="section-label" style="margin-top:0.5rem">{t("section_deployed_threshold")}</p>',
            unsafe_allow_html=True,
        )
        o1, o2 = st.columns(2)
        o1.metric(t("metric_optimal_tau"), f"{info.get('optimal_threshold', 0.05):.2f}")
        o2.metric(t("metric_recall_tau"), f"{metrics_opt.get('recall', 0):.3f}")

        if costs:
            pct = costs.get("cost_reduction_pct", 85.4)
            st.markdown(
                f"""
                <div class="glass-card glass-card-sm" style="margin-top:0.75rem">
                  <div class="card-eyebrow">{t('cost_reduction_eyebrow')}</div>
                  <div style="display:flex;align-items:baseline;gap:0.6rem;flex-wrap:wrap">
                    <span style="color:#f87171;text-decoration:line-through;font-size:0.9rem">
                      {costs.get('cost_default', 0):,.0f} EUR
                    </span>
                    <span style="color:#64748b">→</span>
                    <span style="color:#4ade80;font-size:1.2rem;font-weight:700">
                      {costs.get('cost_optimal', 0):,.0f} EUR
                    </span>
                  </div>
                  <p class="card-sub" style="margin-top:0.5rem">
                    {t('cost_savings_text', pct=pct)}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander(t("expander_costs"), expanded=False):
            st.markdown(t("costs_body"))
