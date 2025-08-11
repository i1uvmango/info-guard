"""
분석 서비스
YouTube 영상 분석을 조율하고 관리합니다.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from app.core.logging import get_logger
from app.core.config import get_settings
from app.services.youtube import YouTubeService
from app.services.ai_models import ai_model_service
from app.services.cache import cache_service
from app.models.analysis import AnalysisResult, AnalysisMetadata, AnalysisType, AnalysisStatus
from app.models.youtube import YouTubeVideoMetadata

logger = get_logger(__name__)
settings = get_settings()


class AnalysisService:
    """영상 분석을 조율하는 서비스"""

    def __init__(self):
        self.youtube_service = YouTubeService(cache_service)
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.analysis_queue: List[str] = []
        self.max_concurrent_analyses = 3
        self.websocket_manager = None  # WebSocket 매니저 참조

    def set_websocket_manager(self, manager):
        """WebSocket 매니저를 설정합니다."""
        self.websocket_manager = manager
        logger.info("WebSocket 매니저가 분석 서비스에 연결되었습니다.")

    async def _broadcast_update(self, analysis_id: str, update_data: Dict[str, Any]):
        """WebSocket을 통해 분석 업데이트를 브로드캐스트합니다."""
        if self.websocket_manager:
            try:
                message = {
                    "type": "analysis_update",
                    "analysis_id": analysis_id,
                    "data": update_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.websocket_manager.broadcast_to_analysis(
                    str(message), analysis_id
                )
                logger.debug(f"WebSocket 업데이트 전송: {analysis_id}")
                
            except Exception as e:
                logger.error(f"WebSocket 업데이트 전송 실패: {analysis_id} - {e}")

    async def _update_analysis_progress(
        self, 
        analysis_id: str, 
        progress: int, 
        message: str, 
        status: AnalysisStatus = None
    ):
        """분석 진행 상황을 업데이트하고 WebSocket으로 전송합니다."""
        if analysis_id in self.active_analyses:
            analysis_data = self.active_analyses[analysis_id]
            analysis_data["progress"] = progress
            analysis_data["message"] = message
            analysis_data["updated_at"] = datetime.utcnow()
            
            if status:
                analysis_data["status"] = status
            
            # WebSocket으로 업데이트 전송
            await self._broadcast_update(analysis_id, {
                "status": analysis_data["status"].value if hasattr(analysis_data["status"], 'value') else str(analysis_data["status"]),
                "progress": progress,
                "message": message,
                "updated_at": analysis_data["updated_at"].isoformat()
            })

    async def start_analysis(
        self,
        video_url: str,
        analysis_types: List[str],
        priority: str = "normal"
    ) -> str:
        """분석을 시작합니다."""
        try:
            # 분석 ID 생성
            analysis_id = str(uuid4())
            
            # 분석 작업 생성
            analysis_data = {
                "id": analysis_id,
                "video_url": video_url,
                "analysis_types": analysis_types,
                "priority": priority,
                "status": AnalysisStatus.PENDING,
                "progress": 0,
                "message": "분석 요청이 등록되었습니다.",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "estimated_completion": None,
                "video_metadata": None,
                "results": None,
                "error": None
            }
            
            # 저장소에 저장
            self.active_analyses[analysis_id] = analysis_data
            
            # 우선순위에 따라 큐에 추가
            if priority == "high":
                self.analysis_queue.insert(0, analysis_id)
            else:
                self.analysis_queue.append(analysis_id)
            
            # 백그라운드에서 분석 시작
            asyncio.create_task(self._process_analysis_queue())
            
            logger.info(f"분석 요청 등록: {analysis_id} - {video_url}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"분석 시작 실패: {e}")
            raise

    async def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """분석 상태를 조회합니다."""
        return self.active_analyses.get(analysis_id)

    async def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """분석 결과를 조회합니다."""
        analysis_data = self.active_analyses.get(analysis_id)
        if not analysis_data or analysis_data["status"] != AnalysisStatus.COMPLETED:
            return None
            
        return AnalysisResult(
            analysis_id=analysis_data["id"],
            video_url=analysis_data["video_url"],
            analysis_type=AnalysisType.COMPREHENSIVE,  # 기본값으로 설정
            status=AnalysisStatus.COMPLETED,  # 기본값으로 설정
            created_at=analysis_data["created_at"],
            completed_at=analysis_data.get("completed_at", datetime.utcnow()),
            processing_time=analysis_data.get("processing_time"),
            model_version="1.0.0"
        )

    async def cancel_analysis(self, analysis_id: str) -> bool:
        """분석을 취소합니다."""
        if analysis_id not in self.active_analyses:
            return False
            
        analysis_data = self.active_analyses[analysis_id]
        if analysis_data["status"] in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            return False
            
        analysis_data["status"] = AnalysisStatus.CANCELLED
        analysis_data["message"] = "사용자에 의해 취소되었습니다."
        analysis_data["updated_at"] = datetime.utcnow()
        
        # 큐에서 제거
        if analysis_id in self.analysis_queue:
            self.analysis_queue.remove(analysis_id)
            
        logger.info(f"분석 취소: {analysis_id}")
        return True

    async def _process_analysis_queue(self):
        """분석 큐를 처리합니다."""
        while self.analysis_queue:
            # 동시 실행 제한 확인
            running_count = sum(
                1 for a in self.active_analyses.values() 
                if a["status"] == AnalysisStatus.PROCESSING
            )
            
            if running_count >= self.max_concurrent_analyses:
                await asyncio.sleep(1)
                continue
                
            # 큐에서 분석 ID 가져오기
            analysis_id = self.analysis_queue.pop(0)
            
            # 분석 실행
            asyncio.create_task(self._execute_analysis(analysis_id))

    async def _execute_analysis(self, analysis_id: str):
        """실제 분석을 실행합니다."""
        try:
            analysis_data = self.active_analyses[analysis_id]
            
            # 상태를 처리 중으로 변경하고 WebSocket으로 전송
            await self._update_analysis_progress(
                analysis_id, 10, "영상 데이터를 수집하고 있습니다...", AnalysisStatus.PROCESSING
            )
            
            # 1. YouTube 영상 정보 수집
            video_metadata = await self._collect_video_data(analysis_id)
            if not video_metadata:
                raise Exception("영상 정보 수집 실패")
                
            analysis_data["video_metadata"] = video_metadata
            await self._update_analysis_progress(
                analysis_id, 30, "AI 모델로 분석을 수행하고 있습니다..."
            )
            
            # 2. AI 분석 수행
            analysis_result = await self._perform_ai_analysis(
                video_metadata, analysis_data["analysis_types"]
            )
            
            await self._update_analysis_progress(
                analysis_id, 80, "결과를 정리하고 있습니다..."
            )
            
            # 3. 결과 정리
            analysis_data["results"] = analysis_result
            analysis_data["completed_at"] = datetime.utcnow()
            
            # 완료 상태로 업데이트하고 WebSocket으로 전송
            await self._update_analysis_progress(
                analysis_id, 100, "분석이 완료되었습니다.", AnalysisStatus.COMPLETED
            )
            
            # 메타데이터 생성
            metadata = AnalysisMetadata(
                analysis_type=",".join(analysis_data["analysis_types"]),
                processing_time=(analysis_data["completed_at"] - analysis_data["created_at"]).total_seconds(),
                started_at=analysis_data["created_at"],
                completed_at=analysis_data["completed_at"],
                video_metadata=video_metadata
            )
            analysis_data["metadata"] = metadata
            
            logger.info(f"분석 완료: {analysis_id}")
            
        except Exception as e:
            logger.error(f"분석 실행 실패: {analysis_id} - {e}")
            if analysis_id in self.active_analyses:
                analysis_data = self.active_analyses[analysis_id]
                analysis_data["error"] = str(e)
                
                # 실패 상태로 업데이트하고 WebSocket으로 전송
                await self._update_analysis_progress(
                    analysis_id, 0, f"분석 실패: {str(e)}", AnalysisStatus.FAILED
                )

    async def _collect_video_data(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """YouTube 영상 데이터를 수집합니다."""
        try:
            analysis_data = self.active_analyses[analysis_id]
            video_url = analysis_data["video_url"]
            
            # 비디오 ID 추출
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise Exception("유효한 YouTube URL이 아닙니다.")
            
            # 캐시에서 먼저 확인
            cache_key = f"video_metadata:{video_id}"
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.info(f"캐시에서 영상 정보 조회: {video_id}")
                return cached_data
            
            # YouTube API로 데이터 수집
            video_metadata = await self.youtube_service.get_video_metadata(video_id)
            if not video_metadata:
                raise Exception("영상 정보를 가져올 수 없습니다.")
            
            # 캐시에 저장 (1시간 TTL)
            await cache_service.set(cache_key, video_metadata, ttl=3600)
            
            return video_metadata
            
        except Exception as e:
            logger.error(f"영상 데이터 수집 실패: {e}")
            raise

    async def _perform_ai_analysis(
        self,
        video_metadata: Dict[str, Any],
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """AI 모델로 분석을 수행합니다."""
        try:
            # 분석할 텍스트 준비
            text_content = self._prepare_text_content(video_metadata)
            
            # AI 분석 실행
            analysis_result = await ai_model_service.analyze_content(
                text=text_content,
                video_metadata=video_metadata,
                analysis_type="full" if "full" in analysis_types else ",".join(analysis_types)
            )
            
            # 결과를 딕셔너리로 변환
            results = {}
            if analysis_result.credibility:
                results["credibility"] = {
                    "score": analysis_result.credibility.overall_score,
                    "fact_check_score": analysis_result.credibility.fact_check_score,
                    "source_reliability": analysis_result.credibility.source_reliability,
                    "bias_indicator": analysis_result.credibility.bias_indicator,
                    "confidence": analysis_result.credibility.confidence,
                    "reasoning": analysis_result.credibility.reasoning
                }
            
            if analysis_result.bias:
                results["bias"] = {
                    "score": analysis_result.bias.overall_bias_score,
                    "types": analysis_result.bias.bias_types,
                    "indicators": analysis_result.bias.bias_indicators,
                    "confidence": analysis_result.bias.confidence,
                    "reasoning": analysis_result.bias.reasoning
                }
            
            if analysis_result.fact_check:
                results["facts"] = {
                    "score": analysis_result.fact_check.overall_fact_score,
                    "claims": analysis_result.fact_check.fact_claims,
                    "verification_status": analysis_result.fact_check.verification_status,
                    "sources": analysis_result.fact_check.sources,
                    "confidence": analysis_result.fact_check.confidence,
                    "reasoning": analysis_result.fact_check.reasoning
                }
            
            if analysis_result.sentiment:
                results["sentiment"] = {
                    "score": analysis_result.sentiment.overall_sentiment,
                    "dominant_emotion": analysis_result.sentiment.dominant_emotion,
                    "emotion_breakdown": analysis_result.sentiment.emotion_breakdown,
                    "confidence": analysis_result.sentiment.confidence,
                    "reasoning": analysis_result.sentiment.reasoning
                }
            
            if analysis_result.classification:
                results["classification"] = {
                    "primary_category": analysis_result.classification.primary_category,
                    "secondary_categories": analysis_result.classification.secondary_categories,
                    "content_type": analysis_result.classification.content_type,
                    "target_audience": analysis_result.classification.target_audience,
                    "confidence": analysis_result.classification.confidence,
                    "reasoning": analysis_result.classification.reasoning
                }
            
            # 메타데이터 추가
            results["metadata"] = {
                "processing_time": analysis_result.processing_time,
                "model_version": analysis_result.model_version,
                "analysis_timestamp": analysis_result.completed_at.isoformat() if analysis_result.completed_at else None
            }
            
            return results
            
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}")
            raise

    def _prepare_text_content(self, video_metadata: Dict[str, Any]) -> str:
        """분석할 텍스트 콘텐츠를 준비합니다."""
        text_parts = []
        
        # 제목
        if video_metadata.get("title"):
            text_parts.append(f"제목: {video_metadata['title']}")
        
        # 설명
        if video_metadata.get("description"):
            text_parts.append(f"설명: {video_metadata['description']}")
        
        # 자막
        if video_metadata.get("transcript"):
            text_parts.append(f"자막: {video_metadata['transcript']}")
        
        # 댓글 (최대 10개)
        comments = video_metadata.get("comments", [])
        if comments:
            comment_texts = [comment.get("text", "") for comment in comments[:10]]
            text_parts.append(f"댓글: {' '.join(comment_texts)}")
        
        return " ".join(text_parts)

    def _extract_video_id(self, url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID를 추출합니다."""
        import re
        
        # 다양한 YouTube URL 패턴 지원
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    async def get_active_analyses(self) -> List[Dict[str, Any]]:
        """활성 분석 목록을 반환합니다."""
        return list(self.active_analyses.values())

    async def cleanup_completed_analyses(self, max_age_hours: int = 24):
        """완료된 분석을 정리합니다."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            to_remove = []
            
            for analysis_id, analysis_data in self.active_analyses.items():
                if (analysis_data["status"] in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED] and 
                    analysis_data["updated_at"] < cutoff_time):
                    to_remove.append(analysis_id)
            
            for analysis_id in to_remove:
                del self.active_analyses[analysis_id]
                
            if to_remove:
                logger.info(f"{len(to_remove)}개의 완료된 분석 정리됨")
                
        except Exception as e:
            logger.error(f"분석 정리 실패: {e}")

    async def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계를 반환합니다."""
        try:
            total_analyses = len(self.active_analyses)
            pending_count = sum(1 for a in self.active_analyses.values() if a["status"] == AnalysisStatus.PENDING)
            processing_count = sum(1 for a in self.active_analyses.values() if a["status"] == AnalysisStatus.PROCESSING)
            completed_count = sum(1 for a in self.active_analyses.values() if a["status"] == AnalysisStatus.COMPLETED)
            failed_count = sum(1 for a in self.active_analyses.values() if a["status"] == AnalysisStatus.FAILED)
            cancelled_count = sum(1 for a in self.active_analyses.values() if a["status"] == AnalysisStatus.CANCELLED)
            
            return {
                "total_analyses": total_analyses,
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "cancelled": cancelled_count,
                "queue_length": len(self.analysis_queue),
                "max_concurrent": self.max_concurrent_analyses,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {"error": str(e)}


# 전역 분석 서비스 인스턴스
analysis_service = AnalysisService()
