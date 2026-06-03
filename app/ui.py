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

LANGUAGES = [
    "Python", "JavaScript", "Java", "C++", "Go",
    "Ruby", "Rust", "TypeScript", "PHP", "C", "Other",
]
LICENSES = [
    "MIT License", "Apache License 2.0",
    "GNU General Public License v3.0", "GNU General Public License v2.0",
    'BSD 3-Clause "New" or "Revised" License',
    "Mozilla Public License 2.0", "GNU Affero General Public License v3.0", "Other",
]

# ── Page config ──────────────────────────────────────────────────────────────
_page_icon = str(ICON_PATH) if ICON_PATH.exists() else "🛡️"
st.set_page_config(
    page_title="RepoGuard — Activity Classifier",
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
    prob = res["probability"]
    conf = res["confidence"]
    is_inactive = pred == "inactif"

    if is_inactive and conf == "High":
        st.error(
            f"**Inactive repository detected** — abandonment probability "
            f"**{prob * 100:.1f}%**. Review before adopting as a dependency."
        )
    elif is_inactive:
        st.warning(
            f"**Possible inactivity** — probability **{prob * 100:.1f}%** "
            f"({conf} confidence). Manual review recommended."
        )
    elif conf == "Low":
        st.warning(
            f"**Active** with borderline signal — probability **{prob * 100:.1f}%** "
            f"({conf} confidence). Monitor periodically."
        )
    else:
        st.success(
            f"**Repository appears active** — inactivity probability "
            f"**{prob * 100:.1f}%** ({conf} confidence)."
        )


# ── Sidebar ──────────────────────────────────────────────────────────────────
online = api_health()
model_info = fetch_model_info() or STATIC_MODEL_INFO
m_def = model_info.get("test_metrics", {}).get("default_threshold_metrics", {})
tau = model_info.get("optimal_threshold", 0.05)

with st.sidebar:
    if ICON_PATH.exists():
        st.image(str(ICON_PATH), width=48)
    st.markdown(
        """
        <div style="margin-bottom:0.5rem">
          <div style="font-size:1.15rem;font-weight:700;color:#f1f5f9">RepoGuard</div>
          <div style="font-size:0.75rem;color:#64748b">GitHub Activity Classifier</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    pill_cls = "" if online else " offline"
    pill_lbl = "API Online" if online else "API Offline"
    st.markdown(
        f'<span class="status-pill{pill_cls}"><span class="status-dot"></span>{pill_lbl}</span>',
        unsafe_allow_html=True,
    )
    if USE_MOCK_API:
        st.caption("Demo mode — mock predictions enabled")

    st.markdown(
        f"""
        <div class="glass-card glass-card-sm" style="margin-top:1rem">
          <div class="card-eyebrow">Model</div>
          <div style="font-weight:600;color:#f1f5f9">{model_info.get('model_name', '—')}</div>
          <div style="font-size:0.78rem;color:#94a3b8;margin-top:0.25rem">
            τ* = {tau} · Recall {m_def.get('recall', 0):.3f}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("ENSA Tétouan · ML 2025–2026")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="fade-up" style="margin-bottom:0.5rem">
      <h1 style="font-size:1.75rem;font-weight:700;letter-spacing:-0.03em;margin:0;color:#f1f5f9">
        Repository Risk Dashboard
        <span class="hero-badge">Gradient Boosting</span>
      </h1>
      <p class="card-sub" style="margin-top:0.5rem;max-width:640px">
        Predict inactivity risk for open-source repositories using public GitHub metadata.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_context = st.tabs(
    ["Single Prediction", "Batch Prediction", "Model Context"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Single Prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab_single:
    col_input, col_spacer = st.columns([2, 1], gap="large")

    with col_input:
        st.markdown('<p class="section-label">Input</p>', unsafe_allow_html=True)
        with st.container(border=False):
            st.markdown(
                '<div class="glass-card" style="margin-bottom:0">'
                '<div class="card-eyebrow">Repository features</div>'
                '<p class="card-sub">Enter GitHub metadata to run a single detection.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.form("single_predict_form", border=False):
                r1a, r1b, r1c = st.columns(3)
                with r1a:
                    stars = st.number_input("Stars", min_value=0, value=8, step=1)
                    forks = st.number_input("Forks", min_value=0, value=2, step=1)
                    watchers = st.number_input("Watchers", min_value=0, value=8, step=1)
                with r1b:
                    open_issues = st.number_input("Open issues", min_value=0, value=1, step=1)
                    contributor_count = st.number_input(
                        "Contributors", min_value=-1, value=3, step=1,
                        help="Use -1 if unknown (GitHub caps at 100).",
                    )
                    size_kb = st.number_input("Size (KB)", min_value=0.0, value=1500.0, step=100.0)
                with r1c:
                    repo_age_days = st.number_input("Age (days)", min_value=30, value=600, step=10)
                    engagement_rate = st.number_input(
                        "Engagement rate", min_value=0.0, value=0.016, format="%.5f",
                    )
                    stars_forks_ratio = st.number_input(
                        "Stars / forks ratio", min_value=0.0, value=4.0, format="%.2f",
                    )

                r2a, r2b = st.columns(2)
                with r2a:
                    avg_issue_response_hours = st.number_input(
                        "Avg. issue response (h)", min_value=-1.0, value=24.0, step=1.0,
                    )
                    language = st.selectbox("Primary language", LANGUAGES)
                with r2b:
                    license_name = st.selectbox("License", LICENSES)
                    st.markdown('<p class="section-label" style="margin-top:0.5rem">Flags</p>',
                                  unsafe_allow_html=True)
                    f1, f2 = st.columns(2)
                    with f1:
                        has_description = st.checkbox("Has description", value=True)
                        has_wiki = st.checkbox("Wiki enabled", value=True)
                        is_fork = st.checkbox("Is a fork", value=False)
                    with f2:
                        has_homepage = st.checkbox("Has homepage", value=False)
                        has_projects = st.checkbox("Projects enabled", value=False)

                st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
                detect = st.form_submit_button(
                    "Detect", type="primary", use_container_width=True,
                )

    with col_spacer:
        st.markdown(
            """
            <div class="glass-card glass-card-sm fade-up" style="margin-top:1.85rem">
              <div class="card-eyebrow">How it works</div>
              <p class="card-sub">
                The model scores inactivity probability against an optimal threshold
                (τ* = 5%) tuned for supply-chain risk — favoring recall over precision.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if detect:
        if not online and not USE_MOCK_API:
            st.error("API is offline. Start with: `uvicorn app.api:app --port 8000`")
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
                with st.spinner("Running detection model…"):
                    res = predict_single(payload)

                st.markdown('<p class="section-label" style="margin-top:1.25rem">Result</p>',
                            unsafe_allow_html=True)
                render_result_alert(res)

                prob = res["probability"]
                threshold = res["threshold"]
                conf = res["confidence"]
                inactive_prob_pct = prob * 100
                active_prob_pct = (1 - prob) * 100

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Inactivity probability", f"{inactive_prob_pct:.1f}%")
                m2.metric("Decision threshold (τ*)", f"{threshold * 100:.0f}%")
                m3.metric("Confidence", conf)
                m4.metric(
                    "Verdict",
                    res["prediction"].capitalize(),
                    delta=f"{'Risk' if res['prediction'] == 'inactif' else 'OK'}",
                    delta_color="inverse" if res["prediction"] == "inactif" else "normal",
                )

            except httpx.HTTPStatusError as e:
                st.error(f"API error ({e.response.status_code}): {e.response.text}")
            except httpx.RequestError as e:
                st.error(f"Cannot reach API at {API_URL}: {e}")
            except Exception as e:
                st.error(f"Prediction failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Batch Prediction
# ══════════════════════════════════════════════════════════════════════════════
with tab_batch:
    st.markdown('<p class="section-label">Batch upload</p>', unsafe_allow_html=True)

    upload_col, info_col = st.columns([3, 2], gap="large")

    with upload_col:
        with st.container():
            st.markdown(
                """
                <div class="glass-card" style="padding-bottom:0.5rem;margin-bottom:0.75rem">
                  <div class="card-eyebrow">Dataset</div>
                  <p class="card-sub">Upload a CSV with one repository per row.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader(
                "Drop CSV here",
                type=["csv"],
                label_visibility="collapsed",
                help="Required columns match the single-prediction form fields.",
            )

    with info_col:
        st.markdown(
            """
            <div class="glass-card glass-card-sm">
              <div class="card-eyebrow">Required columns</div>
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
                f'<p class="section-label">Preview · {len(df_preview):,} rows</p>',
                unsafe_allow_html=True,
            )
            st.dataframe(df_preview.head(8), use_container_width=True, hide_index=True)

            run_batch = st.button(
                "Run batch detection",
                type="primary",
                use_container_width=False,
                key="batch_run",
            )

            if run_batch:
                if not online and not USE_MOCK_API:
                    st.error("API is offline. Start the backend first.")
                else:
                    progress = st.progress(0.0, text="Initializing batch pipeline…")

                    with st.spinner(f"Processing {len(df_preview):,} repositories…"):
                        if USE_MOCK_API:
                            df_out = mock_predict_batch(df_preview, progress)
                        else:
                            progress.progress(0.35, text="Uploading to API…")
                            df_out = predict_batch_csv(raw_bytes, uploaded.name)
                            progress.progress(1.0, text="Complete")

                    progress.progress(1.0, text="Batch complete")
                    time.sleep(0.15)
                    progress.empty()

                    total = len(df_out)
                    inactifs = int((df_out["prediction"] == "inactif").sum()) if "prediction" in df_out else 0
                    actifs = total - inactifs

                    st.markdown('<p class="section-label">Summary</p>', unsafe_allow_html=True)
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("Total", f"{total:,}")
                    s2.metric("Active", f"{actifs:,}", f"{actifs / total * 100:.1f}%" if total else "—")
                    s3.metric(
                        "Inactive", f"{inactifs:,}",
                        f"{inactifs / total * 100:.1f}%" if total else "—",
                        delta_color="inverse",
                    )
                    s4.metric("Alert rate", f"{inactifs / total * 100:.1f}%" if total else "—")

                    st.markdown('<p class="section-label">Results</p>', unsafe_allow_html=True)

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

                    st.dataframe(
                        sort_df[display_cols] if display_cols else sort_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "stars": st.column_config.NumberColumn("Stars", format="%d"),
                            "language": st.column_config.TextColumn("Language"),
                            "probability_inactive": st.column_config.ProgressColumn(
                                "Inactivity prob.",
                                min_value=0,
                                max_value=1,
                                format="%.2f",
                            ),
                            "prediction": st.column_config.TextColumn(
                                "Prediction",
                                help="actif = maintained · inactif = at risk",
                            ),
                            "confidence": st.column_config.TextColumn("Confidence"),
                        },
                    )

                    st.download_button(
                        label="Download results CSV",
                        data=df_out.to_csv(index=False).encode("utf-8"),
                        file_name=f"repoguard_{uploaded.name}",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                    )

        except Exception as exc:
            st.error(f"Could not process file: {exc}")


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
            """
            <div class="glass-card fade-up">
              <div class="card-eyebrow">Mission</div>
              <h2 class="card-title">Supply-chain inactivity detection</h2>
              <p class="card-sub">
                Abandoned open-source dependencies expose teams to unpatched CVEs and
                breaking changes. RepoGuard flags repositories using only public GitHub
                signals — no clone or commit history required.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Architecture & feature pipeline", expanded=False):
            st.markdown(
                """
                **Pipeline (CRISP-DM)**
                1. GitHub REST metadata extraction
                2. Feature engineering (engagement rate, maturity bins, license/language encoding)
                3. `HistGradientBoostingClassifier` with `scale_pos_weight`
                4. Threshold optimization via asymmetric business cost (FN ≫ FP)

                **Inputs:** 15 raw + derived features per repository.

                **Output:** `actif` / `inactif` + calibrated probability vs. τ* = 0.05.
                """
            )

        with st.expander("FAQ", expanded=False):
            st.markdown(
                """
                **Why τ* = 5% and not 50%?**  
                A missed inactive repo (false negative) costs ~167× more than a false alert.
                Lowering the threshold maximizes recall for security audits.

                **Can I use this without the API?**  
                Set `USE_MOCK_API=true` (default) to explore the UI with simulated responses.

                **What file format for batch mode?**  
                CSV with the same columns as the single-prediction form.
                """
            )

    with dash_right:
        st.markdown('<p class="section-label">Test-set performance</p>', unsafe_allow_html=True)

        row1_a, row1_b, row1_c = st.columns(3)
        row1_a.metric("Accuracy", f"{metrics_def.get('accuracy', 0):.3f}")
        row1_b.metric("F1-Score", f"{metrics_def.get('f1', 0):.3f}")
        row1_c.metric("ROC-AUC", f"{metrics_def.get('roc_auc', 0):.3f}")

        row2_a, row2_b, row2_c = st.columns(3)
        row2_a.metric("Precision", f"{metrics_def.get('precision', 0):.3f}")
        row2_b.metric("Recall (τ=0.50)", f"{metrics_def.get('recall', 0):.3f}")
        row2_c.metric("PR-AUC", f"{metrics_def.get('pr_auc', 0):.3f}")

        st.markdown('<p class="section-label" style="margin-top:0.5rem">Deployed threshold (τ*)</p>',
                    unsafe_allow_html=True)
        o1, o2 = st.columns(2)
        o1.metric("Optimal τ*", f"{info.get('optimal_threshold', 0.05):.2f}")
        o2.metric("Recall @ τ*", f"{metrics_opt.get('recall', 0):.3f}")

        if costs:
            st.markdown(
                f"""
                <div class="glass-card glass-card-sm" style="margin-top:0.75rem">
                  <div class="card-eyebrow">Business cost reduction</div>
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
                    Estimated savings: <strong style="color:#4ade80">
                    {costs.get('cost_reduction_pct', 85.4):.1f}%</strong> on held-out test set.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Asymmetric error costs", expanded=False):
            st.markdown(
                """
                | Error | Impact | Est. cost |
                |-------|--------|-----------|
                | **False negative** | Inactive repo marked active — no alert | ~10,000 EUR |
                | **False positive** | Unnecessary manual review (~30 min) | ~60 EUR |

                The classifier is tuned to minimize expected business cost, not raw accuracy.
                """
            )
