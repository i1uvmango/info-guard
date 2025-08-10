import re
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from ..config.logging_config import get_logger, metrics_logger
    from ..config.settings import settings
except ImportError:
    from config.logging_config import get_logger, metrics_logger
    from config.settings import settings

class YouTubeService:
    """
    YouTube API 연동 서비스
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.api_key = settings.YOUTUBE_API_KEY
        
        if self.api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        else:
            self.youtube = None
            self.logger.warning("YouTube API 키가 설정되지 않았습니다.")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        YouTube URL에서 비디오 ID를 추출합니다.
        """
        try:
            # 다양한 YouTube URL 형식 지원
            patterns = [
                r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
                r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
                r'youtu\.be\/([^&\n?#]+)',
                r'youtube\.com\/embed\/([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.error(f"비디오 ID 추출 실패: {url}, 오류: {str(e)}")
            return None
    
    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        비디오 정보를 가져옵니다.
        """
        import time
        start_time = time.time()
        
        try:
            if not self.youtube:
                return self._get_video_info_fallback(video_id)
            
            # YouTube API 호출
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                raise ValueError(f"비디오를 찾을 수 없습니다: {video_id}")
            
            video_data = response['items'][0]
            snippet = video_data['snippet']
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            # 채널 정보 가져오기
            channel_info = self._get_channel_info(snippet.get('channelId', ''))
            
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("youtube_service_get_info", processing_time)
            
            result = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'duration': content_details.get('duration', ''),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'subscriber_count': channel_info.get('subscriber_count', 0),
                'channel_creation_date': channel_info.get('creation_date', ''),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'processing_time': processing_time
            }
            
            self.logger.info(
                "비디오 정보 가져오기 완료",
                video_id=video_id,
                title=result['title'][:50],
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"비디오 정보 가져오기 실패: {video_id}, 오류: {str(e)}")
            metrics_logger.log_error("youtube_service", str(e))
            raise
    
    def _get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        채널 정보를 가져옵니다.
        """
        try:
            if not self.youtube or not channel_id:
                return {}
            
            request = self.youtube.channels().list(
                part='statistics,snippet',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                return {}
            
            channel_data = response['items'][0]
            statistics = channel_data.get('statistics', {})
            snippet = channel_data.get('snippet', {})
            
            return {
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'view_count': int(statistics.get('viewCount', 0)),
                'creation_date': snippet.get('publishedAt', ''),
                'description': snippet.get('description', ''),
                'country': snippet.get('country', '')
            }
            
        except Exception as e:
            self.logger.warning(f"채널 정보 가져오기 실패: {channel_id}, 오류: {str(e)}")
            return {}
    
    def _get_video_info_fallback(self, video_id: str) -> Dict[str, Any]:
        """
        API 키가 없을 때 기본 정보만 반환합니다.
        """
        return {
            'video_id': video_id,
            'title': '',
            'description': '',
            'channel_id': '',
            'channel_title': '',
            'published_at': '',
            'duration': '',
            'view_count': 0,
            'like_count': 0,
            'comment_count': 0,
            'subscriber_count': 0,
            'channel_creation_date': '',
            'tags': [],
            'category_id': '',
            'processing_time': 0
        }
    
    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        비디오 자막을 가져옵니다.
        """
        import time
        start_time = time.time()
        
        try:
            # 자막 가져오기
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # 자막 텍스트 결합
            full_text = ' '.join([entry['text'] for entry in transcript_list])
            
            # 자막 통계
            transcript_stats = {
                'total_entries': len(transcript_list),
                'total_duration': sum(entry.get('duration', 0) for entry in transcript_list),
                'avg_entry_duration': sum(entry.get('duration', 0) for entry in transcript_list) / len(transcript_list) if transcript_list else 0
            }
            
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("youtube_service_get_transcript", processing_time)
            
            result = {
                'video_id': video_id,
                'transcript_text': full_text,
                'transcript_entries': transcript_list,
                'transcript_stats': transcript_stats,
                'processing_time': processing_time
            }
            
            self.logger.info(
                "자막 가져오기 완료",
                video_id=video_id,
                entry_count=len(transcript_list),
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"자막 가져오기 실패: {video_id}, 오류: {error_msg}")
            metrics_logger.log_error("youtube_service", error_msg)
            
            # 자막이 없는 경우 빈 결과 반환하되, 에러 정보 포함
            return {
                'video_id': video_id,
                'transcript_text': '',
                'transcript_entries': [],
                'transcript_stats': {
                    'total_entries': 0,
                    'total_duration': 0,
                    'avg_entry_duration': 0
                },
                'processing_time': time.time() - start_time,
                'transcript_error': error_msg,
                'transcript_available': False
            }
    
    def get_comments(self, video_id: str, max_results: int = 100) -> Dict[str, Any]:
        """
        비디오 댓글을 가져옵니다.
        """
        import time
        start_time = time.time()
        
        try:
            if not self.youtube:
                return {
                    'video_id': video_id,
                    'comments': [],
                    'comment_count': 0,
                    'processing_time': time.time() - start_time
                }
            
            # 댓글 가져오기
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                order='relevance'
            )
            response = request.execute()
            
            comments = []
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment.get('authorDisplayName', ''),
                    'text': comment.get('textDisplay', ''),
                    'like_count': comment.get('likeCount', 0),
                    'published_at': comment.get('publishedAt', ''),
                    'updated_at': comment.get('updatedAt', '')
                })
            
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("youtube_service_get_comments", processing_time)
            
            result = {
                'video_id': video_id,
                'comments': comments,
                'comment_count': len(comments),
                'processing_time': processing_time
            }
            
            self.logger.info(
                "댓글 가져오기 완료",
                video_id=video_id,
                comment_count=len(comments),
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"댓글 가져오기 실패: {video_id}, 오류: {str(e)}")
            metrics_logger.log_error("youtube_service", str(e))
            
            return {
                'video_id': video_id,
                'comments': [],
                'comment_count': 0,
                'processing_time': time.time() - start_time
            }
    
    def analyze_video(self, url: str) -> Dict[str, Any]:
        """
        YouTube 비디오를 종합적으로 분석합니다.
        """
        import time
        start_time = time.time()
        
        try:
            # 비디오 ID 추출
            video_id = self.extract_video_id(url)
            if not video_id:
                raise ValueError(f"유효하지 않은 YouTube URL입니다: {url}")
            
            # 비디오 정보 가져오기
            video_info = self.get_video_info(video_id)
            
            # 자막 가져오기
            transcript_info = self.get_transcript(video_id)
            
            # 댓글 가져오기 (선택적)
            comments_info = self.get_comments(video_id, max_results=50)
            
            processing_time = time.time() - start_time
            metrics_logger.log_analysis_time("youtube_service_analyze", processing_time)
            
            result = {
                'url': url,
                'video_id': video_id,
                'video_info': video_info,
                'transcript_info': transcript_info,
                'comments_info': comments_info,
                'processing_time': processing_time
            }
            
            self.logger.info(
                "YouTube 비디오 분석 완료",
                video_id=video_id,
                title=video_info.get('title', '')[:50],
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"YouTube 비디오 분석 실패: {url}, 오류: {str(e)}")
            metrics_logger.log_error("youtube_service", str(e))
            raise
    
    def get_video_data(self, video_id: str) -> Dict[str, Any]:
        """
        비디오 데이터를 가져옵니다 (main.py에서 사용).
        """
        try:
            # 비디오 정보 가져오기
            video_info = self.get_video_info(video_id)
            
            # 자막 가져오기
            transcript_info = self.get_transcript(video_id)
            
            # 통합 데이터 반환
            result = {
                'video_id': video_id,
                'transcript': transcript_info.get('transcript', ''),
                'metadata': video_info,
                'channel_info': {
                    'channel_id': video_info.get('channel_id', ''),
                    'channel_title': video_info.get('channel_title', ''),
                    'subscriber_count': video_info.get('subscriber_count', 0),
                    'channel_creation_date': video_info.get('channel_creation_date', '')
                }
            }
            
            self.logger.info(f"비디오 데이터 가져오기 완료: {video_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"비디오 데이터 가져오기 실패: {video_id}, 오류: {str(e)}")
            # 기본 데이터 반환
            return {
                'video_id': video_id,
                'transcript': '',
                'metadata': {},
                'channel_info': {}
            }

    def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        비디오 메타데이터만 가져옵니다.
        """
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                raise ValueError(f"유효하지 않은 YouTube URL입니다: {url}")
            
            video_info = self.get_video_info(video_id)
            
            # 분석에 필요한 메타데이터만 반환
            metadata = {
                'video_id': video_id,
                'title': video_info.get('title', ''),
                'description': video_info.get('description', ''),
                'channel_title': video_info.get('channel_title', ''),
                'view_count': video_info.get('view_count', 0),
                'like_count': video_info.get('like_count', 0),
                'comment_count': video_info.get('comment_count', 0),
                'subscriber_count': video_info.get('subscriber_count', 0),
                'channel_creation_date': video_info.get('channel_creation_date', ''),
                'published_at': video_info.get('published_at', ''),
                'duration': video_info.get('duration', ''),
                'tags': video_info.get('tags', [])
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"메타데이터 가져오기 실패: {url}, 오류: {str(e)}")
            raise 