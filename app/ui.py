import os
import io
import streamlit as st
import httpx
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(
    page_title="GitHub Repository Activity Classifier",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS for Premium Design
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stAlert {
        border-radius: 8px;
    }
    .metric-card {
        background-color: #1e222b;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 1rem;
    }
    .metric-card.active {
        border-left-color: #00e676;
    }
</style>
""", unsafe_allow_html=True)

st.title("🐙 Classifier d'Activité de Dépôts GitHub")
st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3 = st.tabs([
    "🔍 Prédiction Unitaire", 
    "📁 Prédiction par Lot (Batch)", 
    "ℹ️ Informations Modèle & Contexte Métier"
])

# --- TAB 1: Single Prediction ---
with tab1:
    st.subheader("Vérifier un Dépôt Unique")
    st.write("Saisissez les caractéristiques du dépôt ci-dessous pour prédire s'il est à risque d'inactivité/abandon.")
    
    with st.form("predict_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📊 Métriques de la Communauté")
            stars = st.number_input("Stars (Étoiles)", min_value=0, value=8, step=1, help="Nombre de stars du dépôt")
            forks = st.number_input("Forks", min_value=0, value=2, step=1, help="Nombre de forks du dépôt")
            watchers = st.number_input("Watchers", min_value=0, value=8, step=1, help="Nombre d'abonnés")
            contributor_count = st.number_input("Nombre de contributeurs", min_value=-1, value=3, step=1, help="Utiliser -1 si inconnu (Cappe à 100)")
            
        with col2:
            st.markdown("### ⚙️ Métadonnées Dépôt")
            size_kb = st.number_input("Taille du dépôt (KB)", min_value=0.0, value=1500.0, step=100.0, help="Taille en Kilooctets")
            repo_age_days = st.number_input("Âge du dépôt (jours)", min_value=30, value=600, step=10, help="Nombre de jours depuis la création (min 30)")
            avg_issue_response_hours = st.number_input("Délai moyen réponse issues (heures)", min_value=-1.0, value=24.0, step=1.0, help="Délai en heures. Utiliser -1.0 si absent/aucune issue closed")
            engagement_rate = st.number_input("Taux d'engagement", min_value=0.0, value=0.016, format="%.5f", help="(stars + forks) / age_days")
            stars_forks_ratio = st.number_input("Rapport Stars/Forks", min_value=0.0, value=4.0, format="%.2f", help="stars / max(1, forks)")
            
        with col3:
            st.markdown("### 🏷️ Configurations & Langages")
            language = st.selectbox("Langage Principal", [
                "Python", "JavaScript", "Java", "C++", "Go", 
                "Ruby", "Rust", "TypeScript", "PHP", "C", "Other"
            ])
            license_name = st.selectbox("Licence", [
                "MIT License", "Apache License 2.0", "GNU General Public License v3.0", 
                "GNU General Public License v2.0", "BSD 3-Clause \"New\" or \"Revised\" License",
                "Mozilla Public License 2.0", "GNU Affero General Public License v3.0", "Other"
            ])
            
            st.markdown("### 🎛️ Indicateurs Booléens")
            has_description = st.checkbox("Description présente", value=True)
            has_homepage = st.checkbox("Site Web présent", value=False)
            has_wiki = st.checkbox("Wiki activé", value=True)
            has_projects = st.checkbox("Projets activés", value=False)
            is_fork = st.checkbox("Le dépôt est un fork", value=False)
            
        submit_btn = st.form_submit_button("🔍 Lancer l'Analyse")
        
    if submit_btn:
        payload = {
            "stars": stars,
            "forks": forks,
            "open_issues": 1 if forks > 0 else 0,  # Proxy for raw open issues if needed
            "watchers": watchers,
            "size_kb": size_kb,
            "repo_age_days": repo_age_days,
            "contributor_count": contributor_count,
            "avg_issue_response_hours": None if avg_issue_response_hours == -1.0 else avg_issue_response_hours,
            "engagement_rate": engagement_rate,
            "stars_forks_ratio": stars_forks_ratio,
            "language": language,
            "license": license_name,
            "has_description": has_description,
            "has_homepage": has_homepage,
            "has_wiki": has_wiki,
            "has_projects": has_projects,
            "is_fork": is_fork
        }
        
        # Make request to API
        try:
            with st.spinner("Analyse du dépôt par l'API..."):
                r = httpx.post(f"{API_URL}/predict", json=payload, timeout=10.0)
                
            if r.status_code == 200:
                res = r.json()
                pred = res["prediction"]
                prob = res["probability"]
                threshold = res["threshold"]
                conf = res["confidence"]
                
                st.subheader("🎯 Résultat de la Prédiction")
                
                # Aesthetic Display
                if pred == "inactif":
                    st.error(f"⚠️ **RISQUE ÉLEVÉ D'ABANDON (INACTIF)**")
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <h4>Le modèle prédit que ce dépôt est <b>inactif / abandonné</b>.</h4>
                            <p><b>Probabilité d'inactivité :</b> <span style="font-size: 1.5rem; color: #ff4b4b; font-weight: bold;">{prob*100:.2f}%</span></p>
                            <p><b>Seuil décisionnel critique :</b> {threshold*100:.1f}%</p>
                            <p><b>Confiance :</b> {conf.upper()}</p>
                        </div>
                        """, unsafe_allow_html=True
                    )
                    st.warning(
                        "**Impact Sécurité (Métier)**: Les dépôts inactifs ont un risque plus élevé de contenir des vulnérabilités de dépendances non corrigées. "
                        "Il est recommandé de ne pas intégrer ce projet sans vérification préalable."
                    )
                else:
                    st.success(f"✅ **RISQUE FAIBLE (ACTIF)**")
                    st.markdown(
                        f"""
                        <div class="metric-card active">
                            <h4>Le modèle prédit que ce dépôt est <b>actif et maintenu</b>.</h4>
                            <p><b>Probabilité d'inactivité :</b> <span style="font-size: 1.5rem; color: #00e676; font-weight: bold;">{prob*100:.2f}%</span></p>
                            <p><b>Seuil décisionnel critique :</b> {threshold*100:.1f}%</p>
                            <p><b>Confiance :</b> {conf.upper()}</p>
                        </div>
                        """, unsafe_allow_html=True
                    )
            else:
                st.error(f"Erreur de l'API ({r.status_code}): {r.text}")
                
        except httpx.RequestError as e:
            st.error(f"Impossible de contacter l'API REST à {API_URL}. Assurez-vous que le service API est en ligne. Erreur: {e}")

# --- TAB 2: Batch Prediction ---
with tab2:
    st.subheader("Traitement de Lot (Batch Prediction)")
    st.write("Téléchargez un fichier CSV contenant une liste de dépôts pour obtenir des prédictions en masse.")
    
    st.markdown("""
    > 📥 **Format requis :** Le fichier CSV doit contenir les mêmes colonnes que celles du formulaire unitaire (`stars`, `forks`, `watchers`, `size_kb`, `repo_age_days`, `contributor_count`, `avg_issue_response_hours`, `engagement_rate`, `stars_forks_ratio`, `language`, `license`, `has_description`, `has_homepage`, `has_wiki`, `has_projects`, `is_fork`).
    """)
    
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Quick preview
            df_preview = pd.read_csv(uploaded_file)
            st.markdown(f"**Aperçu du fichier chargé ({len(df_preview)} lignes) :**")
            st.dataframe(df_preview.head(5))
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            process_btn = st.button("🚀 Lancer les prédictions par lot")
            
            if process_btn:
                files = {"file": (uploaded_file.name, uploaded_file.read(), "text/csv")}
                
                with st.spinner("L'API traite le fichier..."):
                    r = httpx.post(f"{API_URL}/predict/batch", files=files, timeout=60.0)
                    
                if r.status_code == 200:
                    df_out = pd.read_csv(io.StringIO(r.text))
                    st.success("Traitement par lot terminé avec succès !")
                    
                    # Display results stats
                    total = len(df_out)
                    inactifs = (df_out['prediction'] == 'inactif').sum()
                    actifs = total - inactifs
                    
                    st.subheader("📊 Résumé du Lot")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Nombre total de dépôts", total)
                    c2.metric("Prédits ACTIFS", actifs, f"{actifs/total*100:.1f}%", delta_color="normal")
                    c3.metric("Prédits INACTIFS (Alerte)", inactifs, f"-{inactifs/total*100:.1f}%", delta_color="inverse")
                    
                    # Graph representation
                    chart_data = pd.DataFrame({
                        'Status': ['Actif', 'Inactif (Abandonné)'],
                        'Quantité': [actifs, inactifs]
                    })
                    st.bar_chart(chart_data.set_index('Status'))
                    
                    # Preview predicted dataset
                    st.write("**Aperçu des résultats enrichis :**")
                    st.dataframe(df_out[['stars', 'language', 'probability_inactive', 'prediction', 'confidence']].head(10))
                    
                    # Download link
                    csv_data = df_out.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Télécharger le fichier CSV complet avec prédictions",
                        data=csv_data,
                        file_name=f"predicted_{uploaded_file.name}",
                        mime="text/csv"
                    )
                else:
                    st.error(f"Erreur API ({r.status_code}) : {r.text}")
                    
        except Exception as e:
            st.error(f"Erreur lors du traitement du fichier : {e}")

# --- TAB 3: Model and Business Context ---
with tab3:
    st.subheader("Informations sur le Modèle et le Contexte Métier")
    
    st.markdown("""
    ### 🛡️ Le problème métier : Inactivité des dépôts et risques de sécurité
    Les projets open-source abandonnés posent des risques de sécurité majeurs. Les dépendances obsolètes peuvent contenir des vulnérabilités non corrigées, 
    et l'absence de maintenance rend l'intégration de ces bibliothèques risquée pour les entreprises.
    
    ### ⚖️ Matrice de Coût Asymétrique (CRISP-DM Phase 1)
    Le coût des erreurs de classification est fortement asymétrique :
    *   **Faux Négatif (FN)** : Un dépôt abandonné est classé comme actif. Le système ne lève aucune alerte, l'entreprise l'utilise, entraînant une faille de sécurité. **Coût estimé : 10 000 €**.
    *   **Faux Positif (FP)** : Un dépôt actif est classé comme inactif. Le système lève une alerte, forçant une analyse manuelle de sécurité qui s'avère inutile. **Coût estimé : 60 € (temps de travail)**.
    
    ### 📈 Optimisation du Seuil Décisionnel (Threshold)
    En raison de ce déséquilibre de coût (un FN coûte 166 fois plus qu'un FP), le seuil par défaut de **0.50** n'est pas optimal.
    Le modèle de Gradient Boosting applique un **seuil optimal de 0.05** (déterminé lors de la Phase 3).
    
    Cela signifie que si le modèle estime à **plus de 5%** le risque que le projet soit inactif, il est marqué comme `inactif` pour forcer un audit de sécurité.
    """)
    
    # Query API metadata for performance metrics
    try:
        r_info = httpx.get(f"{API_URL}/model/info", timeout=5.0)
        if r_info.status_code == 200:
            info = r_info.json()
            st.markdown(f"### ⚙️ Métadonnées de performance (issues de l'API)")
            
            st.json(info)
        else:
            st.warning("Impossible de charger les métadonnées de l'API pour le moment.")
    except Exception:
        st.warning("API injoignable pour charger les statistiques de performance du modèle.")
