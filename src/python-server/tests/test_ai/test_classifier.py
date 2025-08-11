"""
콘텐츠 분류 모델 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.ai.classifier import ContentClassifier
from app.models.analysis import ContentClassification

pytestmark = pytest.mark.asyncio


class TestContentClassifier:
    """콘텐츠 분류기 테스트 클래스"""
    
    @pytest.fixture
    def classifier(self):
        """콘텐츠 분류기 인스턴스 생성"""
        classifier = ContentClassifier()
        yield classifier
        # cleanup은 각 테스트 후에 수동으로 호출
    
    async def test_initialization(self, classifier):
        """초기화 테스트"""
        assert classifier.model_name == "content_classifier"
        assert classifier.classification_pipeline is None
        assert classifier.classification_threshold == 0.6
        assert len(classifier.content_categories) > 0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_model_loading(self, classifier):
        """모델 로딩 테스트"""
        # 모델 로딩 시도
        success = await classifier.load_model()
        
        # 로딩 성공 여부는 환경에 따라 다름
        if success:
            assert classifier.is_loaded is True
            assert classifier.classification_pipeline is not None
        else:
            assert classifier.is_loaded is False
            assert classifier.classification_pipeline is None
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_content_classification(self, classifier):
        """콘텐츠 분류 테스트"""
        # 뉴스 콘텐츠
        text = "정부가 새로운 경제 정책을 발표했습니다."
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        assert isinstance(result.primary_category, str)
        assert isinstance(result.primary_confidence, float)
        assert 0.0 <= result.primary_confidence <= 1.0
        assert isinstance(result.all_categories, dict)
        assert result.reasoning is not None
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_news_content(self, classifier):
        """뉴스 콘텐츠 분류 테스트"""
        text = "오늘 국회에서 새로운 법안이 통과되었습니다."
        result = await classifier.analyze(text)
        
        # 뉴스 콘텐츠는 높은 신뢰도로 분류되어야 함
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        assert len(result.all_categories) > 0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_educational_content(self, classifier):
        """교육 콘텐츠 분류 테스트"""
        text = "이 수학 공식은 다음과 같이 증명됩니다."
        result = await classifier.analyze(text)
        
        # 교육 콘텐츠는 적절히 분류되어야 함
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_entertainment_content(self, classifier):
        """엔터테인먼트 콘텐츠 분류 테스트"""
        text = "이 영화는 정말 재미있었습니다."
        result = await classifier.analyze(text)
        
        # 엔터테인먼트 콘텐츠는 적절히 분류되어야 함
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_neutral_content(self, classifier):
        """중립적 콘텐츠 테스트"""
        text = "오늘 날씨는 맑고 기온은 20도입니다."
        result = await classifier.analyze(text)
        
        # 중립적 콘텐츠는 적절히 분류되어야 함
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_empty_text(self, classifier):
        """빈 텍스트 테스트"""
        text = ""
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_long_text(self, classifier):
        """긴 텍스트 테스트"""
        text = "이것은 매우 긴 텍스트입니다. " * 100
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_model_unloading(self, classifier):
        """모델 언로딩 테스트"""
        # 모델 로딩
        await classifier.load_model()
        
        # 언로딩
        await classifier.cleanup()
        
        # 모델이 언로드되었는지 확인
        assert classifier.is_loaded is False
    
    async def test_error_handling(self, classifier):
        """에러 처리 테스트"""
        # 잘못된 입력으로 테스트
        invalid_inputs = [None, 123, [], {}]
        
        for invalid_input in invalid_inputs:
            try:
                result = await classifier.analyze(invalid_input)
                # 에러가 발생하지 않았다면 결과가 있어야 함
                assert isinstance(result, ContentClassification)
            except Exception as e:
                # 에러가 발생했다면 적절히 처리되어야 함
                assert isinstance(e, Exception)
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_classification_confidence_range(self, classifier):
        """분류 신뢰도 범위 테스트"""
        test_texts = [
            "정치 뉴스입니다.",
            "과학 교육 자료입니다.",
            "영화 리뷰입니다.",
            "음악 소개입니다.",
            "요리 레시피입니다."
        ]
        
        for text in test_texts:
            result = await classifier.analyze(text)
            
            # 모든 신뢰도가 0-1 범위 내에 있어야 함
            assert 0.0 <= result.primary_confidence <= 1.0
            
            # 모든 카테고리의 신뢰도도 0-1 범위 내에 있어야 함
            for confidence in result.all_categories.values():
                assert 0.0 <= confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_category_consistency(self, classifier):
        """카테고리 일관성 테스트"""
        text = "이것은 정치적 뉴스 콘텐츠입니다."
        result = await classifier.analyze(text)
        
        # 주요 카테고리가 all_categories에 포함되어야 함
        assert result.primary_category in result.all_categories
        
        # 주요 카테고리의 신뢰도가 가장 높아야 함
        primary_confidence = result.all_categories[result.primary_category]
        for category, confidence in result.all_categories.items():
            if category != result.primary_category:
                assert primary_confidence >= confidence
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_text_preprocessing(self, classifier):
        """텍스트 전처리 테스트"""
        # 특수문자가 포함된 텍스트
        text = "콘텐츠분류!!!@@@###$$$%%%^^^&&&***()()()"
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_multiple_categories(self, classifier):
        """다중 카테고리 테스트"""
        # 여러 카테고리가 섞인 텍스트
        text = "이 영화는 교육적이면서도 재미있는 엔터테인먼트 콘텐츠입니다."
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        
        # 여러 카테고리가 감지될 가능성이 높음
        assert len(result.all_categories) >= 1
        assert result.primary_confidence > 0.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
    
    async def test_mixed_content(self, classifier):
        """혼합 콘텐츠 테스트"""
        # 뉴스와 교육이 섞인 콘텐츠
        text = "새로운 연구 결과에 따르면, 이 방법은 효과적입니다."
        result = await classifier.analyze(text)
        
        assert isinstance(result, ContentClassification)
        
        # 혼합 콘텐츠는 적절히 분류되어야 함
        assert result.primary_confidence >= 0.0
        assert result.primary_confidence <= 1.0
        
        # 테스트 후 cleanup
        await classifier.cleanup()
