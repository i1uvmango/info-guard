"""
분석 API 라우터
YouTube 영상 신뢰도 분석을 위한 주요 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import asyncio

from utils.config import settings
from utils.logger import get_logger
from ai_models.model_manager import ModelManager

logger = get_logger(__name__)
router = APIRouter()

# Pydantic 모델들
class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    video_url: str = Field(..., description="YouTube 영상 URL")
    video_id: Optional[str] = Field(None, description="YouTube 영상 ID")
    analysis_types: List[str] = Field(
        default=["sentiment", "bias", "credibility", "content"],
        description="수행할 분석 타입들"
    )
    include_comments: bool = Field(
        default=True, 
        description="댓글 분석 포함 여부"
    )
    include_subtitles: bool = Field(
        default=True, 
        description="자막 분석 포함 여부"
    )
    priority: str = Field(
        default="normal",
        description="분석 우선순위 (low, normal, high)"
    )
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if not v.startswith(('https://www.youtube.com/', 'https://youtu.be/')):
            raise ValueError('유효한 YouTube URL이 아닙니다')
        return v
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = ["sentiment", "bias", "credibility", "content"]
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f'지원하지 않는 분석 타입: {analysis_type}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high"]:
            raise ValueError('우선순위는 low, normal, high 중 하나여야 합니다')
        return v

class AnalysisResponse(BaseModel):
    """분석 응답 모델"""
    analysis_id: str
    status: str
    message: str
    estimated_time_seconds: Optional[int] = None
    created_at: datetime

class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    analysis_id: str
    video_id: str
    video_title: str
    video_url: str
    analysis_types: List[str]
    results: Dict[str, Any]
    confidence_scores: Dict[str, float]
    overall_credibility_score: float
    analysis_time_seconds: float
    created_at: datetime
    updated_at: datetime

class BatchAnalysisRequest(BaseModel):
    """배치 분석 요청 모델"""
    video_urls: List[str] = Field(..., description="분석할 YouTube 영상 URL들")
    analysis_types: List[str] = Field(
        default=["sentiment", "bias", "credibility", "content"],
        description="수행할 분석 타입들"
    )
    max_concurrent: int = Field(
        default=3,
        description="동시 분석 최대 개수"
    )

# 전역 변수 (실제로는 Redis나 데이터베이스에 저장해야 함)
analysis_tasks: Dict[str, Dict[str, Any]] = {}
analysis_results: Dict[str, AnalysisResult] = {}

# 의존성 함수들
async def get_model_manager() -> ModelManager:
    """AI 모델 매니저 인스턴스 반환"""
    # TODO: 실제 모델 매니저 인스턴스 반환 로직 구현
    # 현재는 더미 데이터 반환
    return None

async def validate_video_access(video_url: str) -> bool:
    """영상 접근 가능성 검증"""
    try:
        from data_processing.youtube_client import YouTubeClient
        
        # YouTube 클라이언트로 영상 접근 가능성 확인
        client = YouTubeClient()
        video_id = client.extract_video_id(video_url)
        
        if not video_id:
            return False
            
        # 영상 정보 조회 시도
        video_info = await client.get_video_info(video_id)
        await client.close()
        
        return video_info is not None
        
    except Exception as e:
        logger.error(f"영상 접근 검증 실패: {e}")
        return False

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    model_manager: ModelManager = Depends(get_model_manager)
) -> AnalysisResponse:
    """
    YouTube 영상 분석 요청
    비동기로 분석을 수행하고 분석 ID를 반환
    """
    try:
        # 영상 접근 가능성 검증
        if not await validate_video_access(request.video_url):
            raise HTTPException(
                status_code=400,
                detail="영상에 접근할 수 없습니다. URL을 확인해주세요."
            )
        
        # 분석 ID 생성
        analysis_id = str(uuid.uuid4())
        
        # 분석 작업 정보 저장
        analysis_tasks[analysis_id] = {
            "status": "pending",
            "request": request.dict(),
            "created_at": datetime.now(),
            "progress": 0,
            "message": "분석 대기 중..."
        }
        
        # 백그라운드에서 분석 수행
        background_tasks.add_task(
            perform_analysis,
            analysis_id,
            request,
            model_manager
        )
        
        # 예상 소요 시간 계산 (분석 타입과 우선순위에 따라)
        estimated_time = calculate_estimated_time(request)
        
        logger.info(f"분석 요청 생성: {analysis_id}, URL: {request.video_url}")
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="pending",
            message="분석이 시작되었습니다",
            estimated_time_seconds=estimated_time,
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분석 요청 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분석 요청 처리 중 오류 발생: {str(e)}"
        )

@router.get("/status/{analysis_id}", response_model=Dict[str, Any])
async def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    분석 상태 조회
    """
    if analysis_id not in analysis_tasks:
        raise HTTPException(
            status_code=404,
            detail="분석 ID를 찾을 수 없습니다"
        )
    
    task = analysis_tasks[analysis_id]
    return {
        "analysis_id": analysis_id,
        "status": task["status"],
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "created_at": task["created_at"].isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@router.get("/result/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_result(analysis_id: str) -> AnalysisResult:
    """
    분석 결과 조회
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail="분석 결과를 찾을 수 없습니다"
        )
    
    return analysis_results[analysis_id]

@router.post("/batch", response_model=Dict[str, Any])
async def batch_analyze(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    배치 분석 요청
    여러 영상을 동시에 분석
    """
    try:
        # URL 개수 제한
        if len(request.video_urls) > 50:
            raise HTTPException(
                status_code=400,
                detail="한 번에 최대 50개 영상만 분석할 수 있습니다"
            )
        
        # 배치 분석 ID 생성
        batch_id = str(uuid.uuid4())
        analysis_ids = []
        
        # 각 영상에 대해 분석 요청 생성
        for video_url in request.video_urls:
            analysis_request = AnalysisRequest(
                video_url=video_url,
                analysis_types=request.analysis_types
            )
            
            analysis_id = str(uuid.uuid4())
            analysis_ids.append(analysis_id)
            
            # 분석 작업 정보 저장
            analysis_tasks[analysis_id] = {
                "status": "pending",
                "request": analysis_request.dict(),
                "created_at": datetime.now(),
                "progress": 0,
                "message": "배치 분석 대기 중...",
                "batch_id": batch_id
            }
        
        # 백그라운드에서 배치 분석 수행
        background_tasks.add_task(
            perform_batch_analysis,
            batch_id,
            analysis_ids,
            request
        )
        
        logger.info(f"배치 분석 요청 생성: {batch_id}, 영상 수: {len(request.video_urls)}")
        
        return {
            "batch_id": batch_id,
            "analysis_ids": analysis_ids,
            "total_videos": len(request.video_urls),
            "status": "pending",
            "message": "배치 분석이 시작되었습니다",
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 분석 요청 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"배치 분석 요청 처리 중 오류 발생: {str(e)}"
        )

@router.get("/batch/{batch_id}/status")
async def get_batch_status(batch_id: str) -> Dict[str, Any]:
    """
    배치 분석 상태 조회
    """
    # 배치 ID로 관련된 모든 분석 작업 찾기
    batch_analyses = [
        task for task in analysis_tasks.values()
        if task.get("batch_id") == batch_id
    ]
    
    if not batch_analyses:
        raise HTTPException(
            status_code=404,
            detail="배치 분석 ID를 찾을 수 없습니다"
        )
    
    # 상태 집계
    total = len(batch_analyses)
    completed = len([t for t in batch_analyses if t["status"] == "completed"])
    failed = len([t for t in batch_analyses if t["status"] == "failed"])
    pending = total - completed - failed
    
    return {
        "batch_id": batch_id,
        "total": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "progress_percent": round((completed / total) * 100, 2) if total > 0 else 0,
        "status": "completed" if completed == total else "in_progress" if pending > 0 else "failed"
    }

@router.delete("/{analysis_id}")
async def cancel_analysis(analysis_id: str) -> Dict[str, str]:
    """
    분석 작업 취소
    """
    if analysis_id not in analysis_tasks:
        raise HTTPException(
            status_code=404,
            detail="분석 ID를 찾을 수 없습니다"
        )
    
    task = analysis_tasks[analysis_id]
    if task["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail="이미 완료되거나 실패한 분석은 취소할 수 없습니다"
        )
    
    # 작업 상태를 취소로 변경
    task["status"] = "cancelled"
    task["message"] = "사용자에 의해 취소됨"
    
    # WebSocket 취소 알림 전송
    try:
        from .websocket import notify_analysis_cancelled
        await notify_analysis_cancelled(analysis_id)
    except Exception as ws_error:
        logger.error(f"WebSocket 취소 알림 전송 실패: {ws_error}")
    
    logger.info(f"분석 취소: {analysis_id}")
    
    return {"message": "분석이 취소되었습니다"}

# 백그라운드 작업 함수들
async def perform_analysis(
    analysis_id: str,
    request: AnalysisRequest,
    model_manager: ModelManager
):
    """실제 분석 수행"""
    try:
        from data_processing.youtube_client import YouTubeClient
        from .websocket import (
            notify_analysis_started,
            notify_analysis_progress,
            notify_analysis_completed,
            notify_analysis_failed
        )
        
        start_time = datetime.now()
        
        # 분석 시작 알림
        await notify_analysis_started(analysis_id, "분석 시작")
        
        # 진행 상황 업데이트
        analysis_tasks[analysis_id]["status"] = "processing"
        analysis_tasks[analysis_id]["progress"] = 10
        analysis_tasks[analysis_id]["message"] = "영상 정보 수집 중..."
        
        # 진행상황 알림
        await notify_analysis_progress(analysis_id, 10, "영상 정보 수집 중...")
        
        # YouTube 클라이언트 초기화
        client = YouTubeClient()
        video_id = client.extract_video_id(request.video_url)
        
        if not video_id:
            raise Exception("Video ID를 추출할 수 없습니다")
        
        # 영상 정보 수집
        video_info = await client.get_video_info(video_id)
        if not video_info:
            raise Exception("영상 정보를 가져올 수 없습니다")
        
        analysis_tasks[analysis_id]["progress"] = 20
        analysis_tasks[analysis_id]["message"] = "자막 및 댓글 수집 중..."
        
        # 진행상황 알림
        await notify_analysis_progress(analysis_id, 20, "자막 및 댓글 수집 중...")
        
        # 자막 수집
        transcript = None
        if request.include_subtitles:
            transcript = await client.get_video_transcript(video_id)
        
        # 댓글 수집
        comments = []
        if request.include_comments:
            comments = await client.get_video_comments(video_id, max_results=50)
        
        analysis_tasks[analysis_id]["progress"] = 40
        analysis_tasks[analysis_id]["message"] = "AI 모델 분석 중..."
        
        # 진행상황 알림
        await notify_analysis_progress(analysis_id, 40, "AI 모델 분석 중...")
        
        # AI 모델 분석 수행
        analysis_results_data = {}
        confidence_scores = {}
        
        # 감정 분석
        if "sentiment" in request.analysis_types:
            sentiment_result = await analyze_sentiment(transcript, comments)
            analysis_results_data["sentiment"] = sentiment_result
            confidence_scores["sentiment"] = sentiment_result.get("confidence", 0.8)
        
        # 편향 감지
        if "bias" in request.analysis_types:
            bias_result = await analyze_bias(transcript, comments)
            analysis_results_data["bias"] = bias_result
            confidence_scores["bias"] = bias_result.get("confidence", 0.8)
        
        # 신뢰도 분석
        if "credibility" in request.analysis_types:
            credibility_result = await analyze_credibility(transcript, comments, video_info)
            analysis_results_data["credibility"] = credibility_result
            confidence_scores["credibility"] = credibility_result.get("confidence", 0.8)
        
        # 콘텐츠 분류
        if "content" in request.analysis_types:
            content_result = await analyze_content(transcript, video_info)
            analysis_results_data["content"] = content_result
            confidence_scores["content"] = content_result.get("confidence", 0.8)
        
        analysis_tasks[analysis_id]["progress"] = 80
        analysis_tasks[analysis_id]["message"] = "결과 정리 중..."
        
        # 진행상황 알림
        await notify_analysis_progress(analysis_id, 80, "결과 정리 중...")
        
        # 전체 신뢰도 점수 계산
        overall_credibility_score = calculate_overall_credibility(confidence_scores)
        
        # 분석 완료
        analysis_tasks[analysis_id]["status"] = "completed"
        analysis_tasks[analysis_id]["progress"] = 100
        analysis_tasks[analysis_id]["message"] = "분석 완료"
        
        # 결과 생성
        result = AnalysisResult(
            analysis_id=analysis_id,
            video_id=video_id,
            video_title=video_info.get("title", "Unknown"),
            video_url=request.video_url,
            analysis_types=request.analysis_types,
            results=analysis_results_data,
            confidence_scores=confidence_scores,
            overall_credibility_score=overall_credibility_score,
            analysis_time_seconds=(datetime.now() - start_time).total_seconds(),
            created_at=start_time,
            updated_at=datetime.now()
        )
        
        # 결과 저장
        analysis_results[analysis_id] = result
        
        # 분석 완료 알림
        await notify_analysis_completed(analysis_id, result)
        
        # 클라이언트 정리
        await client.close()
        
        logger.info(f"분석 완료: {analysis_id}, 영상: {video_info.get('title', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"분석 수행 실패: {analysis_id}, 오류: {e}")
        analysis_tasks[analysis_id]["status"] = "failed"
        analysis_tasks[analysis_id]["message"] = f"분석 실패: {str(e)}"
        
        # 분석 실패 알림
        try:
            from .websocket import notify_analysis_failed
            await notify_analysis_failed(analysis_id, str(e))
        except Exception as ws_error:
            logger.error(f"WebSocket 실패 알림 전송 실패: {ws_error}")

# AI 분석 함수들
async def analyze_sentiment(transcript: str, comments: List[Dict]) -> Dict[str, Any]:
    """감정 분석 수행"""
    try:
        # TODO: 실제 감정 분석 모델 사용
        # 현재는 간단한 규칙 기반 분석
        
        text_to_analyze = ""
        if transcript:
            text_to_analyze += transcript + " "
        
        # 댓글 텍스트 추가
        for comment in comments:
            text_to_analyze += comment.get("text", "") + " "
        
        # 간단한 감정 분석 (실제로는 AI 모델 사용)
        positive_words = ["좋다", "훌륭하다", "감동", "사랑", "행복", "좋은", "멋진", "최고"]
        negative_words = ["나쁘다", "싫다", "실망", "화나다", "슬프다", "나쁜", "최악", "별로"]
        
        positive_count = sum(1 for word in positive_words if word in text_to_analyze)
        negative_count = sum(1 for word in negative_words if word in text_to_analyze)
        
        if positive_count > negative_count:
            label = "positive"
            confidence = min(0.9, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            label = "negative"
            confidence = min(0.9, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            label = "neutral"
            confidence = 0.7
        
        return {
            "label": label,
            "confidence": confidence,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "neutral_score": len(text_to_analyze.split()) - positive_count - negative_count
        }
        
    except Exception as e:
        logger.error(f"감정 분석 실패: {e}")
        return {"label": "neutral", "confidence": 0.5, "error": str(e)}

async def analyze_bias(transcript: str, comments: List[Dict]) -> Dict[str, Any]:
    """편향 감지 분석 수행"""
    try:
        # TODO: 실제 편향 감지 모델 사용
        # 현재는 간단한 규칙 기반 분석
        
        text_to_analyze = ""
        if transcript:
            text_to_analyze += transcript + " "
        
        # 댓글 텍스트 추가
        for comment in comments:
            text_to_analyze += comment.get("text", "") + " "
        
        # 편향 감지 키워드
        bias_indicators = {
            "political": ["정치", "여당", "야당", "보수", "진보", "좌파", "우파", "정부", "대통령"],
            "gender": ["남자", "여자", "성별", "남성", "여성", "아빠", "엄마"],
            "racial": ["인종", "민족", "국적", "외국인", "한국인"],
            "religious": ["종교", "기독교", "불교", "천주교", "신", "하나님"]
        }
        
        bias_scores = {}
        total_bias_score = 0
        
        for bias_type, keywords in bias_indicators.items():
            count = sum(1 for keyword in keywords if keyword in text_to_analyze)
            bias_scores[bias_type] = count
            total_bias_score += count
        
        # 편향 정도 판단
        if total_bias_score == 0:
            label = "neutral"
            confidence = 0.8
        elif total_bias_score <= 2:
            label = "low_bias"
            confidence = 0.7
        elif total_bias_score <= 5:
            label = "moderate_bias"
            confidence = 0.8
        else:
            label = "high_bias"
            confidence = 0.9
        
        return {
            "label": label,
            "confidence": confidence,
            "bias_scores": bias_scores,
            "total_bias_score": total_bias_score
        }
        
    except Exception as e:
        logger.error(f"편향 감지 분석 실패: {e}")
        return {"label": "neutral", "confidence": 0.5, "error": str(e)}

async def analyze_credibility(transcript: str, comments: List[Dict], video_info: Dict) -> Dict[str, Any]:
    """신뢰도 분석 수행"""
    try:
        # TODO: 실제 신뢰도 분석 모델 사용
        # 현재는 여러 요소를 종합한 점수 계산
        
        credibility_score = 0.5  # 기본 점수
        factors = {}
        
        # 1. 채널 신뢰도 (구독자 수, 영상 수 등)
        if video_info:
            subscriber_count = video_info.get("subscriber_count", 0)
            video_count = video_info.get("video_count", 0)
            
            if subscriber_count > 1000000:  # 100만 구독자 이상
                channel_score = 0.9
            elif subscriber_count > 100000:  # 10만 구독자 이상
                channel_score = 0.8
            elif subscriber_count > 10000:  # 1만 구독자 이상
                channel_score = 0.7
            else:
                channel_score = 0.5
            
            factors["channel_credibility"] = channel_score
            credibility_score += channel_score * 0.3
        
        # 2. 콘텐츠 품질 (자막 길이, 댓글 수 등)
        if transcript:
            transcript_length = len(transcript)
            if transcript_length > 1000:
                content_score = 0.9
            elif transcript_length > 500:
                content_score = 0.8
            elif transcript_length > 100:
                content_score = 0.7
            else:
                content_score = 0.5
            
            factors["content_quality"] = content_score
            credibility_score += content_score * 0.2
        
        # 3. 댓글 품질
        if comments:
            comment_count = len(comments)
            if comment_count > 100:
                comment_score = 0.8
            elif comment_count > 50:
                comment_score = 0.7
            elif comment_count > 10:
                comment_score = 0.6
            else:
                comment_score = 0.5
            
            factors["comment_quality"] = comment_score
            credibility_score += comment_score * 0.1
        
        # 4. 영상 통계
        if video_info:
            view_count = video_info.get("view_count", 0)
            like_count = video_info.get("like_count", 0)
            
            if view_count > 0:
                like_ratio = like_count / view_count
                if like_ratio > 0.1:  # 좋아요 비율 10% 이상
                    engagement_score = 0.9
                elif like_ratio > 0.05:  # 좋아요 비율 5% 이상
                    engagement_score = 0.8
                elif like_ratio > 0.01:  # 좋아요 비율 1% 이상
                    engagement_score = 0.7
                else:
                    engagement_score = 0.5
                
                factors["engagement"] = engagement_score
                credibility_score += engagement_score * 0.2
        
        # 5. 최종 신뢰도 점수 정규화
        credibility_score = min(1.0, max(0.0, credibility_score))
        
        # 신뢰도 레벨 결정
        if credibility_score >= 0.8:
            label = "highly_reliable"
        elif credibility_score >= 0.6:
            label = "reliable"
        elif credibility_score >= 0.4:
            label = "moderate"
        else:
            label = "low_reliability"
        
        return {
            "label": label,
            "confidence": min(0.95, credibility_score + 0.1),
            "credibility_score": round(credibility_score, 3),
            "factors": factors
        }
        
    except Exception as e:
        logger.error(f"신뢰도 분석 실패: {e}")
        return {"label": "moderate", "confidence": 0.5, "error": str(e)}

async def analyze_content(transcript: str, video_info: Dict) -> Dict[str, Any]:
    """콘텐츠 분류 분석 수행"""
    try:
        # TODO: 실제 콘텐츠 분류 모델 사용
        # 현재는 키워드 기반 분류
        
        text_to_analyze = ""
        if transcript:
            text_to_analyze += transcript + " "
        
        # 제목과 설명 추가
        if video_info:
            text_to_analyze += video_info.get("title", "") + " "
            text_to_analyze += video_info.get("description", "") + " "
        
        # 콘텐츠 카테고리 키워드
        content_categories = {
            "news": ["뉴스", "보도", "기자", "언론", "방송", "매체", "사건", "사고"],
            "education": ["교육", "학습", "강의", "수업", "학교", "대학", "교수", "선생님"],
            "entertainment": ["예능", "오락", "게임", "음악", "춤", "노래", "연예인", "스타"],
            "technology": ["기술", "IT", "컴퓨터", "프로그램", "소프트웨어", "알고리즘", "AI"],
            "lifestyle": ["라이프스타일", "요리", "운동", "건강", "패션", "뷰티", "여행"],
            "politics": ["정치", "정책", "법안", "의회", "선거", "투표", "민주주의"],
            "business": ["경제", "비즈니스", "기업", "투자", "주식", "금융", "마케팅"]
        }
        
        category_scores = {}
        for category, keywords in content_categories.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            category_scores[category] = score
        
        # 가장 높은 점수의 카테고리 선택
        if category_scores:
            primary_category = max(category_scores, key=category_scores.get)
            confidence = min(0.95, 0.5 + category_scores[primary_category] * 0.1)
        else:
            primary_category = "general"
            confidence = 0.5
        
        return {
            "label": primary_category,
            "confidence": confidence,
            "category_scores": category_scores,
            "primary_category": primary_category
        }
        
    except Exception as e:
        logger.error(f"콘텐츠 분류 분석 실패: {e}")
        return {"label": "general", "confidence": 0.5, "error": str(e)}

def calculate_overall_credibility(confidence_scores: Dict[str, float]) -> float:
    """전체 신뢰도 점수 계산"""
    try:
        if not confidence_scores:
            return 0.5
        
        # 가중 평균 계산
        total_score = 0
        total_weight = 0
        
        # 각 분석 타입별 가중치
        weights = {
            "sentiment": 0.2,
            "bias": 0.3,
            "credibility": 0.4,
            "content": 0.1
        }
        
        for analysis_type, score in confidence_scores.items():
            weight = weights.get(analysis_type, 0.25)
            total_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_score = total_score / total_weight
        else:
            overall_score = 0.5
        
        return round(overall_score, 3)
        
    except Exception as e:
        logger.error(f"전체 신뢰도 점수 계산 실패: {e}")
        return 0.5

async def perform_batch_analysis(
    batch_id: str,
    analysis_ids: List[str],
    request: BatchAnalysisRequest
):
    """배치 분석 수행"""
    try:
        # 동시 분석 제한을 고려하여 순차적으로 처리
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def process_single_analysis(analysis_id: str):
            async with semaphore:
                task = analysis_tasks[analysis_id]
                analysis_request = AnalysisRequest(**task["request"])
                
                # 개별 분석 수행
                await perform_analysis(analysis_id, analysis_request, None)
        
        # 모든 분석 작업을 동시에 시작
        tasks = [process_single_analysis(analysis_id) for analysis_id in analysis_ids]
        await asyncio.gather(*tasks)
        
        logger.info(f"배치 분석 완료: {batch_id}")
        
    except Exception as e:
        logger.error(f"배치 분석 실패: {batch_id}, 오류: {e}")

def calculate_estimated_time(request: AnalysisRequest) -> int:
    """예상 소요 시간 계산 (초 단위)"""
    base_time = 30  # 기본 30초
    
    # 분석 타입에 따른 추가 시간
    type_multiplier = len(request.analysis_types) * 0.8
    
    # 우선순위에 따른 조정
    priority_multiplier = {
        "low": 1.5,
        "normal": 1.0,
        "high": 0.7
    }.get(request.priority, 1.0)
    
    # 댓글/자막 포함 여부
    content_multiplier = 1.0
    if request.include_comments:
        content_multiplier += 0.3
    if request.include_subtitles:
        content_multiplier += 0.2
    
    estimated_time = int(base_time * type_multiplier * priority_multiplier * content_multiplier)
    return max(estimated_time, 10)  # 최소 10초
