"""
헬스체크 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """기본 헬스체크 테스트"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "app_name" in data
    assert "version" in data


def test_detailed_health_check():
    """상세 헬스체크 테스트"""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "server" in data
    assert "features" in data
    assert data["server"]["host"] == "0.0.0.0"
    assert data["server"]["port"] == 8000


def test_readiness_check():
    """준비 상태 확인 테스트"""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"
