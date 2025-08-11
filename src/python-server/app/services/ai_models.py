"""
AI 모델 서비스
여러 AI 모델을 통합하고 관리하는 서비스입니다.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from app.core.logging import get_logger
from app.core.config import get_settings
from app.ai.credibility import CredibilityAnalyzer
from app.ai.bias import BiasDetector
from app.ai.fact_checker import FactChecker
from app.ai.sentiment import SentimentAnalyzer
from app.ai.classifier import ContentClassifier
from app.models.analysis import (
    AnalysisResult,
    CredibilityScore,
    BiasAnalysis,
    FactCheckResult,
    SentimentAnalysis,
    ContentClassification,
    AnalysisMetadata,
    AnalysisStatus,
    AnalysisType
)

logger = get_logger(__name__)
settings = get_settings()


class AIModelService:
    """AI 모델들을 통합하고 관리하는 서비스"""
    
    def __init__(self):
        self.credibility_analyzer = CredibilityAnalyzer()
        self.bias_detector = BiasDetector()
        self.fact_checker = FactChecker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.content_classifier = ContentClassifier()
        
        logger.info("AI 모델 서비스 초기화됨")
    
    async def initialize_models(self):
        """모든 AI 모델을 초기화하고 로드합니다."""
        try:
            logger.info("🔄 AI 모델들 초기화 중...")
            
            # 모든 모델을 병렬로 로드
            tasks = [
                self.credibility_analyzer.load_model(),
                self.bias_detector.load_model(),
                self.fact_checker.load_model(),
                self.sentiment_analyzer.load_model(),
                self.content_classifier.load_model()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 확인
            for i, (model_name, result) in enumerate([
                ("credibility_analyzer", results[0]),
                ("bias_detector", results[1]),
                ("fact_checker", results[2]),
                ("sentiment_analyzer", results[3]),
                ("content_classifier", results[4])
            ]):
                if isinstance(result, Exception):
                    logger.error(f"❌ {model_name} 로드 실패: {result}")
                else:
                    logger.info(f"✅ {model_name} 로드 성공")
            
            logger.info("🎉 AI 모델 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ AI 모델 초기화 실패: {e}")
            raise
    
    async def analyze_content(
        self,
        text: str,
        video_metadata: Optional[Dict[str, Any]] = None,
        analysis_type: str = "full"
    ) -> AnalysisResult:
        """콘텐츠를 종합적으로 분석합니다."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"콘텐츠 분석 시작 (타입: {analysis_type})")
            
            # 모델들이 로드되었는지 확인하고, 필요시 초기화
            if not hasattr(self, '_models_initialized'):
                await self.initialize_models()
                self._models_initialized = True
            
            # 분석 타입에 따라 실행할 분석 결정
            if analysis_type == "full":
                tasks = [
                    self._analyze_credibility(text, video_metadata),
                    self._analyze_bias(text),
                    self._analyze_facts(text),
                    self._analyze_sentiment(text),
                    self._classify_content(text)
                ]
            elif analysis_type == "credibility":
                tasks = [self._analyze_credibility(text, video_metadata)]
            elif analysis_type == "bias":
                tasks = [self._analyze_bias(text)]
            elif analysis_type == "facts":
                tasks = [self._analyze_facts(text)]
            elif analysis_type == "sentiment":
                tasks = [self._analyze_sentiment(text)]
            elif analysis_type == "classification":
                tasks = [self._classify_content(text)]
            else:
                raise ValueError(f"지원하지 않는 분석 타입: {analysis_type}")
            
            # 병렬로 분석 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리 및 통합
            analysis_result = await self._process_results(
                results, analysis_type, start_time, video_metadata
            )
            
            logger.info(f"콘텐츠 분석 완료 (소요시간: {analysis_result.processing_time:.2f}초)")
            return analysis_result
            
        except Exception as e:
            logger.error(f"콘텐츠 분석 실패: {e}")
            raise
    
    async def _analyze_credibility(
        self, 
        text: str, 
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> CredibilityScore:
        """신뢰도 분석"""
        try:
            if video_metadata:
                return await self.credibility_analyzer.analyze(text, video_metadata=video_metadata)
            else:
                return await self.credibility_analyzer.analyze(text)
        except Exception as e:
            logger.error(f"신뢰도 분석 실패: {e}")
            raise
    
    async def _analyze_bias(self, text: str) -> BiasAnalysis:
        """편향 감지 분석"""
        try:
            return await self.bias_detector.analyze(text)
        except Exception as e:
            logger.error(f"편향 감지 실패: {e}")
            raise
    
    async def _analyze_facts(self, text: str) -> FactCheckResult:
        """팩트 체크"""
        try:
            return await self.fact_checker.analyze(text)
        except Exception as e:
            logger.error(f"팩트 체크 실패: {e}")
            raise
    
    async def _analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """감정 분석"""
        try:
            return await self.sentiment_analyzer.analyze(text)
        except Exception as e:
            logger.error(f"감정 분석 실패: {e}")
            raise
    
    async def _classify_content(self, text: str) -> ContentClassification:
        """콘텐츠 분류"""
        try:
            return await self.content_classifier.analyze(text)
        except Exception as e:
            logger.error(f"콘텐츠 분류 실패: {e}")
            raise
    
    async def _process_results(
        self,
        results: List[Any],
        analysis_type: str,
        start_time: Union[datetime, float],
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """분석 결과를 처리하고 통합합니다."""
        end_time = datetime.utcnow()
        
        # start_time이 float인 경우 datetime으로 변환
        if isinstance(start_time, float):
            start_datetime = datetime.fromtimestamp(start_time)
        else:
            start_datetime = start_time
            
        processing_time = (end_time - start_datetime).total_seconds()
        
        # 결과를 적절한 필드에 매핑
        credibility_score = None
        bias_analysis = None
        fact_check_result = None
        sentiment_analysis = None
        content_classification = None
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"분석 {i} 실패: {result}")
                continue
                
            if isinstance(result, CredibilityScore):
                credibility_score = result
            elif isinstance(result, BiasAnalysis):
                bias_analysis = result
            elif isinstance(result, FactCheckResult):
                fact_check_result = result
            elif isinstance(result, SentimentAnalysis):
                sentiment_analysis = result
            elif isinstance(result, ContentClassification):
                content_classification = result
        
        # 종합 분석 결과 생성
        analysis_result = AnalysisResult(
            analysis_id=f"analysis_{start_datetime.timestamp()}",
            video_url="https://example.com",  # TODO: 실제 URL 설정
            analysis_type=AnalysisType.COMPREHENSIVE,  # TODO: 실제 타입 설정
            status=AnalysisStatus.COMPLETED,  # 성공적으로 완료됨
            credibility=credibility_score,
            bias=bias_analysis,
            fact_check=fact_check_result,
            sentiment=sentiment_analysis,
            classification=content_classification,
            created_at=start_datetime,
            completed_at=end_time,
            processing_time=processing_time,
            model_version="1.0.0"
        )
        
        return analysis_result
    
    async def get_model_status(self) -> Dict[str, Any]:
        """모든 AI 모델의 상태를 확인합니다."""
        try:
            status = {
                "credibility_analyzer": await self.credibility_analyzer.get_status(),
                "bias_detector": await self.bias_detector.get_status(),
                "fact_checker": await self.fact_checker.get_status(),
                "sentiment_analyzer": await self.sentiment_analyzer.get_status(),
                "content_classifier": await self.content_classifier.get_status(),
                "timestamp": datetime.utcnow().isoformat()
            }
            return status
        except Exception as e:
            logger.error(f"모델 상태 확인 실패: {e}")
            return {"error": str(e)}
    
    async def reload_models(self) -> Dict[str, bool]:
        """모든 AI 모델을 다시 로드합니다."""
        try:
            results = {}
            
            # 각 모델을 순차적으로 리로드
            for model_name, model in [
                ("credibility_analyzer", self.credibility_analyzer),
                ("bias_detector", self.bias_detector),
                ("fact_checker", self.fact_checker),
                ("sentiment_analyzer", self.sentiment_analyzer),
                ("content_classifier", self.content_classifier)
            ]:
                try:
                    if hasattr(model, 'reload'):
                        await model.reload()
                        results[model_name] = True
                        logger.info(f"{model_name} 리로드 성공")
                    else:
                        results[model_name] = False
                        logger.warning(f"{model_name}는 리로드 기능을 지원하지 않음")
                except Exception as e:
                    results[model_name] = False
                    logger.error(f"{model_name} 리로드 실패: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"모델 리로드 실패: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            # 각 모델의 정리 메서드 호출
            for model_name, model in [
                ("credibility_analyzer", self.credibility_analyzer),
                ("bias_detector", self.bias_detector),
                ("fact_checker", self.fact_checker),
                ("sentiment_analyzer", self.sentiment_analyzer),
                ("content_classifier", self.content_classifier)
            ]:
                try:
                    if hasattr(model, 'cleanup'):
                        await model.cleanup()
                        logger.debug(f"{model_name} 정리 완료")
                except Exception as e:
                    logger.warning(f"{model_name} 정리 실패: {e}")
            
            logger.info("AI 모델 서비스 정리 완료")
            
        except Exception as e:
            logger.error(f"AI 모델 서비스 정리 실패: {e}")


# 전역 AI 모델 서비스 인스턴스
ai_model_service = AIModelService()


def get_ai_model_service() -> AIModelService:
    """AI 모델 서비스 인스턴스를 반환합니다."""
    return ai_model_service
