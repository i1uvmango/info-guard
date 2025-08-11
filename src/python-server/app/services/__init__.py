"""
서비스 모듈 초기화
모든 서비스를 통합하고 관리합니다.
"""

from .cache import CacheService, cache_service
from .ai_models import AIModelService, ai_model_service
from .youtube import YouTubeService
from .analysis import AnalysisService

__all__ = [
    "CacheService",
    "cache_service",
    "AIModelService", 
    "ai_model_service",
    "YouTubeService",
    "AnalysisService"
]


async def initialize_services():
    """모든 서비스를 초기화합니다."""
    try:
        # 캐시 서비스 연결
        await cache_service.connect()
        
        # AI 모델 서비스는 이미 초기화됨
        
        return True
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"서비스 초기화 실패: {e}")
        return False


async def cleanup_services():
    """모든 서비스를 정리합니다."""
    try:
        # 캐시 서비스 연결 해제
        await cache_service.disconnect()
        
        # AI 모델 서비스 정리
        await ai_model_service.cleanup()
        
        return True
    except Exception as e:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"서비스 정리 실패: {e}")
        return False
