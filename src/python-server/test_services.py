#!/usr/bin/env python3
"""
서비스 테스트 스크립트
각 서비스가 제대로 작동하는지 확인합니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging import get_logger
from app.services import initialize_services, cleanup_services
from app.services.cache import cache_service
from app.services.ai_models import ai_model_service
from app.services.youtube import YouTubeService

logger = get_logger(__name__)


async def test_cache_service():
    """캐시 서비스 테스트"""
    logger.info("🧪 캐시 서비스 테스트 시작")
    
    try:
        # 연결 테스트
        await cache_service.connect()
        
        # 기본 캐시 작업 테스트
        test_key = "test_key"
        test_value = {"message": "Hello, Cache!", "number": 42}
        
        # 저장 테스트
        success = await cache_service.set(test_key, test_value, ttl=60)
        if success:
            logger.info("✅ 캐시 저장 성공")
        else:
            logger.error("❌ 캐시 저장 실패")
            return False
        
        # 조회 테스트
        retrieved_value = await cache_service.get(test_key)
        if retrieved_value == test_value:
            logger.info("✅ 캐시 조회 성공")
        else:
            logger.error("❌ 캐시 조회 실패")
            return False
        
        # 삭제 테스트
        delete_success = await cache_service.delete(test_key)
        if delete_success:
            logger.info("✅ 캐시 삭제 성공")
        else:
            logger.error("❌ 캐시 삭제 실패")
            return False
        
        # 통계 조회 테스트
        stats = await cache_service.get_stats()
        logger.info(f"📊 캐시 통계: {stats}")
        
        logger.info("✅ 캐시 서비스 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 캐시 서비스 테스트 실패: {e}")
        return False


async def test_ai_model_service():
    """AI 모델 서비스 테스트"""
    logger.info("🧪 AI 모델 서비스 테스트 시작")
    
    try:
        # 모델 상태 확인
        status = await ai_model_service.get_model_status()
        logger.info(f"📊 AI 모델 상태: {status}")
        
        # 간단한 분석 테스트
        test_text = "이것은 테스트 텍스트입니다. 신뢰할 수 있는 정보를 제공합니다."
        
        # 전체 분석 테스트
        result = await ai_model_service.analyze_content(
            test_text, 
            analysis_type="full"
        )
        
        if result:
            logger.info(f"✅ AI 분석 완료: {result.analysis_type}")
            logger.info(f"⏱️ 처리 시간: {result.processing_time:.2f}초")
        else:
            logger.error("❌ AI 분석 실패")
            return False
        
        logger.info("✅ AI 모델 서비스 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI 모델 서비스 테스트 실패: {e}")
        return False


async def test_youtube_service():
    """YouTube 서비스 테스트"""
    logger.info("🧪 YouTube 서비스 테스트 시작")
    
    try:
        # YouTube 서비스 인스턴스 생성
        youtube_service = YouTubeService(cache_service)
        
        # API 키 확인
        if not youtube_service.api_key:
            logger.warning("⚠️ YouTube API 키가 설정되지 않음 - 일부 테스트 건너뜀")
            return True
        
        # 서비스 초기화 확인
        logger.info("✅ YouTube 서비스 초기화 성공")
        
        # API 할당량 확인
        quota_info = await youtube_service.get_api_quota()
        logger.info(f"📊 YouTube API 할당량: {quota_info}")
        
        logger.info("✅ YouTube 서비스 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ YouTube 서비스 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    logger.info("🚀 서비스 테스트 시작")
    
    try:
        # 서비스 초기화
        logger.info("🔧 서비스 초기화 중...")
        if not await initialize_services():
            logger.error("❌ 서비스 초기화 실패")
            return 1
        
        # 각 서비스 테스트
        tests = [
            test_cache_service,
            test_ai_model_service,
            test_youtube_service
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                logger.error(f"테스트 실행 중 오류: {e}")
                results.append(False)
        
        # 결과 요약
        passed = sum(results)
        total = len(results)
        
        logger.info(f"📊 테스트 결과: {passed}/{total} 통과")
        
        if passed == total:
            logger.info("🎉 모든 테스트 통과!")
            return 0
        else:
            logger.error("❌ 일부 테스트 실패")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패: {e}")
        return 1
        
    finally:
        # 서비스 정리
        logger.info("🧹 서비스 정리 중...")
        await cleanup_services()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
