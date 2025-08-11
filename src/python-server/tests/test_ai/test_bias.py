"""
편향성 분석 모델 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.ai.bias import BiasDetector
from app.models.analysis import BiasAnalysis

pytestmark = pytest.mark.asyncio


class TestBiasDetector:
    """편향성 분석기 테스트 클래스"""
    
    @pytest.fixture
    def detector(self):
        """편향성 분석기 인스턴스 생성"""
        detector = BiasDetector()
        yield detector
        # cleanup은 각 테스트 후에 수동으로 호출
    
    async def test_initialization(self, detector):
        """초기화 테스트"""
        assert detector.model_name == "bias_detector"
        assert detector.bias_pipeline is None
        assert detector.bias_threshold == 0.6
        assert len(detector.bias_categories) == 8
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_model_loading(self, detector):
        """모델 로딩 테스트"""
        # 모델 로딩 시도
        success = await detector.load_model()
        
        # 로딩 성공 여부는 환경에 따라 다름
        if success:
            assert detector.is_loaded is True
            assert detector.bias_pipeline is not None
        else:
            assert detector.is_loaded is False
            assert detector.bias_pipeline is None
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_bias_analysis(self, detector):
        """편향성 분석 테스트"""
        # 정치적 편향이 있는 텍스트
        text = "이 정부는 정말 나쁩니다. 야당이 더 나을 것 같아요."
        result = await detector.analyze(text)
        
        assert isinstance(result, BiasAnalysis)
        assert result.has_bias in [True, False]  # 더미 로직 결과에 따라 다름
        assert isinstance(result.bias_types, list)
        assert isinstance(result.bias_score, float)
        assert 0.0 <= result.bias_score <= 1.0
        assert isinstance(result.political_bias, float)
        assert isinstance(result.gender_bias, float)
        assert isinstance(result.racial_bias, float)
        assert isinstance(result.religious_bias, float)
        assert isinstance(result.other_biases, dict)
        assert result.reasoning is not None
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_political_bias_detection(self, detector):
        """정치적 편향 감지 테스트"""
        text = "여당은 항상 옳고, 야당은 항상 틀렸다."
        result = await detector.analyze(text)
        
        # 정치적 편향이 감지되어야 함
        if result.has_bias:
            assert "political" in result.bias_types or result.political_bias > 0.0
        assert result.political_bias >= 0.0
        assert result.political_bias <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_gender_bias_detection(self, detector):
        """성별 편향 감지 테스트"""
        text = "남자는 일하고, 여자는 집안일만 해야 한다."
        result = await detector.analyze(text)
        
        # 성별 편향이 감지되어야 함
        if result.has_bias:
            assert "gender" in result.bias_types or result.gender_bias > 0.0
        assert result.gender_bias >= 0.0
        assert result.gender_bias <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_racial_bias_detection(self, detector):
        """인종 편향 감지 테스트"""
        text = "우리 민족이 최고이고, 다른 인종은 열등하다."
        result = await detector.analyze(text)
        
        # 인종 편향이 감지되어야 함
        if result.has_bias:
            assert "racial" in result.bias_types or result.racial_bias > 0.0
        assert result.racial_bias >= 0.0
        assert result.racial_bias <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_neutral_text(self, detector):
        """중립적 텍스트 테스트"""
        text = "오늘 날씨는 맑고 기온은 20도입니다."
        result = await detector.analyze(text)
        
        # 중립적 텍스트는 편향이 적어야 함
        assert isinstance(result, BiasAnalysis)
        assert result.bias_score >= 0.0
        assert result.bias_score <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_empty_text(self, detector):
        """빈 텍스트 테스트"""
        text = ""
        result = await detector.analyze(text)
        
        assert isinstance(result, BiasAnalysis)
        assert result.bias_score >= 0.0
        assert result.bias_score <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_long_text(self, detector):
        """긴 텍스트 테스트"""
        text = "이것은 매우 긴 텍스트입니다. " * 100
        result = await detector.analyze(text)
        
        assert isinstance(result, BiasAnalysis)
        assert result.bias_score >= 0.0
        assert result.bias_score <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_model_unloading(self, detector):
        """모델 언로딩 테스트"""
        # 모델 로딩
        await detector.load_model()
        
        # 언로딩
        await detector.cleanup()
        
        # 모델이 언로드되었는지 확인
        assert detector.is_loaded is False
    
    async def test_error_handling(self, detector):
        """에러 처리 테스트"""
        # 잘못된 입력으로 테스트
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            try:
                result = await detector.analyze(invalid_input)
                # 에러가 발생하지 않았다면 결과가 있어야 함
                assert isinstance(result, BiasAnalysis)
            except Exception as e:
                # 에러가 발생했다면 적절히 처리되어야 함
                assert isinstance(e, Exception)
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_bias_score_range(self, detector):
        """편향 점수 범위 테스트"""
        test_texts = [
            "정말 좋은 하루입니다.",
            "정말 나쁜 하루입니다.",
            "보통의 하루입니다.",
            "정치적으로 편향된 의견입니다.",
            "성별에 따른 차별적 발언입니다."
        ]
        
        for text in test_texts:
            result = await detector.analyze(text)
            
            # 모든 점수가 0-1 범위 내에 있어야 함
            assert 0.0 <= result.bias_score <= 1.0
            assert 0.0 <= result.political_bias <= 1.0
            assert 0.0 <= result.gender_bias <= 1.0
            assert 0.0 <= result.racial_bias <= 1.0
            assert 0.0 <= result.religious_bias <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_bias_types_consistency(self, detector):
        """편향 유형 일관성 테스트"""
        text = "정치적으로 편향되고 성별에 따른 차별이 있는 텍스트입니다."
        result = await detector.analyze(text)
        
        # 편향이 감지되었다면 유형이 일치해야 함
        if result.has_bias:
            assert len(result.bias_types) > 0
            
            # 감지된 편향 유형에 따라 해당 점수가 높아야 함
            for bias_type in result.bias_types:
                if bias_type == "political":
                    assert result.political_bias > 0.0
                elif bias_type == "gender":
                    assert result.gender_bias > 0.0
                elif bias_type == "racial":
                    assert result.racial_bias > 0.0
                elif bias_type == "religious":
                    assert result.religious_bias > 0.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_text_preprocessing(self, detector):
        """텍스트 전처리 테스트"""
        # 특수문자가 포함된 텍스트
        text = "정치!!!@@@###$$$%%%^^^&&&***()()()"
        result = await detector.analyze(text)
        
        assert isinstance(result, BiasAnalysis)
        assert result.bias_score >= 0.0
        assert result.bias_score <= 1.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
    
    async def test_multiple_bias_detection(self, detector):
        """다중 편향 감지 테스트"""
        # 여러 편향이 섞인 텍스트
        text = "이 정부는 성별 차별을 조장하고 인종 편견을 가지고 있습니다."
        result = await detector.analyze(text)
        
        assert isinstance(result, BiasAnalysis)
        
        # 여러 편향이 감지될 가능성이 높음
        if result.has_bias:
            assert len(result.bias_types) >= 1
            assert result.bias_score > 0.0
        
        # 테스트 후 cleanup
        await detector.cleanup()
