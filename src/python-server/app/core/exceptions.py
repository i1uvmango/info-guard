"""
커스텀 예외 클래스 모듈
애플리케이션의 에러 처리를 체계화합니다.
"""

from typing import Any, Dict, Optional


class InfoGuardException(Exception):
    """Info-Guard 애플리케이션의 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(InfoGuardException):
    """설정 관련 오류"""
    pass


class DatabaseError(InfoGuardException):
    """데이터베이스 관련 오류"""
    pass


class YouTubeAPIError(InfoGuardException):
    """YouTube API 관련 오류"""
    pass


class AIModelError(InfoGuardException):
    """AI 모델 관련 오류"""
    pass


class AnalysisError(InfoGuardException):
    """분석 처리 관련 오류"""
    pass


class ValidationError(InfoGuardException):
    """데이터 검증 오류"""
    pass


class AuthenticationError(InfoGuardException):
    """인증 관련 오류"""
    pass


class RateLimitError(InfoGuardException):
    """API 요청 제한 오류"""
    pass


class ResourceNotFoundError(InfoGuardException):
    """리소스를 찾을 수 없는 오류"""
    pass


class ServiceUnavailableError(InfoGuardException):
    """서비스 사용 불가 오류"""
    pass


# HTTP 상태 코드와 매핑되는 예외들
HTTP_EXCEPTION_MAP = {
    400: ValidationError,
    401: AuthenticationError,
    404: ResourceNotFoundError,
    429: RateLimitError,
    500: ServiceUnavailableError,
    503: ServiceUnavailableError,
}


def get_exception_class(status_code: int) -> type:
    """
    HTTP 상태 코드에 해당하는 예외 클래스를 반환합니다.
    
    Args:
        status_code: HTTP 상태 코드
    
    Returns:
        해당하는 예외 클래스
    """
    return HTTP_EXCEPTION_MAP.get(status_code, InfoGuardException)
