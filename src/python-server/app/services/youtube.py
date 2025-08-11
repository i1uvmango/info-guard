"""
YouTube 서비스
YouTube API 연동 및 영상 정보 수집을 담당합니다.
"""

import re
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, parse_qs

import httpx
from app.core.logging import get_logger
from app.core.config import get_settings
from app.core.exceptions import YouTubeAPIError, ValidationError
from app.models.youtube import (
    YouTubeVideoInfo,
    YouTubeTranscript,
    YouTubeComment,
    YouTubeChannelInfo,
    YouTubeSearchResult,
    YouTubeAPIQuota,
    YouTubeVideoMetadata,
)
from app.services.cache import CacheService


logger = get_logger(__name__)
settings = get_settings()


class YouTubeService:
    """YouTube 서비스 클래스"""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.api_key = settings.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.quota_limit = settings.YOUTUBE_API_QUOTA_LIMIT
        self.quota_used = 0
        
        # HTTP 클라이언트 설정
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        logger.info("YouTube 서비스 초기화됨")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_video_metadata(self, video_url: str) -> YouTubeVideoMetadata:
        """YouTube 영상의 메타데이터를 수집합니다."""
        try:
            # URL에서 비디오 ID 추출
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValidationError("유효한 YouTube URL이 아닙니다.")
            
            # 캐시에서 먼저 확인
            cache_key = f"youtube_video_{video_id}"
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                logger.info(f"캐시에서 영상 정보 로드: {video_id}")
                return YouTubeVideoMetadata(**cached_data)
            
            # YouTube API를 통해 정보 수집
            video_info = await self._fetch_video_info(video_id)
            channel_info = await self._fetch_channel_info(video_info.channel_id)
            transcript = await self._fetch_transcript(video_id)
            comments = await self._fetch_comments(video_id)
            
            # 메타데이터 생성
            metadata = YouTubeVideoMetadata(
                video_id=video_id,
                url=video_url,
                title=video_info.title,
                description=video_info.description,
                channel_info=channel_info,
                duration_seconds=self._parse_duration(video_info.duration),
                category=video_info.category_title,
                tags=video_info.tags,
                view_count=video_info.view_count,
                like_ratio=self._calculate_like_ratio(video_info.like_count, video_info.dislike_count),
                engagement_rate=self._calculate_engagement_rate(
                    video_info.view_count, 
                    video_info.like_count, 
                    video_info.comment_count
                ),
                transcript=transcript,
                comments=comments,
                comment_sentiment=await self._analyze_comment_sentiment(comments),
                collected_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            # 캐시에 저장 (1시간 TTL)
            await self.cache_service.set(cache_key, metadata.dict(), ttl=3600)
            
            logger.info(f"영상 메타데이터 수집 완료: {video_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"영상 메타데이터 수집 실패: {video_url} - {str(e)}")
            raise YouTubeAPIError(f"영상 메타데이터를 수집할 수 없습니다: {str(e)}")
    
    async def search_videos(self, query: str, max_results: int = 10) -> List[YouTubeSearchResult]:
        """YouTube에서 영상을 검색합니다."""
        try:
            if not self.api_key:
                raise YouTubeAPIError("YouTube API 키가 설정되지 않았습니다.")
            
            # API 할당량 확인
            if not self._check_quota("search"):
                raise YouTubeAPIError("YouTube API 할당량이 부족합니다.")
            
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }
            
            response = await self.client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            
            data = response.json()
            self._update_quota("search")
            
            results = []
            for item in data.get("items", []):
                snippet = item["snippet"]
                result = YouTubeSearchResult(
                    video_id=item["id"]["videoId"],
                    title=snippet["title"],
                    description=snippet["description"],
                    channel_title=snippet["channelTitle"],
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    thumbnails=snippet["thumbnails"],
                    duration=None,  # 별도 API 호출 필요
                    view_count=None,  # 별도 API 호출 필요
                    relevance_score=None
                )
                results.append(result)
            
            logger.info(f"영상 검색 완료: '{query}' - {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"영상 검색 실패: '{query}' - {str(e)}")
            raise YouTubeAPIError(f"영상을 검색할 수 없습니다: {str(e)}")
    
    async def get_channel_info(self, channel_id: str) -> YouTubeChannelInfo:
        """채널 정보를 조회합니다."""
        try:
            # 캐시 확인
            cache_key = f"youtube_channel_{channel_id}"
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                return YouTubeChannelInfo(**cached_data)
            
            # API 호출
            channel_info = await self._fetch_channel_info(channel_id)
            
            # 캐시 저장 (24시간 TTL)
            await self.cache_service.set(cache_key, channel_info.dict(), ttl=86400)
            
            return channel_info
            
        except Exception as e:
            logger.error(f"채널 정보 조회 실패: {channel_id} - {str(e)}")
            raise YouTubeAPIError(f"채널 정보를 조회할 수 없습니다: {str(e)}")
    
    async def get_api_quota(self) -> YouTubeAPIQuota:
        """YouTube API 할당량 정보를 반환합니다."""
        return YouTubeAPIQuota(
            quota_used=self.quota_used,
            quota_limit=self.quota_limit,
            quota_remaining=self.quota_limit - self.quota_used,
            reset_time=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            cost_per_request={
                "search": 100,
                "videos": 1,
                "channels": 1,
                "comments": 1,
                "captions": 200
            }
        )
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID를 추출합니다."""
        # 다양한 YouTube URL 형식 지원
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _fetch_video_info(self, video_id: str) -> YouTubeVideoInfo:
        """YouTube API를 통해 영상 정보를 가져옵니다."""
        if not self.api_key:
            raise YouTubeAPIError("YouTube API 키가 설정되지 않았습니다.")
        
        if not self._check_quota("videos"):
            raise YouTubeAPIError("YouTube API 할당량이 부족합니다.")
        
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
            "key": self.api_key
        }
        
        response = await self.client.get(f"{self.base_url}/videos", params=params)
        response.raise_for_status()
        
        data = response.json()
        self._update_quota("videos")
        
        if not data.get("items"):
            raise ValidationError(f"영상을 찾을 수 없습니다: {video_id}")
        
        item = data["items"][0]
        snippet = item["snippet"]
        statistics = item["statistics"]
        content_details = item["contentDetails"]
        
        return YouTubeVideoInfo(
            video_id=video_id,
            title=snippet["title"],
            description=snippet["description"],
            channel_id=snippet["channelId"],
            channel_title=snippet["channelTitle"],
            published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
            duration=content_details["duration"],
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else None,
            dislike_count=int(statistics.get("dislikeCount", 0)) if statistics.get("dislikeCount") else None,
            comment_count=int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else None,
            tags=snippet.get("tags", []),
            category_id=snippet["categoryId"],
            category_title=snippet.get("categoryId", "Unknown"),  # 카테고리명은 별도 API 호출 필요
            language=snippet.get("defaultLanguage"),
            region_restriction=snippet.get("regionRestriction"),
            thumbnails=snippet["thumbnails"],
            live_broadcast_content=snippet["liveBroadcastContent"],
            default_audio_language=snippet.get("defaultAudioLanguage"),
            default_language=snippet.get("defaultLanguage")
        )
    
    async def _fetch_channel_info(self, channel_id: str) -> YouTubeChannelInfo:
        """YouTube API를 통해 채널 정보를 가져옵니다."""
        if not self.api_key:
            raise YouTubeAPIError("YouTube API 키가 설정되지 않았습니다.")
        
        if not self._check_quota("channels"):
            raise YouTubeAPIError("YouTube API 할당량이 부족합니다.")
        
        params = {
            "part": "snippet,statistics,brandingSettings",
            "id": channel_id,
            "key": self.api_key
        }
        
        response = await self.client.get(f"{self.base_url}/channels", params=params)
        response.raise_for_status()
        
        data = response.json()
        self._update_quota("channels")
        
        if not data.get("items"):
            raise ValidationError(f"채널을 찾을 수 없습니다: {channel_id}")
        
        item = data["items"][0]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        branding = item.get("brandingSettings", {})
        
        return YouTubeChannelInfo(
            channel_id=channel_id,
            title=snippet["title"],
            description=snippet["description"],
            custom_url=snippet.get("customUrl"),
            published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
            subscriber_count=int(statistics.get("subscriberCount", 0)) if statistics.get("subscriberCount") else None,
            video_count=int(statistics.get("videoCount", 0)),
            view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
            country=snippet.get("country"),
            language=snippet.get("defaultLanguage"),
            topic_categories=snippet.get("topicCategories", []),
            thumbnails=snippet["thumbnails"],
            banner_external_url=branding.get("image", {}).get("bannerExternalUrl")
        )
    
    async def _fetch_transcript(self, video_id: str) -> Optional[YouTubeTranscript]:
        """YouTube 자막을 가져옵니다."""
        try:
            # YouTube 자막 API는 별도 라이브러리 필요 (youtube-transcript-api)
            # 현재는 기본 구조만 구현
            logger.info(f"자막 수집 기능은 아직 구현되지 않음: {video_id}")
            return None
            
        except Exception as e:
            logger.warning(f"자막 수집 실패: {video_id} - {str(e)}")
            return None
    
    async def _fetch_comments(self, video_id: str) -> List[YouTubeComment]:
        """YouTube 댓글을 가져옵니다."""
        try:
            if not self.api_key:
                logger.warning("YouTube API 키가 없어 댓글을 수집할 수 없습니다.")
                return []
            
            if not self._check_quota("comments"):
                logger.warning("YouTube API 할당량이 부족하여 댓글을 수집할 수 없습니다.")
                return []
            
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 100,  # 최대 100개 댓글
                "key": self.api_key
            }
            
            response = await self.client.get(f"{self.base_url}/commentThreads", params=params)
            response.raise_for_status()
            
            data = response.json()
            self._update_quota("comments")
            
            comments = []
            for item in data.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comment = YouTubeComment(
                    comment_id=item["id"],
                    author_name=snippet["authorDisplayName"],
                    author_channel_id=snippet.get("authorChannelId", {}).get("value"),
                    text=snippet["textDisplay"],
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    like_count=snippet["likeCount"],
                    reply_count=item["snippet"]["totalReplyCount"],
                    is_author_channel_owner=snippet["authorChannelId"]["value"] == snippet.get("channelId")
                )
                comments.append(comment)
            
            logger.info(f"댓글 수집 완료: {video_id} - {len(comments)}개")
            return comments
            
        except Exception as e:
            logger.warning(f"댓글 수집 실패: {video_id} - {str(e)}")
            return []
    
    async def _analyze_comment_sentiment(self, comments: List[YouTubeComment]) -> Optional[Dict[str, float]]:
        """댓글 감정 분석을 수행합니다."""
        try:
            if not comments:
                return None
            
            # TODO: 실제 감정 분석 AI 모델 연동
            # 현재는 기본 통계만 반환
            total_comments = len(comments)
            positive_count = sum(1 for c in comments if any(word in c.text.lower() for word in ["좋아", "최고", "훌륭", "감사"]))
            negative_count = sum(1 for c in comments if any(word in c.text.lower() for word in ["싫어", "최악", "별로", "실망"]))
            
            return {
                "positive": positive_count / total_comments,
                "negative": negative_count / total_comments,
                "neutral": (total_comments - positive_count - negative_count) / total_comments
            }
            
        except Exception as e:
            logger.warning(f"댓글 감정 분석 실패: {str(e)}")
            return None
    
    def _parse_duration(self, duration: str) -> int:
        """ISO 8601 duration을 초 단위로 변환합니다."""
        try:
            # PT4M13S -> 253초
            import re
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
            return 0
        except:
            return 0
    
    def _calculate_like_ratio(self, likes: Optional[int], dislikes: Optional[int]) -> Optional[float]:
        """좋아요 비율을 계산합니다."""
        if not likes and not dislikes:
            return None
        
        total = (likes or 0) + (dislikes or 0)
        if total == 0:
            return None
        
        return (likes or 0) / total
    
    def _calculate_engagement_rate(self, views: int, likes: Optional[int], comments: Optional[int]) -> Optional[float]:
        """참여율을 계산합니다."""
        if views == 0:
            return None
        
        engagement = (likes or 0) + (comments or 0)
        return engagement / views
    
    def _check_quota(self, operation: str) -> bool:
        """API 할당량을 확인합니다."""
        # 간단한 할당량 체크 (실제로는 더 정교한 관리 필요)
        return self.quota_used < self.quota_limit
    
    def _update_quota(self, operation: str):
        """API 할당량을 업데이트합니다."""
        # 기본 할당량 비용
        costs = {
            "search": 100,
            "videos": 1,
            "channels": 1,
            "comments": 1,
            "captions": 200
        }
        
        cost = costs.get(operation, 1)
        self.quota_used += cost
        
        logger.debug(f"YouTube API 할당량 사용: {operation} (+{cost}), 총 사용량: {self.quota_used}")
    
    async def close(self):
        """서비스를 종료합니다."""
        await self.client.aclose()
        logger.info("YouTube 서비스 종료됨")
