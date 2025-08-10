#!/usr/bin/env python3
"""
YouTube 클라이언트 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processing.youtube_client import YouTubeClient
from utils.logger import setup_logging


async def test_youtube_client():
    """YouTube 클라이언트 테스트"""
    setup_logging()
    
    # YouTube 클라이언트 초기화
    client = YouTubeClient()
    
    try:
        # 테스트용 YouTube URL (한국어 영상)
        test_url = "https://www.youtube.com/watch?v=9bZkp7q19f0"  # PSY - GANGNAM STYLE (한국어)
        
        print("🎬 YouTube 클라이언트 테스트 시작...")
        print(f"📺 테스트 URL: {test_url}")
        
        # Video ID 추출 테스트
        print("\n1️⃣ Video ID 추출 테스트...")
        video_id = client.extract_video_id(test_url)
        print(f"   추출된 Video ID: {video_id}")
        
        if not video_id:
            print("   ❌ Video ID 추출 실패")
            return
        
        # 영상 정보 조회 테스트
        print("\n2️⃣ 영상 정보 조회 테스트...")
        video_info = await client.get_video_info(video_id)
        if video_info:
            print(f"   제목: {video_info.get('title', 'N/A')}")
            print(f"   채널: {video_info.get('channel_name', 'N/A')}")
            print(f"   조회수: {video_info.get('view_count', 'N/A'):,}")
            print(f"   좋아요: {video_info.get('like_count', 'N/A'):,}")
        else:
            print("   ❌ 영상 정보 조회 실패")
        
        # 자막 추출 테스트
        print("\n3️⃣ 자막 추출 테스트...")
        transcript = await client.get_video_transcript(video_id)
        if transcript:
            print(f"   자막 길이: {len(transcript)} 문자")
            print(f"   자막 미리보기: {transcript[:200]}...")
        else:
            print("   ❌ 자막 추출 실패 (자막이 없거나 비공개일 수 있음)")
        
        # 채널 정보 조회 테스트
        if video_info and video_info.get('channel_id'):
            print("\n4️⃣ 채널 정보 조회 테스트...")
            channel_info = await client.get_channel_info(video_info['channel_id'])
            if channel_info:
                print(f"   채널명: {channel_info.get('channel_name', 'N/A')}")
                print(f"   구독자 수: {channel_info.get('subscriber_count', 'N/A'):,}")
            else:
                print("   ❌ 채널 정보 조회 실패")
        
        # 영상 검색 테스트
        print("\n5️⃣ 영상 검색 테스트...")
        search_results = await client.search_videos("인공지능", max_results=3)
        if search_results:
            print(f"   검색 결과: {len(search_results)}개")
            for i, video in enumerate(search_results[:2], 1):
                print(f"   {i}. {video.get('title', 'N/A')}")
        else:
            print("   ❌ 영상 검색 실패")
        
        print("\n✅ YouTube 클라이언트 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 클라이언트 정리
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_youtube_client())
