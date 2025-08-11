"""
공통 데이터 모델
여러 모듈에서 공통으로 사용되는 데이터 구조를 정의합니다.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="에러 메시지")
    error_code: str = Field(..., description="에러 코드")
    timestamp: datetime = Field(..., description="에러 발생 시간")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 에러 정보")
    request_id: Optional[str] = Field(None, description="요청 ID")


class SuccessResponse(BaseModel):
    """성공 응답 모델"""
    message: str = Field(..., description="성공 메시지")
    timestamp: datetime = Field(..., description="응답 시간")
    data: Optional[Any] = Field(None, description="응답 데이터")


class PaginationParams(BaseModel):
    """페이지네이션 매개변수 모델"""
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    sort_by: Optional[str] = Field(None, description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서 (asc/desc)")


class PaginatedResponse(BaseModel):
    """페이지네이션 응답 모델"""
    items: List[Any] = Field(..., description="아이템 목록")
    total: int = Field(..., description="전체 아이템 수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")


class HealthCheck(BaseModel):
    """헬스 체크 모델"""
    status: str = Field(..., description="서비스 상태")
    timestamp: datetime = Field(..., description="체크 시간")
    version: str = Field(..., description="서비스 버전")
    uptime: Optional[float] = Field(None, description="가동 시간 (초)")


class DetailedHealthCheck(HealthCheck):
    """상세 헬스 체크 모델"""
    components: Dict[str, Dict[str, Any]] = Field(..., description="컴포넌트별 상태")
    dependencies: Dict[str, Dict[str, Any]] = Field(..., description="의존성 상태")


class ReadinessCheck(BaseModel):
    """준비 상태 체크 모델"""
    status: str = Field(..., description="준비 상태")
    timestamp: datetime = Field(..., description="체크 시간")
    checks: Dict[str, bool] = Field(..., description="각 체크 항목별 상태")
    message: Optional[str] = Field(None, description="상태 메시지")


class WebSocketMessage(BaseModel):
    """WebSocket 메시지 모델"""
    type: str = Field(..., description="메시지 타입")
    data: Dict[str, Any] = Field(..., description="메시지 데이터")
    timestamp: datetime = Field(..., description="메시지 시간")
    user_id: Optional[str] = Field(None, description="사용자 ID")


class AnalysisProgressMessage(WebSocketMessage):
    """분석 진행 상황 메시지 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    progress: float = Field(..., ge=0.0, le=100.0, description="진행률 (%)")
    current_step: str = Field(..., description="현재 단계")
    estimated_completion: Optional[datetime] = Field(None, description="예상 완료 시간")


class AnalysisCompleteMessage(WebSocketMessage):
    """분석 완료 메시지 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    result_url: str = Field(..., description="결과 조회 URL")
    summary: Optional[str] = Field(None, description="분석 요약")


class AnalysisErrorMessage(WebSocketMessage):
    """분석 에러 메시지 모델"""
    analysis_id: str = Field(..., description="분석 ID")
    error: str = Field(..., description="에러 메시지")
    error_code: str = Field(..., description="에러 코드")
    retry_available: bool = Field(..., description="재시도 가능 여부")


class CacheEntry(BaseModel):
    """캐시 엔트리 모델"""
    key: str = Field(..., description="캐시 키")
    value: Any = Field(..., description="캐시 값")
    created_at: datetime = Field(..., description="생성 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")
    ttl: Optional[int] = Field(None, description="TTL (초)")
    access_count: int = Field(0, description="접근 횟수")
    last_accessed: datetime = Field(..., description="마지막 접근 시간")


class RateLimitInfo(BaseModel):
    """Rate Limit 정보 모델"""
    limit: int = Field(..., description="제한 횟수")
    remaining: int = Field(..., description="남은 횟수")
    reset_time: datetime = Field(..., description="초기화 시간")
    retry_after: Optional[int] = Field(None, description="재시도 대기 시간 (초)")


class UserContext(BaseModel):
    """사용자 컨텍스트 모델"""
    user_id: str = Field(..., description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    permissions: List[str] = Field(default_factory=list, description="권한 목록")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="사용자 설정")
    created_at: datetime = Field(..., description="생성 시간")
    last_active: datetime = Field(..., description="마지막 활동 시간")


class APIRequestLog(BaseModel):
    """API 요청 로그 모델"""
    request_id: str = Field(..., description="요청 ID")
    method: str = Field(..., description="HTTP 메서드")
    path: str = Field(..., description="요청 경로")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="User Agent")
    request_time: datetime = Field(..., description="요청 시간")
    response_time: Optional[float] = Field(None, description="응답 시간 (초)")
    status_code: Optional[int] = Field(None, description="HTTP 상태 코드")
    error: Optional[str] = Field(None, description="에러 메시지")


class SystemMetrics(BaseModel):
    """시스템 메트릭 모델"""
    timestamp: datetime = Field(..., description="수집 시간")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU 사용률 (%)")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="메모리 사용률 (%)")
    gpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="GPU 사용률 (%)")
    gpu_memory_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="GPU 메모리 사용률 (%)")
    disk_usage: float = Field(..., ge=0.0, le=100.0, description="디스크 사용률 (%)")
    network_io: Dict[str, float] = Field(default_factory=dict, description="네트워크 I/O")
    active_connections: int = Field(..., description="활성 연결 수")
    queue_size: int = Field(..., description="대기열 크기")
