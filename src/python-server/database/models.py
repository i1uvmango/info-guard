"""
데이터베이스 모델 정의
SQLAlchemy ORM 모델들
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    analyses = relationship("AnalysisResult", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class AnalysisResult(Base):
    """분석 결과 모델"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 익명 사용자 허용
    video_id = Column(String(20), nullable=False, index=True)
    video_title = Column(String(500), nullable=False)
    video_url = Column(String(500), nullable=False)
    channel_id = Column(String(255), index=True)
    channel_name = Column(String(255))
    
    # 분석 설정
    analysis_types = Column(JSON, nullable=False)  # ["sentiment", "bias", "credibility", "content"]
    include_comments = Column(Boolean, default=True)
    include_subtitles = Column(Boolean, default=True)
    
    # 분석 결과
    results = Column(JSON, nullable=False)  # 각 분석 타입별 결과
    confidence_scores = Column(JSON, nullable=False)  # 각 분석 타입별 신뢰도
    overall_credibility_score = Column(Float, nullable=False)
    
    # 메타데이터
    analysis_time_seconds = Column(Float, nullable=False)
    status = Column(String(50), default="completed", index=True)  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="analyses")
    feedbacks = relationship("Feedback", back_populates="analysis")
    
    # 인덱스
    __table_args__ = (
        Index('idx_video_analysis', 'video_id', 'created_at'),
        Index('idx_user_analysis', 'user_id', 'created_at'),
        Index('idx_credibility_score', 'overall_credibility_score', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, analysis_id='{self.analysis_id}', video_id='{self.video_id}')>"

class Feedback(Base):
    """사용자 피드백 모델"""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 익명 사용자 허용
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=True)
    
    # 피드백 내용
    feedback_type = Column(String(50), nullable=False)  # accuracy, helpfulness, suggestion, bug_report
    rating = Column(Integer)  # 1-5 점수
    comment = Column(Text)
    
    # 메타데이터
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv6 지원
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user = relationship("User", back_populates="feedbacks")
    analysis = relationship("AnalysisResult", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, type='{self.feedback_type}', rating={self.rating})>"

class VideoMetadata(Base):
    """영상 메타데이터 캐시 모델"""
    __tablename__ = "video_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)
    
    # 기본 정보
    title = Column(String(500), nullable=False)
    description = Column(Text)
    channel_id = Column(String(255), index=True)
    channel_name = Column(String(255))
    
    # 통계
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    subscriber_count = Column(Integer, default=0)
    
    # 메타데이터
    duration = Column(String(50))
    published_at = Column(DateTime(timezone=True))
    tags = Column(JSON)
    category_id = Column(String(50))
    
    # 캐시 정보
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    cache_expires_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<VideoMetadata(id={self.id}, video_id='{self.video_id}', title='{self.title}')>"

class AnalysisCache(Base):
    """분석 결과 캐시 모델"""
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    
    # 캐시된 데이터
    cached_data = Column(JSON, nullable=False)
    
    # 캐시 메타데이터
    cache_type = Column(String(50), nullable=False)  # video_info, transcript, comments, analysis_result
    video_id = Column(String(20), index=True)
    
    # 만료 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # 사용 통계
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AnalysisCache(id={self.id}, cache_key='{self.cache_key}', type='{self.cache_type}')>"

class SystemMetrics(Base):
    """시스템 메트릭 모델"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 성능 메트릭
    request_count = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    
    # 리소스 사용량
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    disk_usage = Column(Float, default=0.0)
    
    # AI 모델 메트릭
    model_inference_count = Column(Integer, default=0)
    model_inference_time = Column(Float, default=0.0)
    
    # 데이터베이스 메트릭
    db_connection_count = Column(Integer, default=0)
    db_query_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, timestamp='{self.timestamp}')>"

# Pydantic 모델들 (API 응답용)
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    """사용자 생성 요청 모델"""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=200)

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    """분석 결과 응답 모델"""
    id: int
    analysis_id: str
    video_id: str
    video_title: str
    video_url: str
    channel_name: Optional[str]
    analysis_types: List[str]
    overall_credibility_score: float
    status: str
    analysis_time_seconds: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    """피드백 생성 요청 모델"""
    feedback_type: str = Field(..., regex=r"^(accuracy|helpfulness|suggestion|bug_report)$")
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    """피드백 응답 모델"""
    id: int
    feedback_type: str
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
