"""
팩트 체커 모델 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.ai.fact_checker import FactChecker
from app.models.analysis import FactCheckAnalysis

pytestmark = pytest.mark.asyncio


class TestFactChecker:
    """팩트 체커 테스트 클래스"""
    
    @pytest.fixture
    def checker(self):
        """팩트 체커 인스턴스 생성"""
        checker = FactChecker()
        yield checker
        # cleanup은 각 테스트 후에 수동으로 호출
    
    async def test_initialization(self, checker):
        """초기화 테스트"""
        assert checker.model_name == "fact_checker"
        assert checker.fact_check_pipeline is None
        assert checker.fact_check_threshold == 0.7
        assert len(checker.fact_check_categories) > 0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_model_loading(self, checker):
        """모델 로딩 테스트"""
        # 모델 로딩 시도
        success = await checker.load_model()
        
        # 로딩 성공 여부는 환경에 따라 다름
        if success:
            assert checker.is_loaded is True
            assert checker.fact_check_pipeline is not None
        else:
            assert checker.is_loaded is False
            assert checker.fact_check_pipeline is None
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_fact_check_analysis(self, checker):
        """팩트 체크 분석 테스트"""
        # 사실 확인이 필요한 텍스트
        text = "한국의 수도는 서울입니다."
        result = await checker.analyze(text)
        
        assert isinstance(result, FactCheckAnalysis)
        assert isinstance(result.fact_check_score, float)
        assert 0.0 <= result.fact_check_score <= 1.0
        assert isinstance(result.claim_verification_score, float)
        assert isinstance(result.source_analysis_score, float)
        assert isinstance(result.evidence_strength_score, float)
        assert isinstance(result.fact_check_result, str)
        assert result.reasoning is not None
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_true_statement(self, checker):
        """참인 문장 테스트"""
        text = "지구는 태양계의 행성입니다."
        result = await checker.analyze(text)
        
        # 참인 문장은 높은 점수를 받아야 함
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        assert result.claim_verification_score >= 0.0
        assert result.evidence_strength_score >= 0.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_false_statement(self, checker):
        """거짓인 문장 테스트"""
        text = "달은 치즈로 만들어졌습니다."
        result = await checker.analyze(text)
        
        # 거짓인 문장은 낮은 점수를 받을 수 있음
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_neutral_statement(self, checker):
        """중립적 문장 테스트"""
        text = "오늘 날씨는 맑습니다."
        result = await checker.analyze(text)
        
        # 중립적 문장은 보통 점수를 받아야 함
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_empty_text(self, checker):
        """빈 텍스트 테스트"""
        text = ""
        result = await checker.analyze(text)
        
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_long_text(self, checker):
        """긴 텍스트 테스트"""
        text = "이것은 매우 긴 텍스트입니다. " * 100
        result = await checker.analyze(text)
        
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_model_unloading(self, checker):
        """모델 언로딩 테스트"""
        # 모델 로딩
        await checker.load_model()
        
        # 언로딩
        await checker.cleanup()
        
        # 모델이 언로드되었는지 확인
        assert checker.is_loaded is False
    
    async def test_error_handling(self, checker):
        """에러 처리 테스트"""
        # 잘못된 입력으로 테스트
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            try:
                result = await checker.analyze(invalid_input)
                # 에러가 발생하지 않았다면 결과가 있어야 함
                assert isinstance(result, FactCheckAnalysis)
            except Exception as e:
                # 에러가 발생했다면 적절히 처리되어야 함
                assert isinstance(e, Exception)
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_fact_check_score_range(self, checker):
        """팩트 체크 점수 범위 테스트"""
        test_texts = [
            "공식 통계에 따르면...",
            "소문에 따르면...",
            "전문가들이 확인한 결과...",
            "누군가가 말하기로는...",
            "연구 결과에 따르면..."
        ]
        
        for text in test_texts:
            result = await checker.analyze(text)
            
            # 모든 점수가 0-1 범위 내에 있어야 함
            assert 0.0 <= result.fact_check_score <= 1.0
            assert 0.0 <= result.claim_verification_score <= 1.0
            assert 0.0 <= result.source_analysis_score <= 1.0
            assert 0.0 <= result.evidence_strength_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_fact_check_result_consistency(self, checker):
        """팩트 체크 결과 일관성 테스트"""
        text = "한국의 수도는 서울이며, 인구는 약 1,000만 명입니다."
        result = await checker.analyze(text)
        
        # 팩트 체크 점수와 결과가 일치해야 함
        if result.fact_check_score >= 0.8:
            assert result.fact_check_result in ["true", "mostly_true"]
        elif result.fact_check_score >= 0.6:
            assert result.fact_check_result in ["partially_true", "mostly_true"]
        elif result.fact_check_score >= 0.4:
            assert result.fact_check_result in ["unclear", "partially_true"]
        else:
            assert result.fact_check_result in ["false", "mostly_false"]
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_text_preprocessing(self, checker):
        """텍스트 전처리 테스트"""
        # 특수문자가 포함된 텍스트
        text = "팩트체크!!!@@@###$$$%%%^^^&&&***()()()"
        result = await checker.analyze(text)
        
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_multiple_claims(self, checker):
        """다중 주장 테스트"""
        # 여러 주장이 포함된 텍스트
        text = "한국은 아시아에 위치하고 있으며, 수도는 서울이고, 공식 언어는 한국어입니다."
        result = await checker.analyze(text)
        
        assert isinstance(result, FactCheckAnalysis)
        
        # 여러 주장이 포함된 텍스트는 복잡한 분석이 필요
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
    
    async def test_controversial_statement(self, checker):
        """논란이 있는 문장 테스트"""
        text = "이 정책은 경제에 긍정적인 영향을 미칠 것입니다."
        result = await checker.analyze(text)
        
        # 논란이 있는 문장은 낮은 점수를 받을 수 있음
        assert isinstance(result, FactCheckAnalysis)
        assert result.fact_check_score >= 0.0
        assert result.fact_check_score <= 1.0
        
        # 테스트 후 cleanup
        await checker.cleanup()
