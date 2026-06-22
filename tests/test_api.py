"""
tests/test_api.py  —  FA23-BAI-030
4 required test functions (exact names verified by grading script).
"""

import os
import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")


def test_health_endpoint():
    """GET /health → HTTP 200; 'status':'healthy' and key 'model_version' present."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_version" in data


def test_predict_returns_label_and_confidence():
    """POST /predict → HTTP 200; label in [POSITIVE,NEGATIVE]; 0<=confidence<=1; 'model_version' present."""
    payload = {
        "text": "This app is incredibly intuitive and has made my daily workflow dramatically more efficient"
    }
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data["confidence"] <= 1
    assert "model_version" in data


def test_predict_negative_text():
    """POST /predict with negative text → HTTP 200."""
    payload = {"text": "This is terrible, awful, and I absolutely hate it"}
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 200


def test_health_returns_model_version_unstable():
    """GET /health → model_version == 'unstable-v1' exactly."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "unstable-v1"
