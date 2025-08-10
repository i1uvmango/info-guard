#!/usr/bin/env python3
"""
YouTube API 연동 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processing.youtube_client import YouTubeClient


async def test_youtube_client():
    """YouTube 클라이언트 테스트"""
    print("🎬 YouTube API 연동 테스트 시작")
    print("=" * 50)
    
    # 클라이언트 초기화
    client = YouTubeClient()
    
    # 할당량 상태 확인
    quota_status = client.get_quota_status()
    print(f"📊 API 할당량 상태:")
    print(f"   - 사용된 할당량: {quota_status['quota_used']}")
    print(f"   - 남은 할당량: {quota_status['quota_remaining']}")
    print(f"   - 사용 가능한 API 키: {quota_status['api_keys_available']}개")
    print()
    
    # 테스트용 YouTube URL (간단한 영상)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll 영상
    
    # Video ID 추출 테스트
    print("🔍 Video ID 추출 테스트")
    video_id = client.extract_video_id(test_url)
    print(f"   - URL: {test_url}")
    print(f"   - 추출된 Video ID: {video_id}")
    print()
    
    if video_id:
        # 영상 정보 조회 테스트
        print("📹 영상 정보 조회 테스트")
        try:
            video_info = await client.get_video_info(video_id)
            if video_info:
                print(f"   - 제목: {video_info['title']}")
                print(f"   - 채널: {video_info['channel_name']}")
                print(f"   - 조회수: {video_info['view_count']:,}")
                print(f"   - 좋아요: {video_info['like_count']:,}")
                print(f"   - 댓글: {video_info['comment_count']:,}")
                print(f"   - 업로드 날짜: {video_info['published_at']}")
            else:
                print("   ❌ 영상 정보를 가져올 수 없습니다.")
        except Exception as e:
            print(f"   ❌ 영상 정보 조회 실패: {e}")
        print()
        
        # 채널 정보 조회 테스트
        if video_info and video_info.get('channel_id'):
            print("📺 채널 정보 조회 테스트")
            try:
                channel_info = await client.get_channel_info(video_info['channel_id'])
                if channel_info:
                    print(f"   - 채널명: {channel_info['channel_name']}")
                    print(f"   - 구독자 수: {channel_info['subscriber_count']:,}")
                    print(f"   - 영상 수: {channel_info['video_count']:,}")
                    print(f"   - 총 조회수: {channel_info['view_count']:,}")
                else:
                    print("   ❌ 채널 정보를 가져올 수 없습니다.")
            except Exception as e:
                print(f"   ❌ 채널 정보 조회 실패: {e}")
            print()
        
        # 자막 추출 테스트
        print("📝 자막 추출 테스트")
        try:
            transcript = await client.get_video_transcript(video_id)
            if transcript:
                print(f"   - 자막 길이: {len(transcript)} 문자")
                print(f"   - 자막 미리보기: {transcript[:100]}...")
            else:
                print("   ❌ 자막을 찾을 수 없습니다.")
        except Exception as e:
            print(f"   ❌ 자막 추출 실패: {e}")
        print()
        
        # 댓글 조회 테스트 (최대 5개)
        print("💬 댓글 조회 테스트")
        try:
            comments = await client.get_video_comments(video_id, max_results=5)
            if comments:
                print(f"   - 댓글 수: {len(comments)}개")
                for i, comment in enumerate(comments[:3], 1):
                    print(f"   - 댓글 {i}: {comment['author_name']} - {comment['text'][:50]}...")
            else:
                print("   ❌ 댓글을 가져올 수 없습니다.")
        except Exception as e:
            print(f"   ❌ 댓글 조회 실패: {e}")
        print()
    
    # 최종 할당량 상태 확인
    final_quota = client.get_quota_status()
    print("📊 최종 API 할당량 상태:")
    print(f"   - 사용된 할당량: {final_quota['quota_used']}")
    print(f"   - 남은 할당량: {final_quota['quota_remaining']}")
    print(f"   - 총 요청 수: {final_quota['request_count']}")
    print()
    
    # 클라이언트 정리
    await client.close()
    
    print("✅ YouTube API 연동 테스트 완료!")


if __name__ == "__main__":
    # 이벤트 루프 실행
    asyncio.run(test_youtube_client())
