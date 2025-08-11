"""
감정 분석 모델 테스트
"""

import pytest
from app.ai.sentiment import SentimentAnalyzer


class TestSentimentAnalyzer:
    """감정 분석기 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """감정 분석기 인스턴스 생성"""
        return SentimentAnalyzer()
    
    def test_initialization(self, analyzer):
        """초기화 테스트"""
        assert analyzer.model_name == "sentiment_analyzer"
        assert analyzer.model_path == "klue/roberta-base"
        assert analyzer.is_loaded is False
    
    def test_model_loading(self, analyzer):
        """모델 로딩 테스트"""
        success = analyzer.load_model()
        assert success is True
        assert analyzer.is_loaded is True
    
    def test_sentiment_analysis(self, analyzer):
        """감정 분석 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        # 긍정적 텍스트 분석
        text = "오늘은 정말 좋은 날씨입니다. 기분이 너무 좋아요!"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert hasattr(result, 'overall_sentiment')
        assert hasattr(result, 'dominant_emotion')
        assert hasattr(result, 'emotion_breakdown')
        assert result.overall_sentiment > 0  # 긍정적
    
    def test_negative_sentiment(self, analyzer):
        """부정적 감정 분석 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        # 부정적 텍스트 분석
        text = "오늘은 정말 나쁜 날씨입니다. 기분이 너무 나빠요."
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.overall_sentiment < 0  # 부정적
        assert result.dominant_emotion in ["negative", "neutral"]
    
    def test_neutral_sentiment(self, analyzer):
        """중립적 감정 분석 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        # 중립적 텍스트 분석
        text = "오늘 날씨는 보통입니다. 특별한 일은 없었습니다."
        result = analyzer.analyze(text)
        
        assert result is not None
        assert abs(result.overall_sentiment) < 0.3  # 중립적
        assert result.dominant_emotion in ["neutral", "positive", "negative"]
    
    def test_empty_text(self, analyzer):
        """빈 텍스트 처리 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        # 빈 텍스트 분석
        result = analyzer.analyze("")
        
        assert result is not None
        # 빈 텍스트는 중립적이거나 에러 처리되어야 함
    
    def test_long_text(self, analyzer):
        """긴 텍스트 처리 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        # 긴 텍스트 생성
        long_text = "이것은 매우 긴 텍스트입니다. " * 100
        
        result = analyzer.analyze(long_text)
        
        assert result is not None
        assert hasattr(result, 'overall_sentiment')
    
    def test_model_unloading(self, analyzer):
        """모델 언로드 테스트"""
        # 모델 로드
        analyzer.load_model()
        assert analyzer.is_loaded is True
        
        # 모델 언로드
        analyzer.unload_model()
        assert analyzer.is_loaded is False
    
    def test_error_handling(self, analyzer):
        """에러 처리 테스트"""
        # 모델을 로드하지 않고 분석 시도
        result = analyzer.analyze("테스트 텍스트")
        
        # 에러가 발생하지 않고 더미 결과가 반환되어야 함
        assert result is not None
        assert hasattr(result, 'overall_sentiment')
    
    def test_emotion_breakdown(self, analyzer):
        """감정 세부 분석 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        text = "복잡한 감정을 가진 텍스트입니다."
        result = analyzer.analyze(text)
        
        assert result is not None
        assert hasattr(result, 'emotion_breakdown')
        assert isinstance(result.emotion_breakdown, dict)
    
    def test_sentiment_range(self, analyzer):
        """감정 점수 범위 테스트"""
        # 모델 로드
        analyzer.load_model()
        
        text = "테스트 텍스트"
        result = analyzer.analyze(text)
        
        assert result is not None
        # overall_sentiment는 -1에서 1 사이의 값이어야 함
        assert -1.0 <= result.overall_sentiment <= 1.0
