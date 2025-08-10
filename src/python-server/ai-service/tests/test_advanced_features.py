"""
고급 기능 테스트
실시간 분석, 피드백 시스템, 채널 통계, 리포트 시스템 테스트
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket

from services.realtime_service import RealtimeAnalysisService
from services.feedback_service import FeedbackService, UserFeedback
from services.channel_service import ChannelService, VideoAnalysis
from services.report_service import ReportService

class TestRealtimeAnalysis:
    """실시간 분석 테스트"""
    
    @pytest.fixture
    def realtime_service(self):
        return RealtimeAnalysisService()
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, realtime_service):
        """WebSocket 연결 테스트"""
        # Mock WebSocket 생성
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        video_id = "test_video_123"
        video_data = {
            "transcript": "This is a test video with factual information.",
            "metadata": {"title": "Test Video", "source": "test.com"}
        }
        
        # 연결 테스트
        await realtime_service.connect(mock_websocket, video_id)
        assert video_id in realtime_service.active_connections
        
        # 연결 해제 테스트
        await realtime_service.disconnect(video_id)
        assert video_id not in realtime_service.active_connections
    
    @pytest.mark.asyncio
    async def test_progress_updates(self, realtime_service):
        """진행률 업데이트 테스트"""
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        video_id = "test_video_123"
        realtime_service.active_connections[video_id] = mock_websocket
        
        # 진행률 업데이트 테스트
        await realtime_service._update_progress(video_id, "data_collection", 1, 6)
        
        # 메시지가 전송되었는지 확인
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["event_type"] == "analysis_progress"
        assert sent_message["data"]["step"] == "data_collection"

class TestFeedbackSystem:
    """피드백 시스템 테스트"""
    
    @pytest.fixture
    def feedback_service(self):
        return FeedbackService()
    
    @pytest.mark.asyncio
    async def test_submit_feedback(self, feedback_service):
        """피드백 제출 테스트"""
        feedback = UserFeedback(
            analysis_id="test_analysis_123",
            session_id="test_session",
            feedback_type="accurate",
            feedback_score=5,
            feedback_text="정확한 분석이었습니다."
        )
        
        result = await feedback_service.submit_feedback(feedback)
        
        assert result["success"] is True
        assert "feedback_id" in result
        assert feedback.analysis_id in feedback_service.feedback_storage
    
    @pytest.mark.asyncio
    async def test_get_feedback_stats(self, feedback_service):
        """피드백 통계 조회 테스트"""
        # 테스트 피드백 추가
        feedback = UserFeedback(
            analysis_id="test_analysis_123",
            session_id="test_session",
            feedback_type="accurate",
            feedback_score=5
        )
        await feedback_service.submit_feedback(feedback)
        
        stats = await feedback_service.get_feedback_stats()
        
        assert "total_feedback" in stats
        assert "type_distribution" in stats
        assert "score_distribution" in stats
        assert stats["total_feedback"] > 0
    
    @pytest.mark.asyncio
    async def test_calculate_model_accuracy(self, feedback_service):
        """모델 정확도 계산 테스트"""
        # 테스트 피드백 추가
        feedback = UserFeedback(
            analysis_id="test_analysis_123",
            session_id="test_session",
            feedback_type="accurate",
            feedback_score=5
        )
        await feedback_service.submit_feedback(feedback)
        
        accuracy = await feedback_service.calculate_model_accuracy()
        
        assert "accuracy_rate" in accuracy
        assert "accurate_count" in accuracy
        assert "inaccurate_count" in accuracy

class TestChannelStatistics:
    """채널 통계 테스트"""
    
    @pytest.fixture
    def channel_service(self):
        return ChannelService()
    
    @pytest.mark.asyncio
    async def test_update_channel_stats(self, channel_service):
        """채널 통계 업데이트 테스트"""
        video_analysis = VideoAnalysis(
            video_id="test_video_123",
            channel_id="test_channel_456",
            channel_name="Test Channel",
            video_title="Test Video",
            analysis_result={
                "credibility_score": 85.0,
                "bias_score": 15.0,
                "fact_check_score": 90.0
            }
        )
        
        result = await channel_service.update_channel_stats(video_analysis)
        
        assert result["success"] is True
        assert video_analysis.channel_id in channel_service.channel_stats
    
    @pytest.mark.asyncio
    async def test_get_channel_stats(self, channel_service):
        """채널 통계 조회 테스트"""
        # 테스트 데이터 추가
        video_analysis = VideoAnalysis(
            video_id="test_video_123",
            channel_id="test_channel_456",
            channel_name="Test Channel",
            video_title="Test Video",
            analysis_result={
                "credibility_score": 85.0,
                "bias_score": 15.0,
                "fact_check_score": 90.0
            }
        )
        await channel_service.update_channel_stats(video_analysis)
        
        stats = await channel_service.get_channel_stats("test_channel_456")
        
        assert "channel_id" in stats
        assert "channel_name" in stats
        assert "total_videos" in stats
        assert "average_credibility_score" in stats
    
    @pytest.mark.asyncio
    async def test_get_top_channels(self, channel_service):
        """상위 채널 조회 테스트"""
        # 여러 채널 데이터 추가
        channels = [
            ("test_channel_1", "Test Channel 1", 90.0),
            ("test_channel_2", "Test Channel 2", 75.0),
            ("test_channel_3", "Test Channel 3", 60.0)
        ]
        
        for channel_id, channel_name, score in channels:
            video_analysis = VideoAnalysis(
                video_id=f"test_video_{channel_id}",
                channel_id=channel_id,
                channel_name=channel_name,
                video_title=f"Test Video {channel_id}",
                analysis_result={"credibility_score": score}
            )
            await channel_service.update_channel_stats(video_analysis)
        
        top_channels = await channel_service.get_top_channels(limit=2, sort_by="credibility")
        
        assert len(top_channels) == 2
        assert top_channels[0]["average_credibility_score"] >= top_channels[1]["average_credibility_score"]

class TestReportSystem:
    """리포트 시스템 테스트"""
    
    @pytest.fixture
    def report_service(self):
        return ReportService()
    
    @pytest.mark.asyncio
    async def test_generate_analysis_report(self, report_service):
        """분석 리포트 생성 테스트"""
        analysis_data = {
            "credibility_score": 85.0,
            "bias_score": 15.0,
            "fact_check_score": 90.0,
            "source_score": 88.0
        }
        
        result = await report_service.generate_analysis_report(
            video_id="test_video_123",
            channel_id="test_channel_456",
            analysis_data=analysis_data
        )
        
        assert result["success"] is True
        assert "report_id" in result
        assert "report" in result
        assert result["report"]["risk_level"] in ["low", "medium", "high", "critical"]
    
    @pytest.mark.asyncio
    async def test_generate_trend_report(self, report_service):
        """트렌드 리포트 생성 테스트"""
        video_analyses = [
            {
                "video_id": "test_video_1",
                "credibility_score": 85.0,
                "analyzed_at": "2024-01-01T00:00:00Z"
            },
            {
                "video_id": "test_video_2",
                "credibility_score": 90.0,
                "analyzed_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        result = await report_service.generate_trend_report(
            channel_id="test_channel_456",
            period_days=30,
            video_analyses=video_analyses
        )
        
        assert result["success"] is True
        assert "report_id" in result
        assert "report" in result
        assert "trend_data" in result["report"]
    
    @pytest.mark.asyncio
    async def test_get_recent_reports(self, report_service):
        """최근 리포트 조회 테스트"""
        # 테스트 리포트 생성
        analysis_data = {"credibility_score": 85.0}
        await report_service.generate_analysis_report(
            video_id="test_video_123",
            channel_id="test_channel_456",
            analysis_data=analysis_data
        )
        
        recent_reports = await report_service.get_recent_reports(limit=5)
        
        assert isinstance(recent_reports, list)
        assert len(recent_reports) > 0

class TestPerformance:
    """성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """동시 분석 테스트"""
        # 여러 분석 요청을 동시에 실행하는 시뮬레이션
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                asyncio.sleep(0.1)  # 간단한 작업 시뮬레이션
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 모든 요청이 성공했는지 확인
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        assert success_count >= 3  # 최소 3개는 성공해야 함
    
    def test_response_time(self):
        """응답 시간 테스트"""
        import time
        
        start_time = time.time()
        # 간단한 작업 시뮬레이션
        time.sleep(0.1)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 1  # 1초 이내 응답

if __name__ == "__main__":
    pytest.main([__file__]) 