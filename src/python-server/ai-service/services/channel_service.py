"""
채널별 통계 서비스
채널별 신뢰도 통계 및 분석 데이터 관리
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ChannelStats:
    """채널 통계 데이터 모델"""
    channel_id: str
    channel_name: str
    total_videos: int
    average_credibility_score: float
    average_bias_score: float
    average_fact_check_score: float
    total_analysis_count: int
    last_analyzed: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class VideoAnalysis:
    """비디오 분석 데이터 모델"""
    video_id: str
    channel_id: str
    channel_name: str
    video_title: str
    analysis_result: Dict[str, Any]
    analyzed_at: datetime = None
    
    def __post_init__(self):
        if self.analyzed_at is None:
            self.analyzed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

class ChannelService:
    """
    채널별 통계 서비스
    채널별 신뢰도 통계 및 분석 데이터 관리
    """
    
    def __init__(self):
        self.channel_stats: Dict[str, ChannelStats] = {}
        self.video_analyses: Dict[str, VideoAnalysis] = {}
        self.logger = logger
    
    async def update_channel_stats(self, video_analysis: VideoAnalysis) -> Dict[str, Any]:
        """채널 통계 업데이트"""
        try:
            channel_id = video_analysis.channel_id
            
            # 기존 채널 통계 가져오기 또는 새로 생성
            if channel_id not in self.channel_stats:
                self.channel_stats[channel_id] = ChannelStats(
                    channel_id=channel_id,
                    channel_name=video_analysis.channel_name,
                    total_videos=0,
                    average_credibility_score=0.0,
                    average_bias_score=0.0,
                    average_fact_check_score=0.0,
                    total_analysis_count=0
                )
            
            # 비디오 분석 저장
            self.video_analyses[video_analysis.video_id] = video_analysis
            
            # 채널 통계 재계산
            await self._recalculate_channel_stats(channel_id)
            
            self.logger.info(f"채널 통계 업데이트: {channel_id}")
            
            return {
                "success": True,
                "message": "채널 통계가 업데이트되었습니다.",
                "channel_id": channel_id
            }
            
        except Exception as e:
            self.logger.error(f"채널 통계 업데이트 실패: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_channel_stats(self, channel_id: str) -> Dict[str, Any]:
        """특정 채널 통계 조회"""
        try:
            if channel_id not in self.channel_stats:
                return {"error": "채널을 찾을 수 없습니다."}
            
            stats = self.channel_stats[channel_id]
            return stats.to_dict()
            
        except Exception as e:
            self.logger.error(f"채널 통계 조회 실패: {channel_id}, 오류: {e}")
            return {"error": str(e)}
    
    async def get_all_channel_stats(self) -> List[Dict[str, Any]]:
        """모든 채널 통계 조회"""
        try:
            return [stats.to_dict() for stats in self.channel_stats.values()]
            
        except Exception as e:
            self.logger.error(f"모든 채널 통계 조회 실패: {e}")
            return []
    
    async def get_top_channels(self, limit: int = 10, sort_by: str = "credibility") -> List[Dict[str, Any]]:
        """상위 채널 조회"""
        try:
            channels = list(self.channel_stats.values())
            
            # 정렬 기준에 따라 정렬
            if sort_by == "credibility":
                channels.sort(key=lambda x: x.average_credibility_score, reverse=True)
            elif sort_by == "videos":
                channels.sort(key=lambda x: x.total_videos, reverse=True)
            elif sort_by == "recent":
                channels.sort(key=lambda x: x.last_analyzed or datetime.min, reverse=True)
            
            return [channel.to_dict() for channel in channels[:limit]]
            
        except Exception as e:
            self.logger.error(f"상위 채널 조회 실패: {e}")
            return []
    
    async def get_channel_videos(self, channel_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """채널의 비디오 분석 목록 조회"""
        try:
            videos = []
            for video in self.video_analyses.values():
                if video.channel_id == channel_id:
                    videos.append(video.to_dict())
            
            # 최신 순으로 정렬
            videos.sort(key=lambda x: x["analyzed_at"], reverse=True)
            
            return videos[:limit]
            
        except Exception as e:
            self.logger.error(f"채널 비디오 조회 실패: {channel_id}, 오류: {e}")
            return []
    
    async def get_channel_trends(self, channel_id: str, days: int = 30) -> Dict[str, Any]:
        """채널 트렌드 분석"""
        try:
            if channel_id not in self.channel_stats:
                return {"error": "채널을 찾을 수 없습니다."}
            
            # 지정된 기간 내의 분석 데이터 수집
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_videos = []
            
            for video in self.video_analyses.values():
                if (video.channel_id == channel_id and 
                    video.analyzed_at >= cutoff_date):
                    recent_videos.append(video)
            
            if not recent_videos:
                return {"error": "최근 분석 데이터가 없습니다."}
            
            # 트렌드 계산
            credibility_scores = [v.analysis_result.get("credibility_score", 0) for v in recent_videos]
            bias_scores = [v.analysis_result.get("bias_score", 0) for v in recent_videos]
            
            return {
                "channel_id": channel_id,
                "period_days": days,
                "total_videos": len(recent_videos),
                "average_credibility": sum(credibility_scores) / len(credibility_scores),
                "average_bias": sum(bias_scores) / len(bias_scores),
                "trend": self._calculate_trend(credibility_scores),
                "videos": [v.to_dict() for v in recent_videos]
            }
            
        except Exception as e:
            self.logger.error(f"채널 트렌드 분석 실패: {channel_id}, 오류: {e}")
            return {"error": str(e)}
    
    async def _recalculate_channel_stats(self, channel_id: str):
        """채널 통계 재계산"""
        try:
            channel_videos = [v for v in self.video_analyses.values() if v.channel_id == channel_id]
            
            if not channel_videos:
                return
            
            stats = self.channel_stats[channel_id]
            
            # 통계 계산
            stats.total_videos = len(channel_videos)
            stats.total_analysis_count = len(channel_videos)
            stats.last_analyzed = max(v.analyzed_at for v in channel_videos)
            
            # 평균 점수 계산
            credibility_scores = []
            bias_scores = []
            fact_check_scores = []
            
            for video in channel_videos:
                analysis = video.analysis_result
                if "credibility_score" in analysis:
                    credibility_scores.append(analysis["credibility_score"])
                if "bias_score" in analysis:
                    bias_scores.append(analysis["bias_score"])
                if "fact_check_score" in analysis:
                    fact_check_scores.append(analysis["fact_check_score"])
            
            if credibility_scores:
                stats.average_credibility_score = sum(credibility_scores) / len(credibility_scores)
            if bias_scores:
                stats.average_bias_score = sum(bias_scores) / len(bias_scores)
            if fact_check_scores:
                stats.average_fact_check_score = sum(fact_check_scores) / len(fact_check_scores)
            
        except Exception as e:
            self.logger.error(f"채널 통계 재계산 실패: {channel_id}, 오류: {e}")
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """트렌드 계산"""
        if len(scores) < 2:
            return "stable"
        
        # 간단한 선형 트렌드 계산
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "declining"
        else:
            return "stable" 