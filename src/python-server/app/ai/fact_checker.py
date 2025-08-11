"""
사실 확인 AI 모델
텍스트의 사실성을 검증하는 모델입니다.
"""

import torch
from transformers import pipeline
from typing import Dict, Any, List
from loguru import logger

from app.ai.base import BaseAIModel
from app.models.analysis import FactCheckResult


class FactChecker(BaseAIModel):
    """사실 확인기 - 실제 AI 모델 사용"""
    
    def __init__(self):
        super().__init__("fact_checker", "facebook/bart-large-mnli")
        self.fact_check_pipeline = None
        self.entailment_pipeline = None
        self.fact_check_threshold = 0.7
    
    async def load_model(self) -> bool:
        """AI 모델을 로드합니다."""
        try:
            logger.info("사실 확인 모델 로딩 시작...")
            
            # BaseAIModel의 공통 로딩 메서드 사용
            success = await self.load_huggingface_model(self.model_path, "text-classification")
            if not success:
                return False
            
            # 사실 확인 파이프라인 생성
            self.fact_check_pipeline = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device.startswith("cuda") else -1,
                return_all_scores=True
            )
            
            # 전제-가설 관계 파이프라인
            self.entailment_pipeline = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device.startswith("cuda") else -1,
                return_all_scores=True
            )
            
            logger.info("✅ 사실 확인 모델 로딩 완료")
            return True
            
        except Exception as e:
            logger.error(f"사실 확인 모델 로딩 실패: {e}")
            self.is_loaded = False
            return False
    
    async def analyze(self, text: str, **kwargs) -> FactCheckAnalysis:
        """텍스트의 사실성을 검증합니다."""
        # 모델이 로드되어 있는지 확인
        if not await self.ensure_model_loaded():
            logger.warning("모델이 로드되지 않음. 더미 로직 사용")
            return await self._analyze_dummy(text)
        
        try:
            # 텍스트 전처리
            processed_text = self._preprocess_text(text)
            
            # AI 모델로 사실 확인 수행
            fact_score = await self._calculate_fact_score_ai(processed_text)
            fact_claims = await self._extract_fact_claims_ai(processed_text)
            verification_status = await self._check_verification_status_ai(processed_text)
            sources = await self._identify_sources_ai(processed_text)
            
            return FactCheckAnalysis(
                fact_check_score=fact_score,
                claim_verification_score=fact_score,
                source_analysis_score=0.8,
                evidence_strength_score=fact_score,
                fact_check_result=verification_status,
                reasoning="AI 모델 기반 사실 확인 완료"
            )
            
        except Exception as e:
            logger.error(f"AI 모델 사실 확인 실패: {e}, 더미 로직으로 폴백")
            return await self._analyze_dummy(text)
    
    async def _calculate_fact_score_ai(self, text: str) -> float:
        """AI 모델을 사용하여 사실성 점수를 계산합니다."""
        try:
            # 텍스트를 문장 단위로 분리
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
            
            if not sentences:
                return 0.5
            
            # 각 문장의 사실성 평가
            fact_scores = []
            for sentence in sentences[:5]:  # 최대 5개 문장만 분석
                # 전제-가설 관계 분석
                result = self.entailment_pipeline(
                    sentence,
                    candidate_labels=["entailment", "neutral", "contradiction"]
                )
                
                # entailment 점수가 높을수록 사실성 높음
                entailment_score = result[0][0]['score'] if result[0][0]['label'] == 'entailment' else 0.0
                contradiction_score = result[0][2]['score'] if len(result[0]) > 2 and result[0][2]['label'] == 'contradiction' else 0.0
                
                # 사실성 점수 계산
                sentence_score = entailment_score - contradiction_score
                fact_scores.append(max(0.0, sentence_score))
            
            if fact_scores:
                return sum(fact_scores) / len(fact_scores)
            return 0.5
            
        except Exception as e:
            logger.warning(f"AI 모델 사실성 점수 계산 실패: {e}")
            return self._calculate_fact_score_fallback(text)
    
    async def _extract_fact_claims_ai(self, text: str) -> List[str]:
        """AI 모델을 사용하여 사실 주장들을 추출합니다."""
        try:
            claims = []
            
            # 텍스트를 문장 단위로 분리
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]
            
            for sentence in sentences[:5]:
                # 각 문장이 사실 주장인지 판단
                result = self.fact_check_pipeline(
                    sentence,
                    candidate_labels=["factual", "opinion", "speculation"]
                )
                
                label = result[0][0]['label']
                score = result[0][0]['score']
                
                if label == "factual" and score > 0.6:
                    claims.append(f"사실 주장: {sentence[:50]}...")
                elif label == "opinion" and score > 0.6:
                    claims.append(f"의견: {sentence[:50]}...")
                elif label == "speculation" and score > 0.6:
                    claims.append(f"추측: {sentence[:50]}...")
            
            if not claims:
                claims.append("명확한 사실 주장 없음")
            
            return claims
            
        except Exception as e:
            logger.warning(f"AI 모델 사실 주장 추출 실패: {e}")
            return self._extract_fact_claims_fallback(text)
    
    async def _check_verification_status_ai(self, text: str) -> str:
        """AI 모델을 사용하여 검증 상태를 확인합니다."""
        try:
            # 검증 상태 분류
            result = self.fact_check_pipeline(
                text,
                candidate_labels=["verified", "unverified", "uncertain"]
            )
            
            label = result[0][0]['label']
            score = result[0][0]['score']
            
            if score > 0.6:
                if label == "verified":
                    return "검증됨"
                elif label == "unverified":
                    return "미검증"
                else:
                    return "불확실"
            else:
                return "불확실"
                
        except Exception as e:
            logger.warning(f"AI 모델 검증 상태 확인 실패: {e}")
            return self._check_verification_status_fallback(text)
    
    async def _identify_sources_ai(self, text: str) -> List[str]:
        """AI 모델을 사용하여 정보 출처를 식별합니다."""
        try:
            # 출처 유형 분류
            result = self.fact_check_pipeline(
                text,
                candidate_labels=["official", "media", "expert", "research", "unknown"]
            )
            
            sources = []
            for item in result[0]:
                if item['score'] > 0.3:  # 임계값 이상만
                    label = item['label']
                    if label == "official":
                        sources.append("공식 출처")
                    elif label == "media":
                        sources.append("언론매체")
                    elif label == "expert":
                        sources.append("전문가")
                    elif label == "research":
                        sources.append("연구/조사")
                    elif label == "unknown":
                        sources.append("출처 불명")
            
            if not sources:
                sources.append("출처 불명")
            
            return sources
            
        except Exception as e:
            logger.warning(f"AI 모델 출처 식별 실패: {e}")
            return self._identify_sources_fallback(text)
    
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
    
    # 폴백 메서드들 (AI 모델 실패 시 사용)
    def _calculate_fact_score_fallback(self, text: str) -> float:
        """사실성 점수를 계산합니다 (폴백)."""
        # 사실성 지표들
        factual_indicators = [
            "연구", "데이터", "통계", "조사", "보고서", "논문", "전문가",
            "공식", "공식 발표", "확인됨", "검증됨", "사실", "정확한"
        ]
        
        # 의심스러운 지표들
        suspicious_indicators = [
            "소문", "추측", "아마도", "어쩌면", "불확실", "미확인",
            "의심", "혹시", "아마", "추정", "가능성"
        ]
        
        # 극단적 표현들
        extreme_indicators = [
            "절대", "완벽", "최고", "최악", "완전히", "전혀", "100%",
            "완벽하게", "완전하게", "절대적으로"
        ]
        
        factual_count = sum(1 for indicator in factual_indicators if indicator in text)
        suspicious_count = sum(1 for indicator in suspicious_indicators if indicator in text)
        extreme_count = sum(1 for indicator in extreme_indicators if indicator in text)
        
        base_score = 0.5
        factual_bonus = factual_count * 0.1
        suspicious_penalty = suspicious_count * 0.08
        extreme_penalty = extreme_count * 0.05
        
        final_score = base_score + factual_bonus - suspicious_penalty - extreme_penalty
        return max(0.0, min(1.0, final_score))
    
    def _extract_fact_claims_fallback(self, text: str) -> List[str]:
        """사실 주장들을 추출합니다 (폴백)."""
        claims = []
        
        # 숫자 관련 주장
        import re
        number_patterns = [
            r'\d+%',  # 퍼센트
            r'\d+명',  # 명수
            r'\d+개',  # 개수
            r'\d+년',  # 년도
            r'\d+월',  # 월
            r'\d+일'   # 일
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                claims.append(f"수치 주장: {match}")
        
        # 비교 주장
        comparison_words = ["더", "가장", "최고", "최저", "비교", "대비"]
        for word in comparison_words:
            if word in text:
                claims.append(f"비교 주장: '{word}' 포함")
        
        # 시간 관련 주장
        time_words = ["언제", "언제부터", "언제까지", "지금", "현재", "미래", "과거"]
        for word in time_words:
            if word in text:
                claims.append(f"시간 주장: '{word}' 포함")
        
        if not claims:
            claims.append("명확한 사실 주장 없음")
        
        return claims
    
    def _check_verification_status_fallback(self, text: str) -> str:
        """검증 상태를 확인합니다 (폴백)."""
        verified_indicators = ["확인됨", "검증됨", "공식", "공식 발표", "인정됨"]
        unverified_indicators = ["미확인", "검증 안됨", "의심", "소문", "추측"]
        
        verified_count = sum(1 for indicator in verified_indicators if indicator in text)
        unverified_count = sum(1 for indicator in unverified_indicators if indicator in text)
        
        if verified_count > unverified_count:
            return "검증됨"
        elif unverified_count > verified_count:
            return "미검증"
        else:
            return "불확실"
    
    def _identify_sources_fallback(self, text: str) -> List[str]:
        """정보 출처를 식별합니다 (폴백)."""
        sources = []
        
        # 언론사
        media_sources = ["뉴스", "방송", "신문", "잡지", "매체", "언론"]
        for source in media_sources:
            if source in text:
                sources.append(f"언론매체: {source}")
        
        # 전문기관
        institution_sources = ["연구소", "대학", "기관", "협회", "단체", "조직"]
        for source in institution_sources:
            if source in text:
                sources.append(f"전문기관: {source}")
        
        # 개인
        personal_sources = ["전문가", "교수", "연구원", "박사", "의사", "변호사"]
        for source in personal_sources:
            if source in text:
                sources.append(f"전문가: {source}")
        
        # 공식
        official_sources = ["정부", "공식", "공식 발표", "공식 자료", "공식 통계"]
        for source in official_sources:
            if source in text:
                sources.append(f"공식: {source}")
        
        if not sources:
            sources.append("출처 불명")
        
        return sources
    
    async def _analyze_dummy(self, text: str) -> FactCheckAnalysis:
        """더미 로직으로 분석 (폴백)"""
        fact_score = self._calculate_fact_score_fallback(text)
        fact_claims = self._extract_fact_claims_fallback(text)
        verification_status = self._check_verification_status_fallback(text)
        sources = self._identify_sources_fallback(text)
        
        return FactCheckAnalysis(
            fact_check_score=fact_score,
            claim_verification_score=fact_score,
            source_analysis_score=0.6,
            evidence_strength_score=fact_score,
            fact_check_result=verification_status,
            reasoning="더미 로직으로 분석 (AI 모델 로딩 실패)"
        )
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.fact_check_pipeline:
                del self.fact_check_pipeline
            if self.entailment_pipeline:
                del self.entailment_pipeline
            
            # BaseAIModel의 언로드 메서드 사용
            await self.unload_model()
            
            logger.info("사실 확인 모델 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"사실 확인 모델 리소스 정리 실패: {e}")
