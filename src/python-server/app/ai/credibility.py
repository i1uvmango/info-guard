"""
신뢰도 분석 AI 모델
실제 AI 모델을 사용하여 텍스트의 신뢰도를 분석합니다.
"""

import asyncio
from typing import Dict, Any, List
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
from loguru import logger

from .base import BaseAIModel
from ..models.analysis import CredibilityScore


class CredibilityAnalyzer(BaseAIModel):
    """신뢰도 분석 AI 모델"""
    
    def __init__(self):
        super().__init__("credibility_analyzer", "facebook/bart-large-mnli")
        self.sentence_transformer = None
        self.credibility_pipeline = None
        self.claim_detection_pipeline = None
        
    async def load_model(self) -> bool:
        """모델 로드"""
        try:
            logger.info(f"🔄 신뢰도 분석 모델 로딩 중: {self.model_name}")
            
            # BaseAIModel의 공통 로딩 메서드 사용
            success = await self.load_huggingface_model(self.model_path, "text-classification")
            if not success:
                return False
            
            # 문장 임베딩 모델 로드
            self.sentence_transformer = SentenceTransformer(
                'all-MiniLM-L6-v2',
                device=self.device
            )
            
            # 사실 확인 파이프라인
            self.fact_check_pipeline = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device.startswith("cuda") else -1,
                batch_size=self.gpu_config.batch_size
            )
            
            # 주장 감지 파이프라인
            self.claim_detection_pipeline = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                device=0 if self.device.startswith("cuda") else -1,
                batch_size=self.gpu_config.batch_size
            )
            
            logger.info("✅ 신뢰도 분석 모델 로딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 신뢰도 분석 모델 로딩 실패: {e}")
            return False
    
    async def analyze(self, text: str, **kwargs) -> CredibilityAnalysis:
        """텍스트 신뢰도 분석"""
        # 모델이 로드되어 있는지 확인
        if not await self.ensure_model_loaded():
            logger.warning("모델이 로드되지 않음. 기본값 반환")
            return CredibilityAnalysis(
                credibility_score=0.5,
                fact_check_score=0.5,
                source_reliability_score=0.5,
                consistency_score=0.5,
                objectivity_score=0.5,
                credibility_level="중간",
                reasoning="모델 로딩 실패"
            )
        
        try:
            logger.info(f"🔍 신뢰도 분석 시작: {text[:100]}...")
            
            # 1. 사실 확인 (Fact-checking)
            fact_check_result = await self._check_facts(text)
            
            # 2. 출처 신뢰도 평가
            source_credibility = await self._evaluate_source_credibility(text)
            
            # 3. 주장 강도 분석
            claim_strength = await self._analyze_claim_strength(text)
            
            # 4. 일관성 검사
            consistency_score = await self._check_consistency(text)
            
            # 5. 최종 신뢰도 점수 계산
            final_score = self._calculate_final_score(
                fact_check_result,
                source_credibility,
                claim_strength,
                consistency_score
            )
            
            # 6. 신뢰도 레벨 결정
            credibility_level = self._determine_credibility_level(final_score)
            
            result = CredibilityAnalysis(
                credibility_score=final_score,
                fact_check_score=fact_check_result,
                source_reliability_score=source_credibility,
                consistency_score=consistency_score,
                objectivity_score=1.0 - claim_strength,  # 편향성이 낮을수록 객관성 높음
                credibility_level=credibility_level,
                reasoning=f"AI 모델 기반 다중 요소 분석: 사실확인({fact_check_result:.2f}), 출처({source_credibility:.2f}), 주장강도({claim_strength:.2f}), 일관성({consistency_score:.2f})"
            )
            
            logger.info(f"✅ 신뢰도 분석 완료: 점수 {final_score:.2f}, 레벨 {credibility_level}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 신뢰도 분석 실패: {e}")
            # 에러 발생 시 기본값 반환
            return CredibilityAnalysis(
                credibility_score=0.5,
                fact_check_score=0.5,
                source_reliability_score=0.5,
                consistency_score=0.5,
                objectivity_score=0.5,
                credibility_level="중간",
                reasoning=f"분석 중 오류 발생: {str(e)}"
            )
    
    async def _check_facts(self, text: str) -> float:
        """사실 확인"""
        try:
            # 텍스트를 문장 단위로 분리
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return 0.5
            
            # 각 문장의 사실성 평가
            fact_scores = []
            for sentence in sentences[:5]:  # 최대 5개 문장만 분석
                if len(sentence) > 10:  # 너무 짧은 문장 제외
                    result = self.fact_check_pipeline(sentence)
                    # 결과를 0-1 점수로 변환
                    score = self._normalize_fact_check_result(result)
                    fact_scores.append(score)
            
            if fact_scores:
                return sum(fact_scores) / len(fact_scores)
            return 0.5
            
        except Exception as e:
            logger.warning(f"사실 확인 실패: {e}")
            return 0.5
    
    async def _evaluate_source_credibility(self, text: str) -> float:
        """출처 신뢰도 평가"""
        try:
            # 신뢰할 수 있는 키워드 패턴
            credible_patterns = [
                "연구에 따르면", "조사 결과", "공식 발표", "전문가 의견",
                "학술 논문", "peer-reviewed", "메타 분석", "시스템 리뷰"
            ]
            
            # 신뢰할 수 없는 키워드 패턴
            non_credible_patterns = [
                "소문에 따르면", "익명의 소식통", "누군가 말하기를",
                "인터넷에서 본", "카톡으로 받은", "전화로 들은"
            ]
            
            credible_count = sum(1 for pattern in credible_patterns if pattern in text)
            non_credible_count = sum(1 for pattern in non_credible_patterns if pattern in text)
            
            # 기본 점수 0.5에서 시작
            base_score = 0.5
            credible_bonus = credible_count * 0.1
            non_credible_penalty = non_credible_count * 0.15
            
            final_score = base_score + credible_bonus - non_credible_penalty
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            logger.warning(f"출처 신뢰도 평가 실패: {e}")
            return 0.5
    
    async def _analyze_claim_strength(self, text: str) -> float:
        """주장 강도 분석"""
        try:
            # 강한 주장 표현
            strong_claims = [
                "확실히", "분명히", "틀림없이", "100%", "절대적으로",
                "의심의 여지 없이", "입증된 사실", "과학적 사실"
            ]
            
            # 약한 주장 표현
            weak_claims = [
                "아마도", "어쩌면", "추정", "가능성", "~일 수도",
                "~라고 생각", "~일 것 같다", "~일지도"
            ]
            
            strong_count = sum(1 for claim in strong_claims if claim in text)
            weak_count = sum(1 for claim in weak_claims if claim in text)
            
            # 주장 강도 계산 (강할수록 높은 점수)
            if strong_count > 0 and weak_count == 0:
                return 0.8
            elif strong_count > weak_count:
                return 0.6
            elif weak_count > strong_count:
                return 0.3
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"주장 강도 분석 실패: {e}")
            return 0.5
    
    async def _check_consistency(self, text: str) -> float:
        """일관성 검사"""
        try:
            # 문장 임베딩을 사용한 일관성 검사
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
            
            if len(sentences) < 2:
                return 0.7  # 문장이 하나뿐이면 중간 점수
            
            # 문장 임베딩 계산
            embeddings = self.sentence_transformer.encode(sentences)
            
            # 코사인 유사도 계산
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            similarity_matrix = cosine_similarity(embeddings)
            
            # 대각선 제외한 유사도 평균
            n = len(similarity_matrix)
            total_similarity = 0
            count = 0
            
            for i in range(n):
                for j in range(i+1, n):
                    total_similarity += similarity_matrix[i][j]
                    count += 1
            
            if count > 0:
                avg_similarity = total_similarity / count
                # 유사도가 높을수록 일관성이 높음
                return float(avg_similarity)
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"일관성 검사 실패: {e}")
            return 0.5
    
    def _normalize_fact_check_result(self, result) -> float:
        """사실 확인 결과를 0-1 점수로 정규화"""
        try:
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            if isinstance(result, dict):
                label = result.get('label', '')
                score = result.get('score', 0.0)
                
                # 라벨에 따른 점수 조정
                if 'entailment' in label.lower() or 'true' in label.lower():
                    return score
                elif 'contradiction' in label.lower() or 'false' in label.lower():
                    return 1.0 - score
                else:
                    return score
            
            return 0.5
            
        except Exception as e:
            logger.warning(f"결과 정규화 실패: {e}")
            return 0.5
    
    def _calculate_final_score(self, fact_check: float, source: float, 
                              claim: float, consistency: float) -> float:
        """최종 신뢰도 점수 계산"""
        # 가중치 설정
        weights = {
            'fact_check': 0.4,      # 사실 확인이 가장 중요
            'source': 0.3,          # 출처 신뢰도
            'claim': 0.2,           # 주장 강도
            'consistency': 0.1      # 일관성
        }
        
        final_score = (
            fact_check * weights['fact_check'] +
            source * weights['source'] +
            claim * weights['claim'] +
            consistency * weights['consistency']
        )
        
        return round(final_score, 3)
    
    def _determine_credibility_level(self, score: float) -> str:
        """신뢰도 레벨 결정"""
        if score >= 0.8:
            return "very_high"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.sentence_transformer:
                del self.sentence_transformer
            if self.fact_check_pipeline:
                del self.fact_check_pipeline
            if self.claim_detection_pipeline:
                del self.claim_detection_pipeline
            
            # BaseAIModel의 언로드 메서드 사용
            await self.unload_model()
            
            logger.info("✅ 신뢰도 분석 모델 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ 신뢰도 분석 모델 리소스 정리 실패: {e}")
