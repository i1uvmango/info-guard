"""
Info-Guard AI Service API 테스트
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from main import app

client = TestClient(app)

class TestAPIEndpoints:
    """API 엔드포인트 테스트"""
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Info-Guard AI Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime" in data
        assert "models_loaded" in data
    
    def test_metrics_endpoint(self):
        """메트릭 엔드포인트 테스트"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "models_loaded" in data
        assert "uptime" in data

class TestAnalysisEndpoints:
    """분석 엔드포인트 테스트"""
    
    @patch('main.models_loaded', True)
    @patch('main.analysis_service')
    @patch('main.youtube_service')
    def test_analyze_video_success(self, mock_youtube_service, mock_analysis_service):
        """비디오 분석 성공 테스트"""
        # Mock 설정
        mock_analysis_service.analyze_video.return_value = {
            "credibility_score": 85.5,
            "credibility_grade": "A",
            "analysis_breakdown": {
                "sentiment": 45.3,
                "bias": 15.2,
                "fact_check": 92.1,
                "source": 88.7
            },
            "explanation": "이 영상은 높은 신뢰도를 보입니다.",
            "confidence": 87.2
        }
        
        mock_youtube_service.extract_video_id.return_value = "test123"
        mock_youtube_service.get_video_data.return_value = {
            "video_id": "test123",
            "transcript": "테스트 자막",
            "metadata": {"title": "테스트 영상"}
        }
        
        # 요청 데이터
        request_data = {
            "video_url": "https://www.youtube.com/watch?v=test123"
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert "processing_time" in data
        assert "timestamp" in data
    
    @patch('main.models_loaded', False)
    def test_analyze_video_models_not_loaded(self):
        """모델이 로드되지 않은 경우 테스트"""
        request_data = {
            "video_url": "https://www.youtube.com/watch?v=test123"
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 503
        assert "AI 모델이 로드되지 않았습니다" in response.json()["detail"]
    
    @patch('main.models_loaded', True)
    @patch('main.analysis_service')
    def test_analyze_video_with_transcript(self, mock_analysis_service):
        """자막이 직접 제공된 경우 테스트"""
        mock_analysis_service.analyze_video.return_value = {
            "credibility_score": 75.0,
            "credibility_grade": "B",
            "analysis_breakdown": {
                "sentiment": 50.0,
                "bias": 25.0,
                "fact_check": 80.0,
                "source": 70.0
            },
            "explanation": "보통 수준의 신뢰도입니다.",
            "confidence": 75.0
        }
        
        request_data = {
            "transcript": "이것은 테스트 자막입니다.",
            "metadata": {"title": "테스트 영상"}
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
    
    @patch('main.models_loaded', True)
    @patch('main.analysis_service')
    def test_batch_analyze_videos(self, mock_analysis_service):
        """배치 분석 테스트"""
        mock_analysis_service.analyze_video.return_value = {
            "credibility_score": 80.0,
            "credibility_grade": "B",
            "analysis_breakdown": {
                "sentiment": 45.0,
                "bias": 20.0,
                "fact_check": 85.0,
                "source": 75.0
            },
            "explanation": "배치 분석 테스트",
            "confidence": 80.0
        }
        
        request_data = [
            {"video_url": "https://www.youtube.com/watch?v=test1"},
            {"video_url": "https://www.youtube.com/watch?v=test2"},
            {"transcript": "테스트 자막 3"}
        ]
        
        response = client.post("/batch-analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["total_requests"] == 3
        assert "results" in data

class TestErrorHandling:
    """에러 핸들링 테스트"""
    
    @patch('main.models_loaded', True)
    @patch('main.analysis_service')
    def test_analysis_service_error(self, mock_analysis_service):
        """분석 서비스 에러 테스트"""
        mock_analysis_service.analyze_video.side_effect = Exception("분석 실패")
        
        request_data = {
            "video_url": "https://www.youtube.com/watch?v=test123"
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 500
        assert "분석 중 오류가 발생했습니다" in response.json()["detail"]
    
    def test_invalid_request_data(self):
        """잘못된 요청 데이터 테스트"""
        request_data = {
            "invalid_field": "invalid_value"
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__]) 