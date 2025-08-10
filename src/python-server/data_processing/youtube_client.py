"""
YouTube API 클라이언트
YouTube 영상 정보 및 자막을 수집하는 모듈
"""

import os
import re
import logging
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import asyncio
import httpx
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from utils.config import settings
from utils.security import mask_api_key, secure_logging


class YouTubeClient:
    """YouTube API 클라이언트"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.youtube_service = None
        self.logger = logging.getLogger(__name__)
        
        # HTTP 클라이언트 (자막 다운로드용)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # API 요청 제한 관리
        self.quota_used = 0
        self.quota_limit = 10000  # YouTube API 일일 할당량
        self.request_count = 0
        self.last_request_time = None
        self.rate_limit_delay = 0.1  # 초당 최대 10개 요청
        
        # API 키 순환 관리
        self.api_keys = self._get_api_keys()
        self.current_key_index = 0
        
        # YouTube 서비스 초기화
        self._init_youtube_service()
    
    def _get_api_key(self) -> str:
        """API 키 가져오기 (환경변수 또는 설정 파일에서)"""
        # 환경변수에서 먼저 확인
        api_key = os.getenv('YOUTUBE_API_KEY')
        if api_key:
            return api_key
        
        # 설정 파일에서 확인
        if hasattr(settings, 'YOUTUBE_API_KEY') and settings.YOUTUBE_API_KEY:
            return settings.YOUTUBE_KEY
        
        # 기본 설정 파일에서 확인
        try:
            from utils.config import settings
            return getattr(settings, 'YOUTUBE_API_KEY', '')
        except ImportError:
            pass
        
        # API 키가 없을 때만 경고 (키 자체는 로그에 출력하지 않음)
        self.logger.warning("YouTube API 키를 찾을 수 없습니다. 환경변수 YOUTUBE_API_KEY를 설정하세요.")
        return ""
    
    def _get_api_keys(self) -> List[str]:
        """여러 API 키 가져오기 (키 순환용)"""
        keys = []
        
        # 단일 API 키
        if self.api_key:
            keys.append(self.api_key)
        
        # 추가 API 키들 (환경변수에서)
        for i in range(1, 6):  # 최대 5개 키 지원
            key = os.getenv(f'YOUTUBE_API_KEY_{i}')
            if key:
                keys.append(key)
        
        # 설정 파일에서 추가 키들
        try:
            if hasattr(settings, 'YOUTUBE_API_KEYS') and isinstance(settings.YOUTUBE_API_KEYS, list):
                keys.extend(settings.YOUTUBE_API_KEYS)
        except:
            pass
        
        return list(set(keys))  # 중복 제거
    
    def _init_youtube_service(self):
        """YouTube 서비스 초기화"""
        if not self.api_keys:
            self.logger.error("사용 가능한 YouTube API 키가 없습니다.")
            return
        
        try:
            self.youtube_service = build('youtube', 'v3', developerKey=self.api_keys[self.current_key_index])
            self.logger.info(f"YouTube API 서비스 초기화 완료 (키 {self.current_key_index + 1}/{len(self.api_keys)})")
        except Exception as e:
            self.logger.error(f"YouTube 서비스 초기화 실패: {e}")
    
    def _rotate_api_key(self):
        """API 키 순환"""
        if len(self.api_keys) <= 1:
            return False
        
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._init_youtube_service()
        self.logger.info(f"API 키를 {self.current_key_index + 1}번째로 순환")
        return True
    
    def _check_quota(self) -> bool:
        """할당량 확인"""
        if self.quota_used >= self.quota_limit:
            self.logger.warning("일일 API 할당량을 초과했습니다.")
            return False
        return True
    
    def _update_quota(self, cost: int = 1):
        """할당량 업데이트"""
        self.quota_used += cost
        self.request_count += 1
        
        if self.quota_used % 1000 == 0:
            self.logger.info(f"API 할당량 사용: {self.quota_used}/{self.quota_limit}")
    
    def _rate_limit_delay(self):
        """요청 제한 지연"""
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        
        self.last_request_time = time.time()
    
    def _handle_api_error(self, error: Exception) -> bool:
        """API 에러 처리"""
        if isinstance(error, HttpError):
            error_code = error.resp.status
            if error_code == 403:  # Forbidden
                self.logger.error("API 키 권한 부족 또는 할당량 초과")
                if self._rotate_api_key():
                    return True
            elif error_code == 429:  # Too Many Requests
                self.logger.warning("요청 제한 초과, 지연 후 재시도")
                time.sleep(60)  # 1분 대기
                return True
            elif error_code >= 500:  # 서버 에러
                self.logger.warning(f"YouTube 서버 에러 ({error_code}), 재시도")
                time.sleep(5)
                return True
        
        return False
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """YouTube URL에서 video_id 추출"""
        try:
            # 다양한 YouTube URL 형식 지원
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
                r'youtube\.com/attribution_link\?.*v%3D([a-zA-Z0-9_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # URL 파싱으로 시도
            parsed = urlparse(url)
            if parsed.hostname in ['www.youtube.com', 'youtube.com', 'youtu.be']:
                if parsed.hostname == 'youtu.be':
                    return parsed.path[1:]  # /VIDEO_ID -> VIDEO_ID
                elif parsed.path == '/watch':
                    query_params = parse_qs(parsed.query)
                    return query_params.get('v', [None])[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"URL에서 video_id 추출 실패: {e}")
            return None
    
    async def get_video_info(self, video_id: str, max_retries: int = 3) -> Optional[Dict]:
        """영상 기본 정보 조회"""
        if not self._check_quota():
            return None
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                if not self.youtube_service:
                    self.logger.error("YouTube 서비스가 초기화되지 않았습니다.")
                    return None
                
                # YouTube API로 영상 정보 조회
                request = self.youtube_service.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=video_id
                )
                response = request.execute()
                
                self._update_quota(cost=1)  # videos.list는 1 포인트
                
                if not response.get('items'):
                    self.logger.warning(f"영상을 찾을 수 없음: {video_id}")
                    return None
                
                video_data = response['items'][0]
                snippet = video_data['snippet']
                statistics = video_data.get('statistics', {})
                content_details = video_data.get('contentDetails', {})
                
                return {
                    'video_id': video_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'channel_id': snippet.get('channelId', ''),
                    'channel_name': snippet.get('channelTitle', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'duration': content_details.get('duration', ''),
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'tags': snippet.get('tags', []),
                    'category_id': snippet.get('categoryId', ''),
                    'default_language': snippet.get('defaultLanguage', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'retrieved_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"영상 정보 조회 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if self._handle_api_error(e):
                    continue  # 재시도
                else:
                    break
        
        return None
    
    async def get_video_transcript(self, video_id: str, languages: List[str] = None) -> Optional[str]:
        """영상 자막 추출"""
        try:
            if languages is None:
                languages = ['ko', 'ko-KR', 'en', 'en-US']
            
            transcript = None
            
            # 자막 목록 조회 (버전 호환성 고려)
            try:
                # 최신 버전 방식
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # 선호 언어 순서로 자막 찾기
                for lang in languages:
                    try:
                        if lang in transcript_list:
                            transcript = transcript_list[lang]
                            break
                        elif lang.split('-')[0] in transcript_list:
                            transcript = transcript_list[lang.split('-')[0]]
                            break
                    except Exception:
                        continue
                
                # 자막이 없으면 자동 생성 시도
                if transcript is None:
                    try:
                        transcript = transcript_list.find_transcript(languages)
                    except Exception:
                        pass
                        
            except AttributeError:
                # 구버전 방식
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
                except Exception:
                    # 단일 언어로 시도
                    for lang in languages:
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                            break
                        except Exception:
                            continue
            
            if transcript is None:
                self.logger.warning(f"자막을 찾을 수 없음: {video_id}")
                return None
            
            # 자막을 텍스트로 변환
            if hasattr(transcript, 'fetch'):
                # 최신 버전: transcript 객체
                formatter = TextFormatter()
                transcript_text = formatter.format_transcript(transcript.fetch())
            else:
                # 구버전: 리스트 형태
                transcript_text = ' '.join([item.get('text', '') for item in transcript])
            
            # 텍스트 정리
            cleaned_text = self._clean_transcript(transcript_text)
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"자막 추출 실패: {e}")
            return None
    
    def _clean_transcript(self, text: str) -> str:
        """자막 텍스트 정리"""
        # 불필요한 문자 제거
        text = re.sub(r'\[.*?\]', '', text)  # [음악], [박수] 등 제거
        text = re.sub(r'\(.*?\)', '', text)  # (웃음), (박수) 등 제거
        text = re.sub(r'[^\w\s가-힣]', ' ', text)  # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    async def get_channel_info(self, channel_id: str, max_retries: int = 3) -> Optional[Dict]:
        """채널 정보 조회"""
        if not self._check_quota():
            return None
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                if not self.youtube_service:
                    self.logger.error("YouTube 서비스가 초기화되지 않았습니다.")
                    return None
                
                request = self.youtube_service.channels().list(
                    part='snippet,statistics',
                    id=channel_id
                )
                response = request.execute()
                
                self._update_quota(cost=1)  # channels.list는 1 포인트
                
                if not response.get('items'):
                    return None
                
                channel_data = response['items'][0]
                snippet = channel_data['snippet']
                statistics = channel_data.get('statistics', {})
                
                return {
                    'channel_id': channel_id,
                    'channel_name': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'subscriber_count': int(statistics.get('subscriberCount', 0)),
                    'video_count': int(statistics.get('videoCount', 0)),
                    'view_count': int(statistics.get('viewCount', 0)),
                    'country': snippet.get('country', ''),
                    'language': snippet.get('defaultLanguage', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                    'retrieved_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"채널 정보 조회 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if self._handle_api_error(e):
                    continue  # 재시도
                else:
                    break
        
        return None
    
    async def search_videos(self, query: str, max_results: int = 10, max_retries: int = 3) -> List[Dict]:
        """영상 검색"""
        if not self._check_quota():
            return []
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                if not self.youtube_service:
                    self.logger.error("YouTube 서비스가 초기화되지 않았습니다.")
                    return []
                
                request = self.youtube_service.search().list(
                    part='snippet',
                    q=query,
                    type='video',
                    maxResults=max_results,
                    regionCode='KR',
                    relevanceLanguage='ko'
                )
                response = request.execute()
                
                self._update_quota(cost=100)  # search.list는 100 포인트
                
                videos = []
                for item in response.get('items', []):
                    snippet = item['snippet']
                    videos.append({
                        'video_id': item['id']['videoId'],
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'channel_id': snippet.get('channelId', ''),
                        'channel_name': snippet.get('channelTitle', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                        'retrieved_at': datetime.now().isoformat()
                    })
                
                return videos
                
            except Exception as e:
                self.logger.error(f"영상 검색 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if self._handle_api_error(e):
                    continue  # 재시도
                else:
                    break
        
        return []
    
    async def get_video_comments(self, video_id: str, max_results: int = 100, max_retries: int = 3) -> List[Dict]:
        """영상 댓글 조회"""
        if not self._check_quota():
            return []
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                if not self.youtube_service:
                    self.logger.error("YouTube 서비스가 초기화되지 않았습니다.")
                    return []
                
                request = self.youtube_service.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=max_results,
                    order='relevance'
                )
                response = request.execute()
                
                self._update_quota(cost=1)  # commentThreads.list는 1 포인트
                
                comments = []
                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['id'],
                        'author_name': snippet.get('authorDisplayName', ''),
                        'author_channel_id': snippet.get('authorChannelId', {}).get('value', ''),
                        'text': snippet.get('textDisplay', ''),
                        'like_count': snippet.get('likeCount', 0),
                        'published_at': snippet.get('publishedAt', ''),
                        'updated_at': snippet.get('updatedAt', ''),
                        'retrieved_at': datetime.now().isoformat()
                    })
                
                return comments
                
            except Exception as e:
                self.logger.error(f"댓글 조회 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if self._handle_api_error(e):
                    continue  # 재시도
                else:
                    break
        
        return []
    
    def get_quota_status(self) -> Dict:
        """할당량 상태 조회 (API 키는 마스킹)"""
        return {
            'quota_used': self.quota_used,
            'quota_limit': self.quota_limit,
            'quota_remaining': self.quota_limit - self.quota_used,
            'request_count': self.request_count,
            'api_keys_available': len(self.api_keys),
            'current_key_index': self.current_key_index,
            'last_request_time': datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None,
            'api_key_status': 'configured' if self.api_keys else 'not_configured'
        }
    
    def reset_quota(self):
        """할당량 초기화 (일일 리셋용)"""
        self.quota_used = 0
        self.request_count = 0
        self.logger.info("API 할당량이 초기화되었습니다.")
    
    async def close(self):
        """HTTP 클라이언트 정리"""
        await self.http_client.aclose()
    
    def __del__(self):
        """소멸자에서 정리"""
        if hasattr(self, 'http_client') and self.http_client:
            try:
                # 이벤트 루프가 실행 중이 아닐 때는 동기적으로 처리
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(self.close())
                else:
                    # 이벤트 루프가 없으면 새로 생성하여 실행
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.close())
                    finally:
                        loop.close()
            except Exception:
                # 정리 실패 시 무시
                pass
