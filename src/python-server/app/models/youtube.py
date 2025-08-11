"""
YouTube 관련 데이터 모델
YouTube API 연동 및 영상 정보 처리를 위한 데이터 구조를 정의합니다.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class YouTubeVideoInfo(BaseModel):
    """YouTube 영상 기본 정보 모델"""
    video_id: str = Field(..., description="YouTube 영상 ID")
    title: str = Field(..., description="영상 제목")
    description: str = Field(..., description="영상 설명")
    channel_id: str = Field(..., description="채널 ID")
    channel_title: str = Field(..., description="채널명")
    published_at: datetime = Field(..., description="업로드 시간")
    duration: str = Field(..., description="영상 길이 (ISO 8601)")
    view_count: int = Field(..., description="조회수")
    like_count: Optional[int] = Field(None, description="좋아요 수")
    dislike_count: Optional[int] = Field(None, description="싫어요 수")
    comment_count: Optional[int] = Field(None, description="댓글 수")
    
    # 메타데이터
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    category_id: str = Field(..., description="카테고리 ID")
    category_title: str = Field(..., description="카테고리명")
    language: Optional[str] = Field(None, description="언어")
    region_restriction: Optional[str] = Field(None, description="지역 제한")
    
    # 썸네일 정보
    thumbnails: Dict[str, Dict[str, Any]] = Field(..., description="썸네일 정보")
    
    # 추가 정보
    live_broadcast_content: str = Field(..., description="라이브 방송 여부")
    default_audio_language: Optional[str] = Field(None, description="기본 오디오 언어")
    default_language: Optional[str] = Field(None, description="기본 언어")


class YouTubeTranscript(BaseModel):
    """YouTube 자막 정보 모델"""
    language: str = Field(..., description="자막 언어")
    is_auto_generated: bool = Field(..., description="자동 생성 여부")
    segments: List[Dict[str, Any]] = Field(..., description="자막 세그먼트")
    full_text: str = Field(..., description="전체 자막 텍스트")


class YouTubeComment(BaseModel):
    """YouTube 댓글 모델"""
    comment_id: str = Field(..., description="댓글 ID")
    author_name: str = Field(..., description="작성자명")
    author_channel_id: Optional[str] = Field(None, description="작성자 채널 ID")
    text: str = Field(..., description="댓글 내용")
    published_at: datetime = Field(..., description="작성 시간")
    like_count: int = Field(..., description="좋아요 수")
    reply_count: int = Field(..., description="답글 수")
    is_author_channel_owner: bool = Field(..., description="채널 소유자 여부")


class YouTubeChannelInfo(BaseModel):
    """YouTube 채널 정보 모델"""
    channel_id: str = Field(..., description="채널 ID")
    title: str = Field(..., description="채널명")
    description: str = Field(..., description="채널 설명")
    custom_url: Optional[str] = Field(None, description="사용자 정의 URL")
    published_at: datetime = Field(..., description="채널 생성 시간")
    subscriber_count: Optional[int] = Field(None, description="구독자 수")
    video_count: int = Field(..., description="영상 수")
    view_count: Optional[int] = Field(None, description="총 조회수")
    
    # 채널 통계
    country: Optional[str] = Field(None, description="국가")
    language: Optional[str] = Field(None, description="언어")
    topic_categories: List[str] = Field(default_factory=list, description="주제 카테고리")
    
    # 브랜딩
    thumbnails: Dict[str, Dict[str, Any]] = Field(..., description="채널 썸네일")
    banner_external_url: Optional[str] = Field(None, description="배너 이미지 URL")


class YouTubeSearchResult(BaseModel):
    """YouTube 검색 결과 모델"""
    video_id: str = Field(..., description="영상 ID")
    title: str = Field(..., description="제목")
    description: str = Field(..., description="설명")
    channel_title: str = Field(..., description="채널명")
    published_at: datetime = Field(..., description="업로드 시간")
    thumbnails: Dict[str, Dict[str, Any]] = Field(..., description="썸네일")
    duration: Optional[str] = Field(None, description="영상 길이")
    view_count: Optional[int] = Field(None, description="조회수")
    relevance_score: Optional[float] = Field(None, description="관련성 점수")


class YouTubeAPIQuota(BaseModel):
    """YouTube API 할당량 정보 모델"""
    quota_used: int = Field(..., description="사용된 할당량")
    quota_limit: int = Field(..., description="총 할당량")
    quota_remaining: int = Field(..., description="남은 할당량")
    reset_time: Optional[datetime] = Field(None, description="할당량 초기화 시간")
    cost_per_request: Dict[str, int] = Field(default_factory=dict, description="요청별 비용")


class YouTubeVideoMetadata(BaseModel):
    """YouTube 영상 메타데이터 모델 (분석용)"""
    video_id: str = Field(..., description="영상 ID")
    url: HttpUrl = Field(..., description="영상 URL")
    
    # 기본 정보
    title: str = Field(..., description="제목")
    description: str = Field(..., description="설명")
    channel_info: YouTubeChannelInfo = Field(..., description="채널 정보")
    
    # 콘텐츠 정보
    duration_seconds: int = Field(..., description="영상 길이 (초)")
    category: str = Field(..., description="카테고리")
    tags: List[str] = Field(..., description="태그")
    
    # 통계 정보
    view_count: int = Field(..., description="조회수")
    like_ratio: Optional[float] = Field(None, description="좋아요 비율")
    engagement_rate: Optional[float] = Field(None, description="참여율")
    
    # 자막 정보
    transcript: Optional[YouTubeTranscript] = Field(None, description="자막")
    
    # 댓글 정보
    comments: List[YouTubeComment] = Field(default_factory=list, description="댓글")
    comment_sentiment: Optional[Dict[str, float]] = Field(None, description="댓글 감정 분석")
    
    # 수집 시간
    collected_at: datetime = Field(..., description="수집 시간")
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")
