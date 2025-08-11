#!/usr/bin/env python3
"""
배치 처리 시스템 테스트 스크립트
배치 처리기가 제대로 작동하는지 확인합니다.
"""

import asyncio
import sys
import os
import time
from typing import List

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logging import get_logger
from app.services.batch_processor import get_batch_processor, BatchProcessor
from app.services.ai_models import ai_model_service

logger = get_logger(__name__)


async def test_batch_processor_basic():
    """기본 배치 처리 테스트"""
    logger.info("🧪 기본 배치 처리 테스트 시작")
    
    try:
        batch_processor = get_batch_processor()
        
        # 상태 확인
        status = batch_processor.get_status()
        logger.info(f"📊 배치 처리기 상태: {status}")
        
        # 간단한 요청 추가
        test_text = "이것은 테스트 텍스트입니다. 신뢰할 수 있는 정보를 제공합니다."
        request_id = await batch_processor.add_request(
            text=test_text,
            analysis_type="full",
            priority=1
        )
        
        logger.info(f"✅ 배치 요청 추가됨: {request_id}")
        
        # 결과 대기
        result = await batch_processor.get_result(request_id, timeout=30.0)
        
        if result:
            logger.info(f"✅ 배치 결과 수신: {result.status}")
            if result.result:
                logger.info(f"📊 분석 결과: {result.result.metadata.analysis_type}")
                logger.info(f"⏱️ 처리 시간: {result.processing_time:.2f}초")
            else:
                logger.error(f"❌ 분석 실패: {result.error}")
        else:
            logger.error("❌ 배치 결과 타임아웃")
            return False
        
        logger.info("✅ 기본 배치 처리 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 기본 배치 처리 테스트 실패: {e}")
        return False


async def test_batch_processor_multiple():
    """다중 요청 배치 처리 테스트"""
    logger.info("🧪 다중 요청 배치 처리 테스트 시작")
    
    try:
        batch_processor = get_batch_processor()
        
        # 여러 테스트 텍스트 준비
        test_texts = [
            "첫 번째 테스트 텍스트입니다. 신뢰할 수 있는 정보입니다.",
            "두 번째 테스트 텍스트입니다. 편향된 관점을 포함할 수 있습니다.",
            "세 번째 테스트 텍스트입니다. 사실 확인이 필요한 내용입니다.",
            "네 번째 테스트 텍스트입니다. 감정적인 표현이 많습니다.",
            "다섯 번째 테스트 텍스트입니다. 객관적인 정보를 제공합니다."
        ]
        
        # 우선순위가 다른 요청들 추가
        request_ids = []
        for i, text in enumerate(test_texts):
            priority = 5 - i  # 첫 번째가 가장 높은 우선순위
            request_id = await batch_processor.add_request(
                text=text,
                analysis_type="full",
                priority=priority
            )
            request_ids.append(request_id)
            logger.info(f"📝 요청 {i+1} 추가됨: {request_id} (우선순위: {priority})")
        
        # 모든 결과 수집
        results = []
        for i, request_id in enumerate(request_ids):
            result = await batch_processor.get_result(request_id, timeout=60.0)
            if result:
                results.append(result)
                logger.info(f"✅ 요청 {i+1} 완료: {result.status}")
                if result.result:
                    logger.info(f"⏱️ 처리 시간: {result.processing_time:.2f}초")
            else:
                logger.error(f"❌ 요청 {i+1} 타임아웃")
        
        # 통계 확인
        success_count = len([r for r in results if r.status == "completed"])
        failed_count = len([r for r in results if r.status == "failed"])
        
        logger.info(f"📊 다중 요청 결과: 성공 {success_count}, 실패 {failed_count}")
        
        if success_count > 0:
            logger.info("✅ 다중 요청 배치 처리 테스트 완료")
            return True
        else:
            logger.error("❌ 모든 요청이 실패함")
            return False
        
    except Exception as e:
        logger.error(f"❌ 다중 요청 배치 처리 테스트 실패: {e}")
        return False


async def test_batch_processor_priority():
    """우선순위 기반 배치 처리 테스트"""
    logger.info("🧪 우선순위 기반 배치 처리 테스트 시작")
    
    try:
        batch_processor = get_batch_processor()
        
        # 낮은 우선순위부터 요청 추가
        low_priority_id = await batch_processor.add_request(
            text="낮은 우선순위 텍스트입니다.",
            analysis_type="full",
            priority=1
        )
        
        # 잠시 대기
        await asyncio.sleep(0.1)
        
        # 높은 우선순위 요청 추가
        high_priority_id = await batch_processor.add_request(
            text="높은 우선순위 텍스트입니다.",
            analysis_type="full",
            priority=10
        )
        
        logger.info(f"📝 낮은 우선순위 요청: {low_priority_id}")
        logger.info(f"📝 높은 우선순위 요청: {high_priority_id}")
        
        # 높은 우선순위 요청이 먼저 완료되는지 확인
        high_result = await batch_processor.get_result(high_priority_id, timeout=30.0)
        low_result = await batch_processor.get_result(low_priority_id, timeout=30.0)
        
        if high_result and low_result:
            logger.info(f"✅ 높은 우선순위 완료: {high_result.status}")
            logger.info(f"✅ 낮은 우선순위 완료: {low_result.status}")
            
            # 처리 시간 비교
            if high_result.processing_time <= low_result.processing_time:
                logger.info("✅ 우선순위가 높은 요청이 먼저 처리됨")
                return True
            else:
                logger.warning("⚠️ 우선순위가 낮은 요청이 먼저 처리됨")
                return False
        else:
            logger.error("❌ 일부 요청이 완료되지 않음")
            return False
        
    except Exception as e:
        logger.error(f"❌ 우선순위 기반 배치 처리 테스트 실패: {e}")
        return False


async def test_batch_processor_stress():
    """스트레스 테스트 - 많은 요청을 동시에 처리"""
    logger.info("🧪 스트레스 테스트 시작")
    
    try:
        batch_processor = get_batch_processor()
        
        # 20개의 요청을 빠르게 추가
        request_ids = []
        start_time = time.time()
        
        for i in range(20):
            text = f"스트레스 테스트 텍스트 {i+1}입니다. 신뢰할 수 있는 정보를 제공합니다."
            request_id = await batch_processor.add_request(
                text=text,
                analysis_type="full",
                priority=1
            )
            request_ids.append(request_id)
        
        add_time = time.time() - start_time
        logger.info(f"📝 20개 요청 추가 완료: {add_time:.2f}초")
        
        # 모든 결과 수집
        results = []
        for i, request_id in enumerate(request_ids):
            result = await batch_processor.get_result(request_id, timeout=120.0)
            if result:
                results.append(result)
                if i % 5 == 0:  # 5개마다 진행상황 로그
                    logger.info(f"📊 진행상황: {i+1}/20 완료")
            else:
                logger.error(f"❌ 요청 {i+1} 타임아웃")
        
        # 통계 확인
        success_count = len([r for r in results if r.status == "completed"])
        failed_count = len([r for r in results if r.status == "failed"])
        total_time = time.time() - start_time
        
        logger.info(f"📊 스트레스 테스트 결과:")
        logger.info(f"   - 총 요청: 20개")
        logger.info(f"   - 성공: {success_count}개")
        logger.info(f"   - 실패: {failed_count}개")
        logger.info(f"   - 총 소요 시간: {total_time:.2f}초")
        logger.info(f"   - 평균 처리 시간: {total_time/20:.2f}초")
        
        if success_count >= 15:  # 75% 이상 성공하면 통과
            logger.info("✅ 스트레스 테스트 통과")
            return True
        else:
            logger.error("❌ 스트레스 테스트 실패")
            return False
        
    except Exception as e:
        logger.error(f"❌ 스트레스 테스트 실패: {e}")
        return False


async def test_batch_processor_monitoring():
    """배치 처리 모니터링 테스트"""
    logger.info("🧪 배치 처리 모니터링 테스트 시작")
    
    try:
        batch_processor = get_batch_processor()
        
        # 초기 상태 확인
        initial_status = batch_processor.get_status()
        logger.info(f"📊 초기 상태: {initial_status}")
        
        # 몇 개의 요청 추가
        request_ids = []
        for i in range(3):
            text = f"모니터링 테스트 텍스트 {i+1}입니다."
            request_id = await batch_processor.add_request(
                text=text,
                analysis_type="full",
                priority=1
            )
            request_ids.append(request_id)
        
        # 처리 중 상태 확인
        await asyncio.sleep(0.5)
        processing_status = batch_processor.get_status()
        logger.info(f"📊 처리 중 상태: {processing_status}")
        
        # 모든 요청 완료 대기
        for request_id in request_ids:
            await batch_processor.get_result(request_id, timeout=30.0)
        
        # 완료 후 상태 확인
        final_status = batch_processor.get_status()
        logger.info(f"📊 완료 후 상태: {final_status}")
        
        # 상태 변화 확인
        if (final_status["total_processed"] > initial_status["total_processed"] and
            final_status["pending_requests"] == 0):
            logger.info("✅ 모니터링 테스트 통과")
            return True
        else:
            logger.error("❌ 모니터링 테스트 실패")
            return False
        
    except Exception as e:
        logger.error(f"❌ 모니터링 테스트 실패: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    logger.info("🚀 배치 처리 시스템 테스트 시작")
    
    # 서비스 초기화
    try:
        from app.services import initialize_services
        await initialize_services()
        logger.info("✅ 서비스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 서비스 초기화 실패: {e}")
        return
    
    # 테스트 실행
    tests = [
        ("기본 배치 처리", test_batch_processor_basic),
        ("다중 요청 배치 처리", test_batch_processor_multiple),
        ("우선순위 기반 배치 처리", test_batch_processor_priority),
        ("스트레스 테스트", test_batch_processor_stress),
        ("모니터링 테스트", test_batch_processor_monitoring)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"테스트: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ 테스트 {test_name} 실행 중 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    logger.info(f"\n{'='*50}")
    logger.info("테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n📊 최종 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        logger.info("🎉 모든 테스트가 통과했습니다!")
    else:
        logger.warning(f"⚠️ {total - passed}개 테스트가 실패했습니다.")
    
    # 서비스 정리
    try:
        from app.services import cleanup_services
        await cleanup_services()
        logger.info("✅ 서비스 정리 완료")
    except Exception as e:
        logger.error(f"❌ 서비스 정리 실패: {e}")


if __name__ == "__main__":
    asyncio.run(main())
