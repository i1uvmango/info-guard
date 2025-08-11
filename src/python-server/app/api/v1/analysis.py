"""
분석 API 엔드포인트
콘텐츠 분석을 위한 API를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import asyncio

from app.services.ai_models import get_ai_model_service, AIModelService
from app.services.batch_processor import get_batch_processor, BatchProcessor
from app.models.analysis import (
    AnalysisRequest, 
    AnalysisResult, 
    AnalysisStatus,
    AnalysisType
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_content(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    ai_service: AIModelService = Depends(get_ai_model_service)
) -> Dict[str, Any]:
    """콘텐츠를 분석합니다."""
    try:
        logger.info(f"콘텐츠 분석 요청: {request.analysis_type}")
        
        # AI 모델 서비스로 분석 수행
        result = await ai_service.analyze_content(
            text=request.text,
            video_metadata=request.video_metadata,
            analysis_type=request.analysis_type
        )
        
        return {
            "status": "success",
            "data": result.dict(),
            "message": "분석이 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"콘텐츠 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")


@router.post("/analyze/batch", response_model=Dict[str, Any])
async def analyze_content_batch(
    request: AnalysisRequest,
    priority: int = 1,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """콘텐츠를 배치로 분석합니다."""
    try:
        logger.info(f"배치 분석 요청: {request.analysis_type} (우선순위: {priority})")
        
        # 배치 처리기에 요청 추가
        request_id = await batch_processor.add_request(
            text=request.text,
            analysis_type=request.analysis_type,
            priority=priority,
            metadata={
                "video_metadata": request.video_metadata,
                "user_id": getattr(request, 'user_id', None)
            }
        )
        
        return {
            "status": "success",
            "data": {
                "request_id": request_id,
                "status": "pending",
                "message": "배치 분석 요청이 등록되었습니다."
            },
            "message": "배치 분석이 시작되었습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 분석 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=f"배치 분석 요청 중 오류가 발생했습니다: {str(e)}")


@router.get("/batch/{request_id}", response_model=Dict[str, Any])
async def get_batch_result(
    request_id: str,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 분석 결과를 조회합니다."""
    try:
        logger.info(f"배치 분석 결과 조회: {request_id}")
        
        # 배치 처리기에서 결과 조회
        result = await batch_processor.get_result(request_id, timeout=1.0)
        
        if result is None:
            # 아직 처리 중이거나 존재하지 않는 요청
            status = batch_processor.get_status()
            return {
                "status": "pending",
                "data": {
                    "request_id": request_id,
                    "status": "processing",
                    "message": "분석이 진행 중입니다."
                },
                "batch_status": status
            }
        
        if result.status == "completed":
            return {
                "status": "success",
                "data": {
                    "request_id": request_id,
                    "status": "completed",
                    "result": result.result.dict() if result.result else None,
                    "processing_time": result.processing_time,
                    "message": "분석이 완료되었습니다."
                }
            }
        elif result.status == "failed":
            return {
                "status": "error",
                "data": {
                    "request_id": request_id,
                    "status": "failed",
                    "error": result.error,
                    "message": "분석 중 오류가 발생했습니다."
                }
            }
        else:
            return {
                "status": "pending",
                "data": {
                    "request_id": request_id,
                    "status": result.status,
                    "message": "분석이 진행 중입니다."
                }
            }
        
    except Exception as e:
        logger.error(f"배치 분석 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"결과 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/analyze/batch/multiple", response_model=Dict[str, Any])
async def analyze_multiple_contents(
    requests: List[AnalysisRequest],
    priority: int = 1,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """여러 콘텐츠를 배치로 분석합니다."""
    try:
        logger.info(f"다중 배치 분석 요청: {len(requests)}개 (우선순위: {priority})")
        
        if len(requests) > 100:  # 최대 100개 요청 제한
            raise HTTPException(status_code=400, detail="최대 100개 요청까지만 처리할 수 있습니다.")
        
        # 모든 요청을 배치 처리기에 추가
        request_ids = []
        for i, request in enumerate(requests):
            request_id = await batch_processor.add_request(
                text=request.text,
                analysis_type=request.analysis_type,
                priority=priority,
                metadata={
                    "video_metadata": request.video_metadata,
                    "user_id": getattr(request, 'user_id', None),
                    "batch_index": i
                }
            )
            request_ids.append(request_id)
        
        return {
            "status": "success",
            "data": {
                "request_ids": request_ids,
                "total_requests": len(requests),
                "status": "pending",
                "message": f"{len(requests)}개 배치 분석 요청이 등록되었습니다."
            },
            "message": "다중 배치 분석이 시작되었습니다."
        }
        
    except Exception as e:
        logger.error(f"다중 배치 분석 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=f"다중 배치 분석 요청 중 오류가 발생했습니다: {str(e)}")


@router.get("/batch/status", response_model=Dict[str, Any])
async def get_batch_status(
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 처리기 상태를 조회합니다."""
    try:
        status = batch_processor.get_status()
        
        return {
            "status": "success",
            "data": status,
            "message": "배치 처리기 상태를 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/batch/stop", response_model=Dict[str, Any])
async def stop_batch_processing(
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 처리를 중지합니다."""
    try:
        await batch_processor.stop()
        
        return {
            "status": "success",
            "data": {"message": "배치 처리가 중지되었습니다."},
            "message": "배치 처리를 중지했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 처리 중지 실패: {e}")
        raise HTTPException(status_code=500, detail=f"배치 처리 중지 중 오류가 발생했습니다: {str(e)}")


@router.post("/batch/clear", response_model=Dict[str, Any])
async def clear_batch_results(
    max_age_hours: int = 24,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """오래된 배치 결과를 정리합니다."""
    try:
        await batch_processor.clear_completed_results(max_age_hours)
        
        return {
            "status": "success",
            "data": {"message": f"{max_age_hours}시간 이상 된 결과가 정리되었습니다."},
            "message": "배치 결과를 정리했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 결과 정리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"배치 결과 정리 중 오류가 발생했습니다: {str(e)}")


@router.get("/batch/metrics", response_model=Dict[str, Any])
async def get_batch_metrics(
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 처리 메트릭을 조회합니다."""
    try:
        metrics = batch_processor.get_metrics()
        
        return {
            "status": "success",
            "data": {
                "total_requests": metrics.total_requests,
                "total_processed": metrics.total_processed,
                "total_failed": metrics.total_failed,
                "total_cancelled": metrics.total_cancelled,
                "average_processing_time": round(metrics.average_processing_time, 3),
                "average_wait_time": round(metrics.average_wait_time, 3),
                "throughput_per_minute": round(metrics.throughput_per_minute, 1),
                "success_rate": round(metrics.success_rate, 1),
                "gpu_utilization": round(metrics.gpu_utilization, 1),
                "memory_usage": round(metrics.memory_usage, 1)
            },
            "message": "배치 처리 메트릭을 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/batch/performance", response_model=Dict[str, Any])
async def get_batch_performance(
    limit: int = 100,
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 처리 성능 히스토리를 조회합니다."""
    try:
        performance_history = batch_processor.get_performance_history(limit)
        batch_history = batch_processor.get_batch_history(50)
        
        return {
            "status": "success",
            "data": {
                "performance_history": performance_history,
                "batch_history": batch_history,
                "total_records": len(performance_history)
            },
            "message": "배치 처리 성능 히스토리를 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 성능 히스토리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/batch/metrics/reset", response_model=Dict[str, Any])
async def reset_batch_metrics(
    batch_processor: BatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """배치 처리 메트릭을 초기화합니다."""
    try:
        await batch_processor.reset_metrics()
        
        return {
            "status": "success",
            "data": {"message": "배치 처리 메트릭이 초기화되었습니다."},
            "message": "배치 처리 메트릭을 초기화했습니다."
        }
        
    except Exception as e:
        logger.error(f"배치 메트릭 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 초기화 중 오류가 발생했습니다: {str(e)}")


@router.get("/models/status", response_model=Dict[str, Any])
async def get_models_status(
    ai_service: AIModelService = Depends(get_ai_model_service)
) -> Dict[str, Any]:
    """AI 모델들의 상태를 조회합니다."""
    try:
        status = await ai_service.get_model_status()
        
        return {
            "status": "success",
            "data": status,
            "message": "AI 모델 상태를 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"모델 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/models/reload", response_model=Dict[str, Any])
async def reload_models(
    ai_service: AIModelService = Depends(get_ai_model_service)
) -> Dict[str, Any]:
    """AI 모델들을 다시 로드합니다."""
    try:
        results = await ai_service.reload_models()
        
        return {
            "status": "success",
            "data": results,
            "message": "AI 모델 리로드가 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"모델 리로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 리로드 중 오류가 발생했습니다: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """분석 서비스 상태를 확인합니다."""
    return {
        "status": "healthy",
        "service": "content-analysis",
        "timestamp": "2024-01-01T00:00:00Z"
    }
