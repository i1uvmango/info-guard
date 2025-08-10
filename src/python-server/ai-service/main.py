"""
Info-Guard AI Service
FastAPI 기반 AI 분석 서비스
"""

import asyncio
import time
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config.settings import settings
from config.logging_config import get_logger
from services.analysis_service import AnalysisService
from services.youtube_service import YouTubeService
from services.realtime_service import RealtimeAnalysisService
from services.feedback_service import FeedbackService, UserFeedback
from services.channel_service import ChannelService, VideoAnalysis
from services.report_service import ReportService
from models.multitask_credibility_model import MultiTaskCredibilityModel
from services.trained_analysis_service import trained_analysis_service

# 로거 설정
logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="YouTube 영상 신뢰도 분석 AI 서비스",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Pydantic 모델들
class VideoAnalysisRequest(BaseModel):
    video_id: Optional[str] = Field(None, description="YouTube 비디오 ID")
    video_url: Optional[str] = Field(None, description="YouTube 비디오 URL")
    transcript: Optional[str] = Field(None, description="비디오 자막 텍스트")
    metadata: Optional[Dict[str, Any]] = Field(None, description="비디오 메타데이터")
    channel_info: Optional[Dict[str, Any]] = Field(None, description="채널 정보")

class AnalysisResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    model_version: str = "1.0.0"
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    models_loaded: bool

# 전역 변수
analysis_service = None
youtube_service = None
realtime_service = None
feedback_service = None
channel_service = None
report_service = None
credibility_model = None
models_loaded = False

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global analysis_service, youtube_service, realtime_service, feedback_service, channel_service, report_service, credibility_model, models_loaded
    
    logger.info("Info-Guard AI Service 시작 중...")
    
    try:
        # 멀티태스크 신뢰도 모델 로드
        credibility_model = MultiTaskCredibilityModel()
        logger.info("멀티태스크 신뢰도 모델 로드 완료")
        
        # 서비스 초기화
        analysis_service = AnalysisService()
        youtube_service = YouTubeService()
        realtime_service = RealtimeAnalysisService()
        feedback_service = FeedbackService()
        channel_service = ChannelService()
        report_service = ReportService()
        
        # 모델 로드 확인
        models_loaded = True
        logger.info("모든 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        models_loaded = False

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    logger.info("Info-Guard AI Service 종료 중...")

@app.get("/", response_model=Dict[str, str])
async def root():
    """루트 엔드포인트"""
    return {
        "name": "Info-Guard AI Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    import psutil
    
    return HealthResponse(
        status="healthy" if models_loaded else "unhealthy",
        version="1.0.0",
        uptime=time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        models_loaded=models_loaded
    )

@app.get("/metrics")
async def get_metrics():
    """성능 메트릭 엔드포인트"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "models_loaded": models_loaded,
        "uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    request: VideoAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    YouTube 비디오 신뢰도 분석 (학습된 모델 사용)
    
    Args:
        request: 분석 요청 데이터
        background_tasks: 백그라운드 작업
        
    Returns:
        AnalysisResponse: 분석 결과
    """
    if not trained_analysis_service.get_service_status()["service_ready"]:
        raise HTTPException(status_code=503, detail="학습된 AI 모델이 로드되지 않았습니다.")
    
    start_time = time.time()
    
    try:
        logger.info(f"비디오 분석 시작: {request.video_id or request.video_url}")
        
        # 비디오 데이터 준비
        video_data = {
            "video_id": request.video_id,
            "video_url": request.video_url,
            "title": "",
            "description": "",
            "transcript": request.transcript or ""
        }
        
        # YouTube API로 데이터 수집 (있는 경우)
        if youtube_service and (request.video_id or request.video_url):
            try:
                video_id = request.video_id or youtube_service.extract_video_id(request.video_url)
                youtube_data = youtube_service.get_video_data(video_id)
                
                # YouTube 데이터로 업데이트
                video_data.update({
                    "title": youtube_data.get('metadata', {}).get('title', ''),
                    "description": youtube_data.get('metadata', {}).get('description', ''),
                    "transcript": youtube_data.get('transcript', '') or video_data["transcript"]
                })
            except Exception as e:
                logger.warning(f"YouTube 데이터 수집 실패: {e}")
        
        # 메타데이터에서 추가 정보 추출
        if request.metadata:
            video_data["title"] = request.metadata.get("title", video_data["title"])
            video_data["description"] = request.metadata.get("description", video_data["description"])
        
        # 학습된 모델로 분석
        analysis_result = trained_analysis_service.analyze_video(video_data)
        
        if not analysis_result["success"]:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # 결과 포맷팅
        formatted_result = {
            "video_id": video_data.get('video_id', request.video_id),
            "text_analyzed": analysis_result["data"].get("explanation", "")[:200] + "..." if len(analysis_result["data"].get("explanation", "")) > 200 else analysis_result["data"].get("explanation", ""),
            "credibility_score": analysis_result["data"]["credibility_score"],
            "credibility_grade": analysis_result["data"]["credibility_grade"],
            "analysis_breakdown": analysis_result["data"]["analysis_breakdown"],
            "detailed_analysis": analysis_result["data"]["detailed_analysis"],
            "explanation": analysis_result["data"]["explanation"],
            "confidence": analysis_result["data"]["confidence"],
            "metadata": analysis_result.get("metadata", {}),
            "model_version": analysis_result.get("model_version", "trained_v1.0")
        }
        
        processing_time = time.time() - start_time
        
        # 백그라운드에서 메트릭 수집
        background_tasks.add_task(collect_metrics, formatted_result, processing_time)
        
        return AnalysisResponse(
            success=True,
            data=formatted_result,
            processing_time=processing_time,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@app.post("/batch-analyze")
async def batch_analyze_videos(requests: list[VideoAnalysisRequest]):
    """
    여러 비디오 배치 분석
    
    Args:
        requests: 분석 요청 리스트
        
    Returns:
        배치 분석 결과
    """
    if not models_loaded:
        raise HTTPException(status_code=503, detail="AI 모델이 로드되지 않았습니다.")
    
    start_time = time.time()
    results = []
    
    try:
        for i, request in enumerate(requests):
            try:
                result = await analyze_video(request, BackgroundTasks())
                results.append({
                    "index": i,
                    "success": True,
                    "data": result.data,
                    "processing_time": result.processing_time
                })
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "total_requests": len(requests),
            "successful_analyses": len([r for r in results if r["success"]]),
            "failed_analyses": len([r for r in results if not r["success"]]),
            "total_processing_time": total_time,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"배치 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"배치 분석 중 오류가 발생했습니다: {str(e)}")

@app.websocket("/ws/analysis/{video_id}")
async def websocket_analysis(websocket: WebSocket, video_id: str):
    """WebSocket 실시간 분석 엔드포인트"""
    if not models_loaded:
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "event_type": "error",
            "data": {"message": "AI 모델이 로드되지 않았습니다."}
        }))
        await websocket.close()
        return
    
    try:
        # 기본 비디오 데이터 (실제로는 요청에서 받아야 함)
        video_data = {
            "video_id": video_id,
            "transcript": "This is a test video with factual information.",
            "metadata": {"title": "Test Video", "source": "test.com"}
        }
        
        # 실시간 분석 시작
        await realtime_service.start_real_time_analysis(websocket, video_id, video_data)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 해제: {video_id}")
    except Exception as e:
        logger.error(f"WebSocket 분석 실패: {video_id}, 오류: {e}")
        try:
            await websocket.send_text(json.dumps({
                "event_type": "error",
                "data": {"message": f"분석 중 오류가 발생했습니다: {str(e)}"}
            }))
        except:
            pass

# 리포트 API 엔드포인트들
@app.post("/report/analysis")
async def generate_analysis_report(report_data: Dict[str, Any]):
    """분석 리포트 생성"""
    try:
        result = await report_service.generate_analysis_report(
            video_id=report_data.get("video_id"),
            channel_id=report_data.get("channel_id"),
            analysis_data=report_data.get("analysis_data", {})
        )
        return result
        
    except Exception as e:
        logger.error(f"분석 리포트 생성 실패: {e}")
        return {"success": False, "error": str(e)}

@app.post("/report/trend")
async def generate_trend_report(report_data: Dict[str, Any]):
    """트렌드 리포트 생성"""
    try:
        result = await report_service.generate_trend_report(
            channel_id=report_data.get("channel_id"),
            period_days=report_data.get("period_days", 30),
            video_analyses=report_data.get("video_analyses", [])
        )
        return result
        
    except Exception as e:
        logger.error(f"트렌드 리포트 생성 실패: {e}")
        return {"success": False, "error": str(e)}

@app.get("/report/analysis/{report_id}")
async def get_analysis_report(report_id: str):
    """분석 리포트 조회"""
    try:
        return await report_service.get_analysis_report(report_id)
    except Exception as e:
        logger.error(f"분석 리포트 조회 실패: {report_id}, 오류: {e}")
        return {"error": str(e)}

@app.get("/report/trend/{report_id}")
async def get_trend_report(report_id: str):
    """트렌드 리포트 조회"""
    try:
        return await report_service.get_trend_report(report_id)
    except Exception as e:
        logger.error(f"트렌드 리포트 조회 실패: {report_id}, 오류: {e}")
        return {"error": str(e)}

@app.get("/reports/recent")
async def get_recent_reports(limit: int = 10):
    """최근 리포트 조회"""
    try:
        return await report_service.get_recent_reports(limit)
    except Exception as e:
        logger.error(f"최근 리포트 조회 실패: {e}")
        return {"error": str(e)}

# 채널 API 엔드포인트들
@app.post("/channel/update")
async def update_channel_stats(video_analysis_data: Dict[str, Any]):
    """채널 통계 업데이트"""
    try:
        video_analysis = VideoAnalysis(
            video_id=video_analysis_data.get("video_id"),
            channel_id=video_analysis_data.get("channel_id"),
            channel_name=video_analysis_data.get("channel_name"),
            video_title=video_analysis_data.get("video_title"),
            analysis_result=video_analysis_data.get("analysis_result", {})
        )
        
        result = await channel_service.update_channel_stats(video_analysis)
        return result
        
    except Exception as e:
        logger.error(f"채널 통계 업데이트 실패: {e}")
        return {"success": False, "error": str(e)}

@app.get("/channel/{channel_id}")
async def get_channel_stats(channel_id: str):
    """특정 채널 통계 조회"""
    try:
        return await channel_service.get_channel_stats(channel_id)
    except Exception as e:
        logger.error(f"채널 통계 조회 실패: {channel_id}, 오류: {e}")
        return {"error": str(e)}

@app.get("/channels")
async def get_all_channels():
    """모든 채널 통계 조회"""
    try:
        return await channel_service.get_all_channel_stats()
    except Exception as e:
        logger.error(f"모든 채널 통계 조회 실패: {e}")
        return {"error": str(e)}

@app.get("/channels/top")
async def get_top_channels(limit: int = 10, sort_by: str = "credibility"):
    """상위 채널 조회"""
    try:
        return await channel_service.get_top_channels(limit, sort_by)
    except Exception as e:
        logger.error(f"상위 채널 조회 실패: {e}")
        return {"error": str(e)}

@app.get("/channel/{channel_id}/videos")
async def get_channel_videos(channel_id: str, limit: int = 20):
    """채널의 비디오 분석 목록 조회"""
    try:
        return await channel_service.get_channel_videos(channel_id, limit)
    except Exception as e:
        logger.error(f"채널 비디오 조회 실패: {channel_id}, 오류: {e}")
        return {"error": str(e)}

@app.get("/channel/{channel_id}/trends")
async def get_channel_trends(channel_id: str, days: int = 30):
    """채널 트렌드 분석"""
    try:
        return await channel_service.get_channel_trends(channel_id, days)
    except Exception as e:
        logger.error(f"채널 트렌드 분석 실패: {channel_id}, 오류: {e}")
        return {"error": str(e)}

# 피드백 API 엔드포인트들
@app.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]):
    """사용자 피드백 제출"""
    try:
        feedback = UserFeedback(
            analysis_id=feedback_data.get("analysis_id"),
            user_id=feedback_data.get("user_id"),
            session_id=feedback_data.get("session_id", "anonymous"),
            feedback_type=feedback_data.get("feedback_type"),
            feedback_score=feedback_data.get("feedback_score"),
            feedback_text=feedback_data.get("feedback_text")
        )
        
        result = await feedback_service.submit_feedback(feedback)
        return result
        
    except Exception as e:
        logger.error(f"피드백 제출 실패: {e}")
        return {"success": False, "error": str(e)}

@app.get("/feedback/stats")
async def get_feedback_stats():
    """피드백 통계 조회"""
    try:
        return await feedback_service.get_feedback_stats()
    except Exception as e:
        logger.error(f"피드백 통계 조회 실패: {e}")
        return {"error": str(e)}

@app.get("/feedback/accuracy")
async def get_model_accuracy():
    """모델 정확도 계산"""
    try:
        return await feedback_service.calculate_model_accuracy()
    except Exception as e:
        logger.error(f"모델 정확도 계산 실패: {e}")
        return {"error": str(e)}

@app.get("/feedback/recent")
async def get_recent_feedback(limit: int = 10):
    """최근 피드백 조회"""
    try:
        return await feedback_service.get_recent_feedback(limit)
    except Exception as e:
        logger.error(f"최근 피드백 조회 실패: {e}")
        return {"error": str(e)}

@app.get("/feedback/{analysis_id}")
async def get_feedback_by_analysis(analysis_id: str):
    """특정 분석에 대한 피드백 조회"""
    try:
        return await feedback_service.get_feedback_by_analysis(analysis_id)
    except Exception as e:
        logger.error(f"분석별 피드백 조회 실패: {analysis_id}, 오류: {e}")
        return {"error": str(e)}

async def collect_metrics(analysis_result: Dict[str, Any], processing_time: float):
    """메트릭 수집 (백그라운드)"""
    try:
        # 여기에 메트릭 수집 로직 추가
        logger.info(f"메트릭 수집: 처리시간={processing_time:.2f}초, 신뢰도={analysis_result.get('credibility_score', 0)}")
    except Exception as e:
        logger.error(f"메트릭 수집 실패: {e}")

if __name__ == "__main__":
    # 서버 시작 시간 기록
    app.start_time = time.time()
    
    # uvicorn으로 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # reload 비활성화
        log_level="info"
    ) 