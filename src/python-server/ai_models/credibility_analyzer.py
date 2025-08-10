"""
신뢰도 분석기
YouTube 영상의 신뢰도를 종합적으로 분석하는 AI 모델
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .sentiment_analyzer import SentimentAnalyzer
from .bias_detector import BiasDetector
from .fact_checker import FactChecker
from .source_validator import SourceValidator
from .content_classifier import ContentClassifier


@dataclass
class CredibilityResult:
    """신뢰도 분석 결과"""
    video_id: str
    credibility_score: float  # 0-100
    credibility_grade: str    # A, B, C, D, F
    bias_score: float         # 0-100
    fact_check_score: float   # 0-100
    source_score: float       # 0-100
    sentiment_score: float    # 0-100
    content_category: str     # 정치, 경제, 시사, 투자, 사회 등
    analysis_breakdown: Dict
    explanation: str
    confidence_score: float   # 0-100
    processing_time_ms: int
    model_version: str


class CredibilityAnalyzer:
    """신뢰도 분석기 메인 클래스"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.bias_detector = BiasDetector()
        self.fact_checker = FactChecker()
        self.source_validator = SourceValidator()
        self.content_classifier = ContentClassifier()
        
        self.logger = logging.getLogger(__name__)
        
    async def analyze_video(self, video_data: Dict) -> CredibilityResult:
        """영상 신뢰도 분석"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. 콘텐츠 분류
            content_category = await self.content_classifier.classify(video_data)
            
            # 2. 자막 텍스트 추출
            transcript = await self._extract_transcript(video_data)
            
            # 3. 병렬로 각 분석 수행
            tasks = [
                self.sentiment_analyzer.analyze(transcript),
                self.bias_detector.detect(transcript),
                self.fact_checker.verify(transcript),
                self.source_validator.validate(video_data)
            ]
            
            results = await asyncio.gather(*tasks)
            sentiment_score, bias_score, fact_score, source_score = results
            
            # 4. 종합 신뢰도 계산
            credibility_score = self._calculate_credibility(
                sentiment_score, bias_score, fact_score, source_score
            )
            
            # 5. 등급 분류
            credibility_grade = self._classify_grade(credibility_score)
            
            # 6. 설명 생성
            explanation = self._generate_explanation(
                credibility_score, bias_score, fact_score, source_score
            )
            
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            return CredibilityResult(
                video_id=video_data.get('video_id'),
                credibility_score=credibility_score,
                credibility_grade=credibility_grade,
                bias_score=bias_score,
                fact_check_score=fact_score,
                source_score=source_score,
                sentiment_score=sentiment_score,
                content_category=content_category,
                analysis_breakdown={
                    'sentiment': sentiment_score,
                    'bias': bias_score,
                    'fact_check': fact_score,
                    'source': source_score
                },
                explanation=explanation,
                confidence_score=self._calculate_confidence(
                    sentiment_score, bias_score, fact_score, source_score
                ),
                processing_time_ms=processing_time,
                model_version="1.0.0"
            )
            
        except Exception as e:
            self.logger.error(f"영상 분석 중 오류 발생: {e}")
            raise
    
    async def _extract_transcript(self, video_data: Dict) -> str:
        """자막 텍스트 추출"""
        # YouTube API를 통해 자막 추출
        # 실제 구현에서는 youtube-transcript-api 사용
        return video_data.get('transcript', '')
    
    def _calculate_credibility(
        self, 
        sentiment_score: float, 
        bias_score: float, 
        fact_score: float, 
        source_score: float
    ) -> float:
        """종합 신뢰도 점수 계산"""
        # 가중치 설정 (머신러닝으로 최적화 가능)
        weights = {
            'sentiment': 0.2,
            'bias': 0.3,
            'fact_check': 0.3,
            'source': 0.2
        }
        
        weighted_score = (
            sentiment_score * weights['sentiment'] +
            bias_score * weights['bias'] +
            fact_score * weights['fact_check'] +
            source_score * weights['source']
        )
        
        return round(weighted_score, 2)
    
    def _classify_grade(self, credibility_score: float) -> str:
        """신뢰도 등급 분류"""
        if credibility_score >= 80:
            return 'A'
        elif credibility_score >= 60:
            return 'B'
        elif credibility_score >= 40:
            return 'C'
        elif credibility_score >= 20:
            return 'D'
        else:
            return 'F'
    
    def _generate_explanation(
        self, 
        credibility_score: float, 
        bias_score: float, 
        fact_score: float, 
        source_score: float
    ) -> str:
        """분석 결과 설명 생성"""
        if credibility_score >= 80:
            base = "이 영상은 높은 신뢰도를 보입니다."
        elif credibility_score >= 60:
            base = "이 영상은 보통 수준의 신뢰도를 보입니다."
        elif credibility_score >= 40:
            base = "이 영상은 낮은 신뢰도를 보입니다."
        else:
            base = "이 영상은 매우 낮은 신뢰도를 보입니다."
        
        details = []
        if bias_score < 50:
            details.append("편향성이 낮습니다")
        if fact_score < 50:
            details.append("사실 확인이 부족합니다")
        if source_score < 50:
            details.append("출처 정보가 부족합니다")
        
        if details:
            base += f" 주의사항: {', '.join(details)}"
        
        return base
    
    def _calculate_confidence(
        self, 
        sentiment_score: float, 
        bias_score: float, 
        fact_score: float, 
        source_score: float
    ) -> float:
        """분석 신뢰도 계산"""
        # 각 분석의 신뢰도를 종합
        scores = [sentiment_score, bias_score, fact_score, source_score]
        return round(sum(scores) / len(scores), 2)
