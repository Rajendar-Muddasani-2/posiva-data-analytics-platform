"""
Unit tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
import sys
sys.path.append('.')

from src.api.main import app

client = TestClient(app)

def test_health():
    """Test health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'version' in data

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'

def test_yield_analytics():
    """Test yield analytics endpoint"""
    response = client.get("/api/analytics/yield")
    assert response.status_code == 200
    data = response.json()
    assert 'overall_yield' in data
    assert 'total_devices' in data
    assert 'pass_count' in data

def test_prediction():
    """Test prediction endpoint"""
    payload = {
        "test_time": 2.5,
        "test_result": "CONT_TEST",
        "wafer_id": "W001",
        "lot_id": "L001"
    }
    response = client.post("/api/predict/yield", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'prediction' in data
    assert data['prediction'] in ['PASS', 'FAIL']
    assert 'confidence' in data

def test_invalid_prediction():
    """Test prediction with missing fields"""
    payload = {"test_time": 2.5}
    response = client.post("/api/predict/yield", json=payload)
    assert response.status_code == 422  # Validation error
