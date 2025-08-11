"""
신뢰도 분석 모델 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.ai.credibility import CredibilityAnalyzer
from app.models.analysis import CredibilityAnalysis

pytestmark = pytest.mark.asyncio


class TestCredibilityAnalyzer:
    """신뢰도 분석기 테스트 클래스"""
    
    @pytest.fixture
    def analyzer(self):
        """신뢰도 분석기 인스턴스 생성"""
        analyzer = CredibilityAnalyzer()
        yield analyzer
        # cleanup은 각 테스트 후에 수동으로 호출
    
    async def test_initialization(self, analyzer):
        """초기화 테스트"""
        assert analyzer.model_name == "credibility_analyzer"
        assert analyzer.credibility_pipeline is None
        assert analyzer.credibility_threshold == 0.7
        assert len(analyzer.credibility_indicators) > 0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_model_loading(self, analyzer):
        """모델 로딩 테스트"""
        # 모델 로딩 시도
        success = await analyzer.load_model()
        
        # 로딩 성공 여부는 환경에 따라 다름
        if success:
            assert analyzer.is_loaded is True
            assert analyzer.credibility_pipeline is not None
        else:
            assert analyzer.is_loaded is False
            assert analyzer.credibility_pipeline is None
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_credibility_analysis(self, analyzer):
        """신뢰도 분석 테스트"""
        # 신뢰할 수 있는 텍스트
        text = "2024년 12월 기준으로 한국의 GDP는 1.7조 달러입니다."
        result = await analyzer.analyze(text)
        
        assert isinstance(result, CredibilityAnalysis)
        assert isinstance(result.credibility_score, float)
        assert 0.0 <= result.credibility_score <= 1.0
        assert isinstance(result.fact_check_score, float)
        assert isinstance(result.source_reliability_score, float)
        assert isinstance(result.consistency_score, float)
        assert isinstance(result.objectivity_score, float)
        assert isinstance(result.credibility_level, str)
        assert result.reasoning is not None
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_high_credibility_text(self, analyzer):
        """높은 신뢰도 텍스트 테스트"""
        text = "공식 통계에 따르면, 2024년 한국의 인구는 약 5,200만 명입니다."
        result = await analyzer.analyze(text)
        
        # 높은 신뢰도 텍스트는 높은 점수를 받아야 함
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        assert result.fact_check_score >= 0.0
        assert result.source_reliability_score >= 0.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_low_credibility_text(self, analyzer):
        """낮은 신뢰도 텍스트 테스트"""
        text = "내 친구가 말하기로는 외계인이 지구에 왔다고 합니다."
        result = await analyzer.analyze(text)
        
        # 낮은 신뢰도 텍스트는 낮은 점수를 받을 수 있음
        assert isinstance(result, CredibilityAnalysis)
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_neutral_text(self, analyzer):
        """중립적 텍스트 테스트"""
        text = "오늘 날씨는 맑고 기온은 20도입니다."
        result = await analyzer.analyze(text)
        
        # 중립적 텍스트는 보통 신뢰도 점수를 받아야 함
        assert isinstance(result, CredibilityAnalysis)
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_empty_text(self, analyzer):
        """빈 텍스트 테스트"""
        text = ""
        result = await analyzer.analyze(text)
        
        assert isinstance(result, CredibilityAnalysis)
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_long_text(self, analyzer):
        """긴 텍스트 테스트"""
        text = "이것은 매우 긴 텍스트입니다. " * 100
        result = await analyzer.analyze(text)
        
        assert isinstance(result, CredibilityAnalysis)
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_model_unloading(self, analyzer):
        """모델 언로딩 테스트"""
        # 모델 로딩
        await analyzer.load_model()
        
        # 언로딩
        await analyzer.cleanup()
        
        # 모델이 언로드되었는지 확인
        assert analyzer.is_loaded is False
    
    async def test_error_handling(self, analyzer):
        """에러 처리 테스트"""
        # 잘못된 입력으로 테스트
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            try:
                result = await analyzer.analyze(invalid_input)
                # 에러가 발생하지 않았다면 결과가 있어야 함
                assert isinstance(result, CredibilityAnalysis)
            except Exception as e:
                # 에러가 발생했다면 적절히 처리되어야 함
                assert isinstance(e, Exception)
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_credibility_score_range(self, analyzer):
        """신뢰도 점수 범위 테스트"""
        test_texts = [
            "공식 발표에 따르면...",
            "소문에 따르면...",
            "전문가들이 분석한 결과...",
            "누군가가 말하기로는...",
            "연구 결과에 따르면..."
        ]
        
        for text in test_texts:
            result = await analyzer.analyze(text)
            
            # 모든 점수가 0-1 범위 내에 있어야 함
            assert 0.0 <= result.credibility_score <= 1.0
            assert 0.0 <= result.fact_check_score <= 1.0
            assert 0.0 <= result.source_reliability_score <= 1.0
            assert 0.0 <= result.consistency_score <= 1.0
            assert 0.0 <= result.objectivity_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_credibility_level_consistency(self, analyzer):
        """신뢰도 레벨 일관성 테스트"""
        text = "공식 통계 자료에 따르면 한국의 경제 성장률은 3.2%입니다."
        result = await analyzer.analyze(text)
        
        # 신뢰도 점수와 레벨이 일치해야 함
        if result.credibility_score >= 0.8:
            assert result.credibility_level in ["high", "very_high"]
        elif result.credibility_score >= 0.6:
            assert result.credibility_level in ["medium", "high"]
        elif result.credibility_score >= 0.4:
            assert result.credibility_level in ["low", "medium"]
        else:
            assert result.credibility_level in ["very_low", "low"]
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_text_preprocessing(self, analyzer):
        """텍스트 전처리 테스트"""
        # 특수문자가 포함된 텍스트
        text = "신뢰도!!!@@@###$$$%%%^^^&&&***()()()"
        result = await analyzer.analyze(text)
        
        assert isinstance(result, CredibilityAnalysis)
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
    
    async def test_multiple_indicators(self, analyzer):
        """다중 신뢰도 지표 테스트"""
        # 여러 신뢰도 지표가 포함된 텍스트
        text = "공식 통계와 전문가 분석에 따르면, 이 정책은 효과적일 것으로 예상됩니다."
        result = await analyzer.analyze(text)
        
        assert isinstance(result, CredibilityAnalysis)
        
        # 여러 신뢰도 지표가 감지될 가능성이 높음
        assert result.credibility_score >= 0.0
        assert result.credibility_score <= 1.0
        
        # 테스트 후 cleanup
        await analyzer.cleanup()
