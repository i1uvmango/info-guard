"""
콘텐츠 분류 AI 모델
텍스트의 주제와 카테고리를 분류하는 모델입니다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, Any, List, Optional
import numpy as np

from app.ai.base import BaseAIModel
from app.models.analysis import ContentClassification
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentClassifier(BaseAIModel):
    """콘텐츠 분류기 - 실제 AI 모델 사용"""
    
    def __init__(self):
        super().__init__("content_classifier", "klue/roberta-base")
        self.classifier_pipeline = None
        self.classification_pipeline = None
        
        # 카테고리 매핑
        self.category_mapping = {
            0: "정치",
            1: "경제", 
            2: "사회",
            3: "과학기술",
            4: "문화예술",
            5: "스포츠",
            6: "연예",
            7: "건강",
            8: "일반"
        }
        
        # 콘텐츠 타입 매핑
        self.content_type_mapping = {
            0: "뉴스",
            1: "의견/칼럼",
            2: "교육/강의", 
            3: "리뷰/평가",
            4: "인터뷰/대화",
            5: "일반"
        }
        
        # 대상 독자 매핑
        self.audience_mapping = {
            0: "어린이",
            1: "청소년", 
            2: "성인",
            3: "전문가",
            4: "일반"
        }
    
    async def load_model(self) -> bool:
        """AI 모델을 로드합니다."""
        try:
            logger.info("콘텐츠 분류 모델 로딩 시작...")
            
            # 한국어 텍스트 분류를 위한 모델 (KoBERT 기반)
            model_name = "klue/roberta-base"
            
            # BaseAIModel의 공통 로딩 메서드 사용
            success = await self.load_huggingface_model(model_name, "text-classification")
            if not success:
                return False
            
            # 분류 파이프라인 생성
            self.classifier_pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.startswith("cuda") else -1,
                return_all_scores=True
            )
            
            logger.info("✅ 콘텐츠 분류 모델 로딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"콘텐츠 분류 모델 로딩 실패: {e}")
            self.is_loaded = False
            return False
    
    async def analyze(self, text: str, **kwargs) -> ContentClassification:
        """텍스트의 콘텐츠를 분류합니다."""
        # 모델이 로드되어 있는지 확인
        if not await self.ensure_model_loaded():
            logger.warning("모델이 로드되지 않음. 더미 로직 사용")
            return await self._analyze_dummy(text)
        
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # AI 모델로 분류 수행
            category_result = await self._classify_category(processed_text)
            content_type_result = await self._classify_content_type(processed_text)
            audience_result = await self._classify_audience(processed_text)
            
            # 신뢰도 계산
            confidence = self._calculate_confidence(
                category_result, content_type_result, audience_result
            )
            
            # 결과 생성
            return ContentClassification(
                primary_category=category_result["primary"],
                primary_confidence=confidence,
                all_categories={category_result["primary"]: confidence},
                content_type=content_type_result,
                topic=category_result["primary"],
                target_audience=audience_result,
                reasoning="AI 모델 기반 콘텐츠 분류 완료"
            )
            
        except Exception as e:
            logger.error(f"AI 모델 분류 실패: {e}, 더미 로직으로 폴백")
            return await self._analyze_dummy(text)
    
    async def _classify_category(self, text: str) -> Dict[str, Any]:
        """카테고리 분류"""
        try:
            # AI 모델로 분류
            results = self.classifier_pipeline(text, truncation=True, max_length=512)
            
            # 점수 정렬
            scores = results[0]
            sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
            
            # 주요 카테고리 (가장 높은 점수)
            primary_category = self.category_mapping[int(sorted_scores[0]['label'])]
            
            # 보조 카테고리 (상위 3개)
            secondary_categories = []
            for score in sorted_scores[1:4]:
                if score['score'] > 0.3:  # 임계값 이상만
                    category = self.category_mapping[int(score['label'])]
                    if category not in secondary_categories:
                        secondary_categories.append(category)
            
            return {
                "primary": primary_category,
                "secondary": secondary_categories
            }
            
        except Exception as e:
            logger.error(f"카테고리 분류 실패: {e}")
            return {"primary": "일반", "secondary": []}
    
    async def _classify_content_type(self, text: str) -> str:
        """콘텐츠 타입 분류"""
        try:
            # 간단한 키워드 기반 분류 (향후 AI 모델로 교체 가능)
            if any(word in text for word in ["뉴스", "보도", "기사", "속보"]):
                return "뉴스"
            elif any(word in text for word in ["의견", "칼럼", "사설", "논평"]):
                return "의견/칼럼"
            elif any(word in text for word in ["교육", "강의", "설명", "튜토리얼"]):
                return "교육/강의"
            elif any(word in text for word in ["리뷰", "평가", "비교", "추천"]):
                return "리뷰/평가"
            elif any(word in text for word in ["인터뷰", "대화", "질문", "답변"]):
                return "인터뷰/대화"
            else:
                return "일반"
                
        except Exception as e:
            logger.error(f"콘텐츠 타입 분류 실패: {e}")
            return "일반"
    
    async def _classify_audience(self, text: str) -> str:
        """대상 독자 분류"""
        try:
            # 간단한 키워드 기반 분류 (향후 AI 모델로 교체 가능)
            if any(word in text for word in ["어린이", "아이", "초등학생", "유아"]):
                return "어린이"
            elif any(word in text for word in ["청소년", "중학생", "고등학생", "학생"]):
                return "청소년"
            elif any(word in text for word in ["성인", "직장인", "부모", "가족"]):
                return "성인"
            elif any(word in text for word in ["전문가", "연구자", "학자", "전문직"]):
                return "전문가"
            else:
                return "일반"
                
        except Exception as e:
            logger.error(f"대상 독자 분류 실패: {e}")
            return "일반"
    
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
    
    def _calculate_confidence(
        self, 
        category_result: Dict[str, Any], 
        content_type_result: str, 
        audience_result: str
    ) -> float:
        """신뢰도 계산"""
        # 기본 신뢰도
        confidence = 0.8
        
        # 카테고리 신뢰도 조정
        if len(category_result["secondary"]) > 0:
            confidence += 0.1
        
        # 콘텐츠 타입이 명확할 때
        if content_type_result != "일반":
            confidence += 0.05
        
        # 대상 독자가 명확할 때
        if audience_result != "일반":
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    async def _analyze_dummy(self, text: str) -> ContentClassification:
        """더미 로직으로 분석 (폴백)"""
        # 기존 더미 로직 유지
        primary_category = self._detect_primary_category(text)
        secondary_categories = self._detect_secondary_categories(text)
        content_type = self._detect_content_type(text)
        target_audience = self._detect_target_audience(text)
        
        return ContentClassification(
            primary_category=primary_category,
            primary_confidence=0.6,
            all_categories={primary_category: 0.6},
            content_type=content_type,
            topic=primary_category,
            target_audience=target_audience,
            reasoning="더미 로직으로 분석 (AI 모델 로딩 실패)"
        )
    
    def _detect_primary_category(self, text: str) -> str:
        """주요 카테고리를 감지합니다."""
        category_keywords = {
            "정치": ["정치", "정부", "국회", "선거", "여당", "야당", "정책"],
            "경제": ["경제", "금융", "주식", "부동산", "투자", "기업", "시장"],
            "사회": ["사회", "교육", "의료", "환경", "교통", "복지", "범죄"],
            "과학기술": ["과학", "기술", "연구", "발명", "AI", "로봇", "우주"],
            "문화예술": ["문화", "예술", "영화", "음악", "문학", "미술", "공연"],
            "스포츠": ["스포츠", "축구", "야구", "농구", "올림픽", "경기", "선수"],
            "연예": ["연예", "배우", "가수", "방송", "드라마", "예능", "뉴스"],
            "건강": ["건강", "의학", "질병", "운동", "영양", "정신건강", "치료"]
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score
        
        if not any(category_scores.values()):
            return "일반"
        
        primary_category = max(category_scores, key=category_scores.get)
        return primary_category
    
    def _detect_secondary_categories(self, text: str) -> List[str]:
        """보조 카테고리들을 감지합니다."""
        secondary_categories = []
        
        # 주요 카테고리 외의 카테고리들
        all_categories = [
            "정치", "경제", "사회", "과학기술", "문화예술", 
            "스포츠", "연예", "건강", "일반"
        ]
        
        for category in all_categories:
            if category in text and category not in secondary_categories:
                secondary_categories.append(category)
        
        # 최대 3개까지만 반환
        return secondary_categories[:3]
    
    def _detect_content_type(self, text: str) -> str:
        """콘텐츠 유형을 감지합니다."""
        if any(word in text for word in ["뉴스", "보도", "기사", "속보"]):
            return "뉴스"
        elif any(word in text for word in ["의견", "칼럼", "사설", "논평"]):
            return "의견/칼럼"
        elif any(word in text for word in ["교육", "강의", "설명", "튜토리얼"]):
            return "교육/강의"
        elif any(word in text for word in ["리뷰", "평가", "비교", "추천"]):
            return "리뷰/평가"
        elif any(word in text for word in ["인터뷰", "대화", "질문", "답변"]):
            return "인터뷰/대화"
        else:
            return "일반"
    
    def _detect_target_audience(self, text: str) -> str:
        """대상 독자를 감지합니다."""
        if any(word in text for word in ["어린이", "아이", "초등학생", "유아"]):
            return "어린이"
        elif any(word in text for word in ["청소년", "중학생", "고등학생", "학생"]):
            return "청소년"
        elif any(word in text for word in ["성인", "직장인", "부모", "가족"]):
            return "성인"
        elif any(word in text for word in ["전문가", "연구자", "학자", "전문직"]):
            return "전문가"
        else:
            return "일반"
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.classifier_pipeline:
                del self.classifier_pipeline
            
            # BaseAIModel의 언로드 메서드 사용
            await self.unload_model()
            
            logger.info("콘텐츠 분류 모델 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"콘텐츠 분류 모델 리소스 정리 실패: {e}")
