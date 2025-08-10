#!/usr/bin/env python3
"""
콘텐츠 분류 모델 학습을 위한 데이터 수집 스크립트

유튜브 API를 사용하여 정치/경제/시사/기타 콘텐츠 데이터를 수집합니다.
"""

import os
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta
import random

# Google API 클라이언트
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("google-api-python-client가 설치되지 않았습니다.")
    print("pip install google-api-python-client를 실행하세요.")
    exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeDataCollector:
    """유튜브 데이터 수집 클래스"""
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: YouTube Data API v3 키
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 카테고리별 검색 키워드
        self.category_keywords = {
            "정치": [
                "정치", "대통령", "국회", "의원", "정부", "여당", "야당", "선거", "투표",
                "민주주의", "자유주의", "보수", "진보", "정책", "법안", "헌법", "국정감사"
            ],
            "경제": [
                "경제", "주식", "부동산", "금리", "인플레이션", "GDP", "수출", "수입",
                "기업", "주식시장", "환율", "원화", "달러", "투자", "재정", "부동산시장"
            ],
            "시사": [
                "뉴스", "사건", "사고", "범죄", "재난", "사망", "부상", "교통사고",
                "화재", "지진", "태풍", "홍수", "사회", "이슈", "핫이슈"
            ],
            "기타": [
                "엔터테인먼트", "음악", "영화", "드라마", "예능", "게임", "스포츠",
                "요리", "여행", "패션", "뷰티", "건강", "교육", "테크", "IT"
            ]
        }
        
        # 데이터 저장 경로
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_category_data(self, category: str, max_results: int = 100) -> List[Dict]:
        """
        특정 카테고리의 데이터를 수집합니다.
        
        Args:
            category: 수집할 카테고리
            max_results: 최대 수집 결과 수
            
        Returns:
            수집된 데이터 리스트
        """
        logger.info(f"{category} 카테고리 데이터 수집 시작...")
        
        collected_data = []
        keywords = self.category_keywords[category]
        
        for keyword in keywords:
            try:
                logger.info(f"키워드 '{keyword}' 검색 중...")
                
                # 검색 요청
                search_response = self.youtube.search().list(
                    q=keyword,
                    part='id,snippet',
                    maxResults=min(50, max_results // len(keywords)),
                    type='video',
                    videoDuration='medium',  # 중간 길이 영상
                    order='relevance',
                    publishedAfter=(datetime.now() - timedelta(days=365)).isoformat() + 'Z'
                ).execute()
                
                # 비디오 정보 수집
                for item in search_response.get('items', []):
                    video_id = item['id']['videoId']
                    video_data = self._get_video_details(video_id)
                    
                    if video_data:
                        video_data['category'] = category
                        video_data['collected_at'] = datetime.now().isoformat()
                        collected_data.append(video_data)
                
                # API 제한 방지
                time.sleep(0.1)
                
            except HttpError as e:
                logger.error(f"키워드 '{keyword}' 검색 실패: {e}")
                continue
        
        logger.info(f"{category} 카테고리 수집 완료: {len(collected_data)}개")
        return collected_data
    
    def _get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        비디오 상세 정보를 가져옵니다.
        
        Args:
            video_id: 유튜브 비디오 ID
            
        Returns:
            비디오 상세 정보
        """
        try:
            # 비디오 정보 요청
            video_response = self.youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                return None
            
            video = video_response['items'][0]
            snippet = video['snippet']
            statistics = video.get('statistics', {})
            
            return {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'tags': snippet.get('tags', []),
                'category_id': snippet.get('categoryId', ''),
                'published_at': snippet.get('publishedAt', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0))
            }
            
        except HttpError as e:
            logger.error(f"비디오 {video_id} 상세 정보 조회 실패: {e}")
            return None
    
    def collect_all_categories(self, max_results_per_category: int = 100) -> Dict[str, List[Dict]]:
        """
        모든 카테고리의 데이터를 수집합니다.
        
        Args:
            max_results_per_category: 카테고리당 최대 수집 결과 수
            
        Returns:
            카테고리별 수집된 데이터
        """
        all_data = {}
        
        for category in self.category_keywords.keys():
            category_data = self.collect_category_data(category, max_results_per_category)
            all_data[category] = category_data
            
            # API 제한 방지
            time.sleep(1)
        
        return all_data
    
    def save_data(self, data: Dict[str, List[Dict]], filename: str = None) -> str:
        """
        수집된 데이터를 파일로 저장합니다.
        
        Args:
            data: 저장할 데이터
            filename: 파일명 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"youtube_data_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"데이터 저장 완료: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            raise
    
    def create_training_dataset(self, data: Dict[str, List[Dict]], output_filename: str = None) -> str:
        """
        학습용 데이터셋을 생성합니다.
        
        Args:
            data: 원본 데이터
            output_filename: 출력 파일명
            
        Returns:
            생성된 파일 경로
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"training_dataset_{timestamp}.json"
        
        training_data = []
        category_mapping = {"정치": 0, "경제": 1, "시사": 2, "기타": 3}
        
        for category, videos in data.items():
            category_id = category_mapping[category]
            
            for video in videos:
                training_item = {
                    'title': video['title'],
                    'description': video['description'],
                    'tags': video['tags'],
                    'category': category_id,
                    'category_name': category,
                    'video_id': video['video_id'],
                    'metadata': {
                        'view_count': video['view_count'],
                        'like_count': video['like_count'],
                        'comment_count': video['comment_count'],
                        'published_at': video['published_at']
                    }
                }
                training_data.append(training_item)
        
        # 파일 저장
        output_path = self.data_dir / output_filename
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"학습용 데이터셋 생성 완료: {output_path}")
            logger.info(f"총 {len(training_data)}개 샘플")
            
            # 카테고리별 분포 출력
            category_counts = {}
            for item in training_data:
                cat = item['category_name']
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            for cat, count in category_counts.items():
                logger.info(f"  {cat}: {count}개")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"학습용 데이터셋 생성 실패: {e}")
            raise


def main():
    """메인 함수"""
    # API 키 확인
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        logger.error("YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.")
        logger.error("export YOUTUBE_API_KEY='your_api_key'를 실행하세요.")
        return
    
    # 데이터 수집기 생성
    collector = YouTubeDataCollector(api_key)
    
    try:
        logger.info("유튜브 데이터 수집 시작...")
        
        # 모든 카테고리 데이터 수집
        all_data = collector.collect_all_categories(max_results_per_category=50)
        
        # 원본 데이터 저장
        collector.save_data(all_data)
        
        # 학습용 데이터셋 생성
        training_dataset_path = collector.create_training_dataset(all_data)
        
        logger.info("데이터 수집 완료!")
        logger.info(f"학습용 데이터셋: {training_dataset_path}")
        
    except Exception as e:
        logger.error(f"데이터 수집 실패: {e}")
        raise


if __name__ == "__main__":
    main()
