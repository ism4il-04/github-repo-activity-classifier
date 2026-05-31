import pytest
from fastapi.testclient import TestClient
from app.api import app, load_assets

# Force loading assets (model + metadata) before running tests
try:
    load_assets()
except Exception as e:
    print(f"Skipping startup load (assets might not be generated in exact test path): {e}")

client = TestClient(app)

def test_read_root():
    """Test root welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs_url" in data

def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True

def test_model_info():
    """Test model info endpoint."""
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "optimal_threshold" in data
    assert data["optimal_threshold"] == 0.05
    assert "model_name" in data

def test_predict_active():
    """Test prediction for an active repository."""
    payload = {
        "stars": 15,
        "forks": 5,
        "open_issues": 1,
        "watchers": 15,
        "size_kb": 2048.0,
        "repo_age_days": 100,
        "contributor_count": 5,
        "avg_issue_response_hours": 12.0,
        "engagement_rate": 0.2,
        "stars_forks_ratio": 3.0,
        "language": "Python",
        "license": "MIT License",
        "has_description": True,
        "has_homepage": True,
        "has_wiki": True,
        "has_projects": True,
        "is_fork": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "probability" in data
    assert data["prediction"] == "actif"
    assert "confidence" in data
    assert data["threshold"] == 0.05

def test_predict_inactive():
    """Test prediction for a clearly inactive repository."""
    payload = {
        "stars": 4,
        "forks": 0,
        "open_issues": 0,
        "watchers": 4,
        "size_kb": 10.0,
        "repo_age_days": 3000,
        "contributor_count": 1,
        "avg_issue_response_hours": -1.0,
        "engagement_rate": 0.0,
        "stars_forks_ratio": 4.0,
        "language": "Python",
        "license": "MIT License",
        "has_description": False,
        "has_homepage": False,
        "has_wiki": False,
        "has_projects": False,
        "is_fork": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert data["prediction"] == "inactif"
    assert data["probability"] >= 0.05
    assert "confidence" in data

def test_predict_validation():
    """Test validation errors for invalid input payloads."""
    # repo_age_days is less than 30 (which violates ge=30 validation)
    payload = {
        "stars": 10,
        "forks": 2,
        "open_issues": 1,
        "watchers": 10,
        "size_kb": 100.0,
        "repo_age_days": 15,  # Invalid age
        "contributor_count": 2,
        "avg_issue_response_hours": 1.0,
        "engagement_rate": 0.1,
        "stars_forks_ratio": 5.0,
        "language": "Python",
        "license": "MIT License",
        "has_description": True,
        "has_homepage": True,
        "has_wiki": True,
        "has_projects": True,
        "is_fork": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
