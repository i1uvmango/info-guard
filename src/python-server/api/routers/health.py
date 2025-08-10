"""
헬스체크 API 라우터
서버 상태, AI 모델 상태, 데이터베이스 연결 상태를 확인
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import psutil
import time
from datetime import datetime

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# 의존성 함수들
async def get_system_info() -> Dict[str, Any]:
    """시스템 정보 수집"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    except Exception as e:
        logger.error(f"시스템 정보 수집 실패: {e}")
        return {"error": str(e)}

async def get_ai_model_status(request: Request) -> Dict[str, Any]:
    """AI 모델 상태 확인"""
    try:
        # ModelManager에서 실제 모델 상태 가져오기
        if hasattr(request.app.state, 'model_manager'):
            model_manager = request.app.state.model_manager
            models_status = model_manager.get_all_models_status()
            
            return {
                "status": "healthy" if model_manager.are_all_models_ready() else "degraded",
                "models_loaded": models_status,
                "all_models_ready": model_manager.are_all_models_ready(),
                "last_updated": datetime.now().isoformat()
            }
        else:
            # ModelManager가 없는 경우
            return {
                "status": "unknown",
                "models_loaded": {},
                "all_models_ready": False,
                "last_updated": datetime.now().isoformat(),
                "note": "ModelManager not initialized"
            }
    except Exception as e:
        logger.error(f"AI 모델 상태 확인 실패: {e}")
        return {"error": str(e)}

async def get_database_status() -> Dict[str, Any]:
    """데이터베이스 연결 상태 확인"""
    try:
        # TODO: 실제 데이터베이스 연결 상태 확인 로직 구현
        # 현재는 더미 데이터 반환
        return {
            "postgresql": {
                "status": "connected",
                "response_time_ms": 15
            },
            "redis": {
                "status": "connected", 
                "response_time_ms": 5
            },
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"데이터베이스 상태 확인 실패: {e}")
        return {"error": str(e)}

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    기본 헬스체크
    서버가 정상적으로 응답하는지 확인
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Info-Guard AI Server",
        "version": "1.0.0"
    }

@router.get("/status")
async def detailed_status(request: Request) -> Dict[str, Any]:
    """
    상세 상태 확인
    서버, AI 모델, 데이터베이스의 상세 상태 정보
    """
    start_time = time.time()
    
    try:
        # 각 상태 정보 수집
        system_info = await get_system_info()
        ai_model_status = await get_ai_model_status(request)
        database_status = await get_database_status()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": response_time,
            "system": system_info,
            "ai_models": ai_model_status,
            "database": database_status,
            "service": "Info-Guard AI Server",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"상세 상태 확인 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"상태 확인 중 오류 발생: {str(e)}"
        )

@router.get("/ready")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    준비 상태 확인 (Kubernetes Readiness Probe)
    서비스가 요청을 처리할 준비가 되었는지 확인
    """
    try:
        # AI 모델 상태 확인
        ai_status = await get_ai_model_status(request)
        if "error" in ai_status:
            raise HTTPException(
                status_code=503,
                detail="AI 모델이 준비되지 않았습니다"
            )
        
        # 데이터베이스 상태 확인
        db_status = await get_database_status()
        if "error" in db_status:
            raise HTTPException(
                status_code=503,
                detail="데이터베이스 연결이 준비되지 않았습니다"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "service": "Info-Guard AI Server"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"준비 상태 확인 실패: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"준비 상태 확인 중 오류 발생: {str(e)}"
        )

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    생존 상태 확인 (Kubernetes Liveness Probe)
    서비스가 정상적으로 동작하고 있는지 확인
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "service": "Info-Guard AI Server"
    }

@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    메트릭 정보
    성능 및 리소스 사용량 메트릭
    """
    try:
        system_info = await get_system_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "system": system_info,
                "requests": {
                    "total_requests": 0,  # TODO: 실제 요청 수 카운터 구현
                    "successful_requests": 0,
                    "failed_requests": 0
                },
                "ai_analysis": {
                    "total_analyses": 0,  # TODO: 실제 분석 수 카운터 구현
                    "average_response_time_ms": 0
                }
            }
        }
    except Exception as e:
        logger.error(f"메트릭 수집 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"메트릭 수집 중 오류 발생: {str(e)}"
        )
