import os
import json
import logging
import io
import joblib
import pandas as pd
import numpy as np
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(
    title="GitHub Repository Activity Classifier API",
    description="REST API for predicting GitHub repository inactivity using a trained Gradient Boosting model.",
    version="1.0.0"
)

# Constants & Paths
MODEL_PATH = os.getenv("MODEL_PATH", "models/final_model.joblib")
METADATA_PATH = os.getenv("METADATA_PATH", "models/final_model_metadata.json")

# Categories from training data to map out-of-vocabulary inputs to 'Other'
ALLOWED_LANGUAGES = {'Java', 'PHP', 'JavaScript', 'Python', 'C++', 'Ruby', 'Rust', 'Go', 'TypeScript', 'C', 'Other'}
ALLOWED_LICENSES = {
    'Other', 'MIT License', 'GNU General Public License v3.0', 'Apache License 2.0', 
    'GNU Affero General Public License v3.0', 'BSD 3-Clause "New" or "Revised" License', 
    'Mozilla Public License 2.0', 'GNU General Public License v2.0'
}

# Global assets
model = None
metadata = {}
optimal_threshold = 0.5

def categorize_age(days: int) -> str:
    """Bin repo age in days into business-defined maturity categories."""
    if days < 180:
        return 'nouveau'
    elif days < 730:
        return 'jeune'
    elif days < 1825:
        return 'mature'
    else:
        return 'ancien'

@app.on_event("startup")
def load_assets():
    """Load model and metadata at startup once."""
    global model, metadata, optimal_threshold
    logger.info("Loading model assets...")
    if not os.path.exists(MODEL_PATH):
        logger.error(f"Model file not found at: {MODEL_PATH}")
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    if not os.path.exists(METADATA_PATH):
        logger.error(f"Metadata file not found at: {METADATA_PATH}")
        raise FileNotFoundError(f"Metadata file not found at {METADATA_PATH}")
        
    try:
        model = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully.")
        with open(METADATA_PATH, "r") as f:
            metadata = json.load(f)
        optimal_threshold = metadata.get("optimal_threshold", 0.05)
        logger.info(f"Metadata loaded. Decision threshold set to {optimal_threshold}")
    except Exception as e:
        logger.error(f"Error loading assets: {e}")
        raise e

# --- Pydantic Schemas ---

class RepoInput(BaseModel):
    stars: int = Field(..., ge=0, description="Nombre d'étoiles (stargazers)", json_schema_extra={"example": 5})
    forks: int = Field(..., ge=0, description="Nombre de forks", json_schema_extra={"example": 2})
    open_issues: int = Field(..., ge=0, description="Nombre d'issues ouvertes", json_schema_extra={"example": 1})
    watchers: int = Field(..., ge=0, description="Nombre d'abonnés (watchers)", json_schema_extra={"example": 5})
    size_kb: float = Field(..., ge=0, description="Taille du dépôt en KB", json_schema_extra={"example": 1024.0})
    repo_age_days: int = Field(..., ge=30, description="Âge du dépôt en jours (minimum 30)", json_schema_extra={"example": 500})
    contributor_count: int = Field(..., ge=-1, description="Nombre de contributeurs (-1 si inconnu)", json_schema_extra={"example": 3})
    avg_issue_response_hours: Optional[float] = Field(None, description="Délai moyen de réponse aux issues en heures (-1.0 ou None si absent)", json_schema_extra={"example": 24.0})
    engagement_rate: float = Field(..., ge=0.0, description="Taux d'engagement: (stars + forks) / repo_age_days", json_schema_extra={"example": 0.014})
    stars_forks_ratio: float = Field(..., ge=0.0, description="Rapport stars/forks", json_schema_extra={"example": 2.5})
    language: str = Field(..., description="Langage principal du dépôt", json_schema_extra={"example": "Python"})
    license: str = Field(..., description="Licence du dépôt", json_schema_extra={"example": "MIT License"})
    has_description: bool = Field(..., description="Présence d'une description (True/False)", json_schema_extra={"example": True})
    has_homepage: bool = Field(..., description="Présence d'un site web (True/False)", json_schema_extra={"example": False})
    has_wiki: bool = Field(..., description="Wiki activé (True/False)", json_schema_extra={"example": True})
    has_projects: bool = Field(..., description="Projets activés (True/False)", json_schema_extra={"example": False})
    is_fork: bool = Field(..., description="Le dépôt est-il un fork (True/False)", json_schema_extra={"example": False})

class PredictResponse(BaseModel):
    prediction: str = Field(..., description="Classe prédite : 'actif' ou 'inactif'")
    probability: float = Field(..., description="Probabilité d'inactivité (classe 1)")
    threshold: float = Field(..., description="Seuil d'inactivité optimal appliqué")
    confidence: str = Field(..., description="Niveau de confiance : 'high', 'medium', 'low'")

# --- Helper logic for features & confidence ---

def preprocess_single(item: RepoInput) -> pd.DataFrame:
    """Preprocess a single RepoInput item and return a DataFrame ready for the model."""
    # Build a raw dict matching columns expected before the ColumnTransformer
    raw_dict = {
        "stars": item.stars,
        "forks": item.forks,
        "open_issues": item.open_issues,
        "watchers": item.watchers,
        "size_kb": item.size_kb,
        "repo_age_days": item.repo_age_days,
        "contributor_count": item.contributor_count,
        "avg_issue_response_hours": item.avg_issue_response_hours if item.avg_issue_response_hours is not None else np.nan,
        "engagement_rate": item.engagement_rate,
        "stars_forks_ratio": item.stars_forks_ratio,
        "language": item.language if item.language in ALLOWED_LANGUAGES else "Other",
        "license": item.license if item.license in ALLOWED_LICENSES else "Other",
        "has_description": int(item.has_description),
        "has_homepage": int(item.has_homepage),
        "has_wiki": int(item.has_wiki),
        "has_projects": int(item.has_projects),
        "is_fork": int(item.is_fork)
    }
    
    # Map -1.0 sentinel to NaN
    if raw_dict["avg_issue_response_hours"] == -1.0:
        raw_dict["avg_issue_response_hours"] = np.nan
        
    # Feature Engineering
    raw_dict["activity_score"] = raw_dict["stars"] + raw_dict["forks"] + raw_dict["watchers"]
    raw_dict["issues_per_contributor"] = raw_dict["open_issues"] / (raw_dict["contributor_count"] + 1)
    raw_dict["age_category"] = categorize_age(raw_dict["repo_age_days"])
    
    return pd.DataFrame([raw_dict])

def get_confidence_level(prob: float, threshold: float) -> str:
    """Determine confidence level based on distance from the threshold."""
    if prob >= threshold:
        # Inactif
        if prob > threshold + 0.25 or prob > 0.8:
            return "high"
        elif prob > threshold + 0.10:
            return "medium"
        else:
            return "low"
    else:
        # Actif
        if prob < threshold - 0.03 or prob < 0.01:
            return "high"
        elif prob < threshold - 0.01:
            return "medium"
        else:
            return "low"

# --- Endpoints ---

@app.get("/", tags=["General"])
def read_root():
    """Welcome page with description and link to docs."""
    return {
        "message": "Welcome to the GitHub Repository Activity Classifier API",
        "description": "API REST de classification de l'activité des dépôts GitHub. Prédit si un dépôt est actif ou inactif (abandonné).",
        "model_info": f"/model/info",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint to verify that the model is loaded and API is ready."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded and ready."
        )
    return {"status": "ok", "model_loaded": True}

@app.get("/model/info", tags=["Model"])
def model_info():
    """Retrieve metadata about the loaded classification model."""
    if model is None or not metadata:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model assets are not initialized."
        )
    return {
        "model_name": metadata.get("model_name", "GradientBoostingClassifier"),
        "strategy_imbalance": metadata.get("strategy", "class_weight"),
        "optimal_threshold": optimal_threshold,
        "default_threshold": metadata.get("default_threshold", 0.5),
        "test_metrics": {
            "default_threshold_metrics": metadata.get("test_metrics_default"),
            "optimal_threshold_metrics": metadata.get("test_metrics_optimal"),
        },
        "business_costs": metadata.get("cost_matrix")
    }

@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict_single(item: RepoInput):
    """Predict the activity status of a single GitHub repository using raw inputs."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded."
        )
    
    try:
        df_input = preprocess_single(item)
        logger.info(f"Predicting repository activity. Input columns: {df_input.columns.tolist()}")
        
        # Predict probability
        prob = float(model.predict_proba(df_input)[0, 1])
        prediction = "inactif" if prob >= optimal_threshold else "actif"
        confidence = get_confidence_level(prob, optimal_threshold)
        
        logger.info(f"Prediction: {prediction} (p={prob:.4f}, threshold={optimal_threshold}, confidence={confidence})")
        return PredictResponse(
            prediction=prediction,
            probability=prob,
            threshold=optimal_threshold,
            confidence=confidence
        )
    except Exception as e:
        logger.exception("Prediction failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during prediction: {str(e)}"
        )

@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(file: UploadFile = File(...)):
    """
    Perform batch predictions on an uploaded CSV file.
    Expects a CSV with identical columns as RepoInput, returns the CSV enriched with predictions.
    """
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded."
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported."
        )
        
    try:
        contents = await file.read()
        df_raw = pd.read_csv(io.BytesIO(contents))
        logger.info(f"Received batch file {file.filename} with {len(df_raw)} rows.")
        
        # Required raw columns to validate
        required_cols = [
            'stars', 'forks', 'open_issues', 'watchers', 'size_kb', 
            'repo_age_days', 'contributor_count', 'avg_issue_response_hours', 
            'engagement_rate', 'stars_forks_ratio', 'language', 'license', 
            'has_description', 'has_homepage', 'has_wiki', 'has_projects', 'is_fork'
        ]
        
        missing = [col for col in required_cols if col not in df_raw.columns]
        if missing:
            logger.warning(f"Batch file is missing required columns: {missing}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV file is missing required columns: {missing}"
            )
            
        # Make a copy for processing
        df_processed = df_raw.copy()
        
        # 1. Clean sentinel avg_issue_response_hours
        df_processed['avg_issue_response_hours'] = df_processed['avg_issue_response_hours'].replace(-1.0, np.nan)
        
        # 2. Map Categorical OOV values
        df_processed['language'] = df_processed['language'].apply(lambda x: x if x in ALLOWED_LANGUAGES else 'Other')
        df_processed['license'] = df_processed['license'].apply(lambda x: x if x in ALLOWED_LICENSES else 'Other')
        
        # 3. Cast binary boolean cols to int
        binary_cols = ['has_description', 'has_homepage', 'has_wiki', 'has_projects', 'is_fork']
        for col in binary_cols:
            df_processed[col] = df_processed[col].astype(int)
            
        # 4. Feature Engineering
        df_processed['activity_score'] = df_processed['stars'] + df_processed['forks'] + df_processed['watchers']
        df_processed['issues_per_contributor'] = df_processed['open_issues'] / (df_processed['contributor_count'] + 1)
        df_processed['age_category'] = df_processed['repo_age_days'].apply(categorize_age)
        
        # 5. Model execution
        probs = model.predict_proba(df_processed)[:, 1]
        
        # 6. Add enrichment columns to the original raw DataFrame
        df_raw['probability_inactive'] = np.round(probs, 4)
        df_raw['prediction'] = ["inactif" if p >= optimal_threshold else "actif" for p in probs]
        df_raw['confidence'] = [get_confidence_level(p, optimal_threshold) for p in probs]
        df_raw['optimal_threshold'] = optimal_threshold
        
        # Output as streaming CSV
        stream = io.StringIO()
        df_raw.to_csv(stream, index=False)
        
        response = StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv"
        )
        filename = f"predicted_{file.filename}"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        logger.info(f"Batch prediction completed successfully for {len(df_raw)} records.")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch prediction failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )
