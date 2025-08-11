"""
감정 분석 AI 모델
텍스트의 감정을 분석하는 모델입니다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, Any, Optional
import numpy as np

from app.ai.base import BaseAIModel
from app.models.analysis import SentimentAnalysis
from app.core.logging import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer(BaseAIModel):
    """감정 분석 모델"""
    
    def __init__(self, device: str = "cpu"):
        super().__init__("sentiment_analyzer", device)
        self.model_path = "klue/roberta-base"
        self.sentiment_pipeline = None
        self.confidence_threshold = 0.6
        
        # 감정 레이블 매핑
        self.sentiment_mapping = {
            0: "negative",
            1: "neutral", 
            2: "positive"
        }
    
    def load_model(self) -> bool:
        """감정 분석 모델을 로드합니다."""
        try:
            if self.is_loaded:
                return True
            
            logger.info(f"감정 분석 모델 로딩 시작: {self.model_path}")
            
            # transformers 파이프라인 생성
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_path,
                tokenizer=self.model_path,
                device=self.device
            )
            
            self.is_loaded = True
            logger.info("감정 분석 모델 로딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"감정 분석 모델 로딩 실패: {e}")
            self.is_loaded = False
            return False
    
    def unload_model(self) -> bool:
        """감정 분석 모델을 언로드합니다."""
        try:
            if not self.is_loaded:
                return True
            
            # 모델 및 토크나이저 정리
            if hasattr(self, 'sentiment_pipeline'):
                del self.sentiment_pipeline
                self.sentiment_pipeline = None
            
            self.is_loaded = False
            logger.info("감정 분석 모델 언로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"감정 분석 모델 언로드 실패: {e}")
            return False
    
    def analyze(self, text: str, **kwargs) -> SentimentAnalysis:
        """텍스트의 감정을 분석합니다."""
        # 모델이 로드되어 있는지 확인
        if not self.ensure_model_loaded():
            logger.warning("모델이 로드되지 않음. 더미 로직 사용")
            return self._analyze_dummy(text)
        
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # AI 모델로 감정 분석 수행
            sentiment_result = self._analyze_sentiment(processed_text)
            
            # 결과 생성
            return SentimentAnalysis(
                overall_sentiment=sentiment_result["overall_sentiment"],
                dominant_emotion=sentiment_result["dominant_emotion"],
                emotion_breakdown=sentiment_result["emotion_breakdown"],
                confidence=sentiment_result["confidence"],
                reasoning=sentiment_result["reasoning"]
            )
            
        except Exception as e:
            logger.error(f"감정 분석 실패: {e}")
            return self._analyze_dummy(text)
    
    def ensure_model_loaded(self) -> bool:
        """모델이 로드되어 있는지 확인하고, 필요시 로드합니다."""
        if not self.is_loaded:
            return self.load_model()
        return True
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """감정 분석 수행"""
        try:
            # AI 모델로 분석
            results = self.sentiment_pipeline(text, truncation=True, max_length=512)
            
            # 점수 추출
            scores = results[0]
            positive_score = scores[2]['score'] if len(scores) > 2 else 0.0
            negative_score = scores[0]['score'] if len(scores) > 0 else 0.0
            neutral_score = scores[1]['score'] if len(scores) > 1 else 0.0
            
            # 감정 결정
            sentiment_scores = {
                "positive": positive_score,
                "negative": negative_score,
                "neutral": neutral_score
            }
            
            dominant_emotion = max(sentiment_scores, key=sentiment_scores.get)
            
            # overall_sentiment 계산 (-1 ~ 1 범위)
            if dominant_emotion == "positive":
                overall_sentiment = positive_score
            elif dominant_emotion == "negative":
                overall_sentiment = -negative_score
            else:
                overall_sentiment = 0.0
            
            return {
                "overall_sentiment": overall_sentiment,
                "dominant_emotion": dominant_emotion,
                "emotion_breakdown": sentiment_scores,
                "confidence": max(sentiment_scores.values()),  # 가장 높은 점수를 신뢰도로 사용
                "reasoning": f"AI 모델 기반 감정 분석 (신뢰도: {max(sentiment_scores.values()):.3f})"
            }
            
        except Exception as e:
            logger.error(f"AI 모델 감정 분석 실패: {e}")
            return self._analyze_dummy(text)
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 기본 전처리
        text = text.strip()
        text = text[:1000]  # 길이 제한
        
        # 특수문자 정리
        import re
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _analyze_dummy(self, text: str) -> SentimentAnalysis:
        """더미 로직으로 분석 (폴백)"""
        # 간단한 키워드 기반 감정 분석
        positive_words = ["좋다", "훌륭하다", "멋지다", "행복하다", "즐겁다", "감사하다", "좋은", "훌륭한", "멋진", "행복한", "즐거운", "감사한"]
        negative_words = ["나쁘다", "끔찍하다", "슬프다", "화나다", "실망하다", "걱정하다", "나쁜", "끔찍한", "슬픈", "화난", "실망한", "걱정한"]
        neutral_words = ["보통", "일반적", "특별한", "평범한", "보통의", "일반적인", "평범한"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        neutral_count = sum(1 for word in neutral_words if word in text_lower)
        
        # 더 정확한 감정 판단
        if positive_count > negative_count and positive_count > neutral_count:
            dominant_emotion = "positive"
            overall_sentiment = 0.7
            confidence = 0.8
        elif negative_count > positive_count and negative_count > neutral_count:
            dominant_emotion = "negative"
            overall_sentiment = -0.7
            confidence = 0.8
        elif neutral_count > 0 or (positive_count == 0 and negative_count == 0):
            dominant_emotion = "neutral"
            overall_sentiment = 0.0  # 완전 중립
            confidence = 0.9
        else:
            # 약간의 긍정/부정이 섞인 경우
            if positive_count > negative_count:
                dominant_emotion = "positive"
                overall_sentiment = 0.2
                confidence = 0.6
            else:
                dominant_emotion = "negative"
                overall_sentiment = -0.2
                confidence = 0.6
        
        # 감정 분해 계산
        total_words = positive_count + negative_count + neutral_count
        if total_words == 0:
            emotion_breakdown = {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
        else:
            emotion_breakdown = {
                "positive": positive_count / total_words,
                "negative": negative_count / total_words,
                "neutral": neutral_count / total_words
            }
        
        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            dominant_emotion=dominant_emotion,
            emotion_breakdown=emotion_breakdown,
            confidence=confidence,
            reasoning="더미 로직으로 분석 (AI 모델 로딩 실패)"
        )
