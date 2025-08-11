"""
분석 관련 데이터 모델
YouTube 영상 분석을 위한 모든 데이터 구조를 정의합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class AnalysisType(str, Enum):
    """분석 타입 열거형"""
    CREDIBILITY = "credibility"      # 신뢰도 분석
    SENTIMENT = "sentiment"          # 감정 분석
    BIAS = "bias"                    # 편향 감지
    CLASSIFICATION = "classification" # 콘텐츠 분류
    COMPREHENSIVE = "comprehensive"  # 종합 분석


class AnalysisStatus(str, Enum):
    """분석 상태 열거형"""
    PENDING = "pending"      # 대기 중
    PROCESSING = "processing" # 처리 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패
    CANCELLED = "cancelled"  # 취소됨


class CredibilityScore(BaseModel):
    """신뢰도 점수 모델"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="전체 신뢰도 점수 (0-1)")
    fact_check_score: float = Field(..., ge=0.0, le=1.0, description="사실 확인 점수")
    source_reliability: float = Field(..., ge=0.0, le=1.0, description="출처 신뢰도")
    bias_indicator: float = Field(..., ge=0.0, le=1.0, description="편향 지표")
    confidence: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")
    reasoning: str = Field(..., description="분석 근거")


class SentimentAnalysis(BaseModel):
    """감정 분석 결과 모델"""
    overall_sentiment: float = Field(..., ge=-1.0, le=1.0, description="전체 감정 점수 (-1 ~ 1)")
    dominant_emotion: str = Field(..., description="주요 감정")
    emotion_breakdown: Dict[str, float] = Field(default_factory=dict, description="감정별 세부 분석")
    confidence: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")
    reasoning: str = Field(..., description="분석 근거")


class BiasAnalysis(BaseModel):
    """편향성 분석 결과 모델"""
    has_bias: bool = Field(..., description="편향성 존재 여부")
    bias_types: List[str] = Field(default_factory=list, description="편향성 유형")
    bias_score: float = Field(..., ge=0.0, le=1.0, description="전체 편향성 점수")
    political_bias: float = Field(..., ge=0.0, le=1.0, description="정치적 편향 점수")
    gender_bias: float = Field(..., ge=0.0, le=1.0, description="성별 편향 점수")
    racial_bias: float = Field(..., ge=0.0, le=1.0, description="인종 편향 점수")
    religious_bias: float = Field(..., ge=0.0, le=1.0, description="종교적 편향 점수")
    other_biases: Dict[str, float] = Field(default_factory=dict, description="기타 편향 점수")
    reasoning: str = Field(..., description="분석 근거")


class ContentClassification(BaseModel):
    """콘텐츠 분류 결과 모델"""
    primary_category: str = Field(..., description="주요 카테고리")
    primary_confidence: float = Field(..., ge=0.0, le=1.0, description="주요 카테고리 신뢰도")
    all_categories: Dict[str, float] = Field(default_factory=dict, description="모든 카테고리와 신뢰도")
    content_type: str = Field(..., description="콘텐츠 유형")
    topic: str = Field(..., description="주제")
    target_audience: str = Field(..., description="대상 청중")
    reasoning: str = Field(..., description="분류 근거")


class CredibilityAnalysis(BaseModel):
    """신뢰도 분석 결과 모델"""
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="전체 신뢰도 점수")
    fact_check_score: float = Field(..., ge=0.0, le=1.0, description="사실 확인 점수")
    source_reliability_score: float = Field(..., ge=0.0, le=1.0, description="출처 신뢰도 점수")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="일관성 점수")
    objectivity_score: float = Field(..., ge=0.0, le=1.0, description="객관성 점수")
    credibility_level: str = Field(..., description="신뢰도 레벨")
    reasoning: str = Field(..., description="분석 근거")


class FactCheckAnalysis(BaseModel):
    """팩트 체크 분석 결과 모델"""
    fact_check_score: float = Field(..., ge=0.0, le=1.0, description="전체 팩트 체크 점수")
    claim_verification_score: float = Field(..., ge=0.0, le=1.0, description="주장 검증 점수")
    source_analysis_score: float = Field(..., ge=0.0, le=1.0, description="출처 분석 점수")
    evidence_strength_score: float = Field(..., ge=0.0, le=1.0, description="증거 강도 점수")
    fact_check_result: str = Field(..., description="팩트 체크 결과")
    reasoning: str = Field(..., description="분석 근거")


class FactCheckResult(BaseModel):
    """사실 확인 결과 모델"""
    overall_fact_score: float = Field(..., ge=0.0, le=1.0, description="전체 사실성 점수")
    fact_claims: List[str] = Field(default_factory=list, description="사실 주장들")
    verification_status: str = Field(..., description="검증 상태")
    sources: List[str] = Field(default_factory=list, description="정보 출처")
    confidence: float = Field(..., ge=0.0, le=1.0, description="분석 신뢰도")
    reasoning: str = Field(..., description="분석 근거")


class AnalysisMetadata(BaseModel):
    """분석 메타데이터 모델"""
    analysis_type: str = Field(..., description="분석 타입")
    processing_time: float = Field(..., description="처리 시간 (초)")
    started_at: datetime = Field(..., description="시작 시간")
    completed_at: datetime = Field(..., description="완료 시간")
    video_metadata: Optional[Dict[str, Any]] = Field(None, description="비디오 메타데이터")
    model_version: str = Field("1.0.0", description="사용된 AI 모델 버전")


class BiasDetection(BaseModel):
    """편향 감지 결과 모델"""
    political_bias: Optional[str] = Field(None, description="정치적 편향")
    gender_bias: Optional[str] = Field(None, description="성별 편향")
    racial_bias: Optional[str] = Field(None, description="인종 편향")
    religious_bias: Optional[str] = Field(None, description="종교적 편향")
    bias_score: float = Field(..., ge=0.0, le=1.0, description="전체 편향 점수")
    bias_details: List[str] = Field(default_factory=list, description="편향 상세 내용")


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    video_url: HttpUrl = Field(..., description="YouTube 영상 URL")
    analysis_type: AnalysisType = Field(..., description="분석 타입")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    priority: Optional[str] = Field("normal", description="우선순위")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="사용자 정의 매개변수")


class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    status: AnalysisStatus = Field(..., description="분석 상태")
    message: str = Field(..., description="상태 메시지")
    timestamp: datetime = Field(..., description="요청 시간")
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료 시간")


class AnalysisStatus(BaseModel):
    """분석 상태 조회 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    status: AnalysisStatus = Field(..., description="현재 상태")
    progress: float = Field(..., ge=0.0, le=100.0, description="진행률 (%)")
    current_step: str = Field(..., description="현재 단계")
    message: str = Field(..., description="상태 메시지")
    timestamp: datetime = Field(..., description="업데이트 시간")
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료 시간")


class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    video_url: HttpUrl = Field(..., description="분석된 영상 URL")
    analysis_type: AnalysisType = Field(..., description="분석 타입")
    status: AnalysisStatus = Field(..., description="최종 상태")
    
    # 분석 결과들
    credibility: Optional[CredibilityAnalysis] = Field(None, description="신뢰도 분석 결과")
    sentiment: Optional[SentimentAnalysis] = Field(None, description="감정 분석 결과")
    bias: Optional[BiasAnalysis] = Field(None, description="편향성 분석 결과")
    classification: Optional[ContentClassification] = Field(None, description="콘텐츠 분류 결과")
    fact_check: Optional[FactCheckAnalysis] = Field(None, description="사실 확인 결과")
    
    # 메타데이터
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    model_version: str = Field(..., description="사용된 AI 모델 버전")
    
    # 추가 정보
    summary: Optional[str] = Field(None, description="분석 요약")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")
    warnings: List[str] = Field(default_factory=list, description="주의사항")


class BatchAnalysisRequest(BaseModel):
    """배치 분석 요청 모델"""
    video_urls: List[HttpUrl] = Field(..., min_items=1, max_items=10, description="분석할 영상 URL 목록")
    analysis_type: AnalysisType = Field(..., description="분석 타입")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    priority: Optional[str] = Field("normal", description="우선순위")


class BatchAnalysisResponse(BaseModel):
    """배치 분석 응답 모델"""
    batch_id: str = Field(..., description="배치 분석 ID")
    total_videos: int = Field(..., description="총 영상 수")
    accepted_videos: int = Field(..., description="수락된 영상 수")
    rejected_videos: int = Field(..., description="거부된 영상 수")
    analysis_ids: List[str] = Field(..., description="개별 분석 ID 목록")
    timestamp: datetime = Field(..., description="요청 시간")
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료 시간")
