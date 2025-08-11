"""
헬스체크 API 모듈
서버 상태 및 시스템 정보를 제공합니다.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger(__name__)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    기본 헬스체크 엔드포인트
    
    Returns:
        서버 상태 정보
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production"
        }
    except Exception as e:
        logger.error(f"헬스체크 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 상태 확인 실패")


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    상세 헬스체크 엔드포인트
    
    Returns:
        상세한 서버 및 시스템 상태 정보
    """
    try:
        # 기본 상태 정보
        health_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "server": {
                "host": settings.HOST,
                "port": settings.PORT,
                "workers": settings.WORKERS
            },
            "features": {
                "gpu_enabled": settings.USE_GPU,
                "youtube_api": bool(settings.YOUTUBE_API_KEY),
                "database": bool(settings.DATABASE_URL),
                "redis": bool(settings.REDIS_URL)
            }
        }
        
        logger.info("상세 헬스체크 완료")
        return health_info
        
    except Exception as e:
        logger.error(f"상세 헬스체크 오류: {e}")
        raise HTTPException(status_code=500, detail="상세 상태 확인 실패")


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    서비스 준비 상태 확인
    
    Returns:
        서비스 준비 상태
    """
    try:
        # 여기에 실제 서비스 준비 상태 확인 로직 추가
        # 예: 데이터베이스 연결, AI 모델 로드 등
        
        ready = True
        checks = {
            "database": ready,  # 실제 DB 연결 확인 필요
            "ai_models": ready,  # 실제 모델 로드 확인 필요
            "youtube_api": bool(settings.YOUTUBE_API_KEY)
        }
        
        overall_status = "ready" if all(checks.values()) else "not_ready"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
        
    except Exception as e:
        logger.error(f"준비 상태 확인 오류: {e}")
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
