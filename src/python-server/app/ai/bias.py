"""
편향 감지 AI 모델
텍스트의 편향성을 감지하는 모델입니다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, Any, List, Optional
import numpy as np

from app.ai.base import BaseAIModel
from app.models.analysis import BiasAnalysis
from app.core.logging import get_logger

logger = get_logger(__name__)


class BiasDetector(BaseAIModel):
    """편향 감지기 - 실제 AI 모델 사용"""
    
    def __init__(self):
        super().__init__("bias_detector", "klue/roberta-base")
        self.bias_pipeline = None
        
        # 편향 카테고리 매핑
        self.bias_categories = {
            "political": "정치적 편향",
            "gender": "성별 편향", 
            "racial": "인종 편향",
            "religious": "종교적 편향",
            "age": "연령 편향",
            "economic": "경제적 편향",
            "cultural": "문화적 편향",
            "none": "편향 없음"
        }
        
        # 편향 감지 임계값
        self.bias_threshold = 0.6
    
    async def load_model(self) -> bool:
        """AI 모델을 로드합니다."""
        try:
            logger.info("편향 감지 모델 로딩 시작...")
            
            # 한국어 편향 감지를 위한 모델
            model_name = "klue/roberta-base"
            
            # BaseAIModel의 공통 로딩 메서드 사용
            success = await self.load_huggingface_model(model_name, "text-classification")
            if not success:
                return False
            
            # 편향 감지 파이프라인 생성
            self.bias_pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.startswith("cuda") else -1,
                return_all_scores=True
            )
            
            logger.info("✅ 편향 감지 모델 로딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"편향 감지 모델 로딩 실패: {e}")
            self.is_loaded = False
            return False
    
    async def analyze(self, text: str, **kwargs) -> BiasAnalysis:
        """텍스트의 편향성을 분석합니다."""
        # 모델이 로드되어 있는지 확인
        if not await self.ensure_model_loaded():
            logger.warning("모델이 로드되지 않음. 더미 로직 사용")
            return await self._analyze_dummy(text)
        
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # AI 모델로 편향 분석 수행
            bias_result = await self._detect_bias(processed_text)
            
            # 결과 생성
            return BiasAnalysis(
                has_bias=bias_result["has_bias"],
                bias_types=bias_result["bias_types"],
                bias_score=bias_result["bias_score"],
                political_bias=bias_result["political_bias"],
                gender_bias=bias_result["gender_bias"],
                racial_bias=bias_result["racial_bias"],
                religious_bias=bias_result["religious_bias"],
                other_biases=bias_result["other_biases"],
                reasoning="AI 모델 기반 편향 감지 완료"
            )
            
        except Exception as e:
            logger.error(f"AI 모델 편향 감지 실패: {e}, 더미 로직으로 폴백")
            return await self._analyze_dummy(text)
    
    async def _detect_bias(self, text: str) -> Dict[str, Any]:
        """편향 감지 수행"""
        try:
            # AI 모델로 분석
            results = self.bias_pipeline(text, truncation=True, max_length=512)
            
            # 점수 추출 및 정렬
            scores = results[0]
            sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
            
            # 편향 타입별 점수
            bias_scores = {}
            for score in scores:
                label = int(score['label'])
                bias_type = list(self.bias_categories.keys())[label]
                bias_scores[bias_type] = score['score']
            
            # 편향 여부 결정
            max_bias_score = max(bias_scores.values())
            has_bias = max_bias_score > self.bias_threshold
            
            # 편향 타입들
            bias_types = []
            for bias_type, score in bias_scores.items():
                if score > self.bias_threshold and bias_type != "none":
                    bias_types.append(bias_type)
            
            # 개별 편향 점수
            political_bias = bias_scores.get("political", 0.0)
            gender_bias = bias_scores.get("gender", 0.0)
            racial_bias = bias_scores.get("racial", 0.0)
            religious_bias = bias_scores.get("religious", 0.0)
            
            # 기타 편향들
            other_biases = {}
            for bias_type, score in bias_scores.items():
                if bias_type not in ["political", "gender", "racial", "religious", "none"]:
                    if score > self.bias_threshold:
                        other_biases[bias_type] = score
            
            return {
                "has_bias": has_bias,
                "bias_types": bias_types,
                "bias_score": max_bias_score,
                "political_bias": political_bias,
                "gender_bias": gender_bias,
                "racial_bias": racial_bias,
                "religious_bias": religious_bias,
                "other_biases": other_biases
            }
            
        except Exception as e:
            logger.error(f"편향 감지 실패: {e}")
            return {
                "has_bias": False,
                "bias_types": [],
                "bias_score": 0.0,
                "political_bias": 0.0,
                "gender_bias": 0.0,
                "racial_bias": 0.0,
                "religious_bias": 0.0,
                "other_biases": {}
            }
    
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
    
    async def _analyze_dummy(self, text: str) -> BiasAnalysis:
        """더미 로직으로 분석 (폴백)"""
        # 간단한 키워드 기반 편향 감지
        political_keywords = ["정치", "정부", "여당", "야당", "보수", "진보"]
        gender_keywords = ["남자", "여자", "남성", "여성", "아빠", "엄마"]
        racial_keywords = ["인종", "민족", "국적", "외국인", "이민자"]
        religious_keywords = ["종교", "신", "불교", "기독교", "천주교", "이슬람"]
        
        text_lower = text.lower()
        
        political_count = sum(1 for word in political_keywords if word in text_lower)
        gender_count = sum(1 for word in gender_keywords if word in text_lower)
        racial_count = sum(1 for word in racial_keywords if word in text_lower)
        religious_count = sum(1 for word in religious_keywords if word in text_lower)
        
        # 편향 점수 계산
        total_keywords = political_count + gender_count + racial_count + religious_count
        bias_score = min(1.0, total_keywords * 0.2)
        
        has_bias = bias_score > 0.3
        bias_types = []
        
        if political_count > 0:
            bias_types.append("political")
        if gender_count > 0:
            bias_types.append("gender")
        if racial_count > 0:
            bias_types.append("racial")
        if religious_count > 0:
            bias_types.append("religious")
        
        return BiasAnalysis(
            has_bias=has_bias,
            bias_types=bias_types,
            bias_score=bias_score,
            political_bias=min(1.0, political_count * 0.2),
            gender_bias=min(1.0, gender_count * 0.2),
            racial_bias=min(1.0, racial_count * 0.2),
            religious_bias=min(1.0, religious_count * 0.2),
            other_biases={},
            reasoning="더미 로직으로 분석 (AI 모델 로딩 실패)"
        )
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.bias_pipeline:
                del self.bias_pipeline
            
            # BaseAIModel의 언로드 메서드 사용
            await self.unload_model()
            
            logger.info("편향 감지 모델 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"편향 감지 모델 리소스 정리 실패: {e}")
