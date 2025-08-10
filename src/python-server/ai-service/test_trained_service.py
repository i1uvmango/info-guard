"""
학습된 모델 서비스 테스트
"""

import requests
import json
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_service():
    """AI 서비스 테스트"""
    try:
        logger.info("AI 서비스 테스트 시작")
        
        # 테스트 데이터
        test_cases = [
            {
                "name": "신뢰할 수 있는 뉴스",
                "data": {
                    "video_id": "test_news_1",
                    "transcript": "이 뉴스는 과학적 연구 결과를 바탕으로 작성되었습니다. 전문가들의 검증을 거친 사실을 전달합니다.",
                    "metadata": {
                        "title": "정확한 뉴스 제목",
                        "description": "사실 기반 뉴스입니다."
                    }
                }
            },
            {
                "name": "클릭베이트 영상",
                "data": {
                    "video_id": "test_clickbait_1",
                    "transcript": "충격적인 진실! 당신이 몰랐던 놀라운 사실! 믿을 수 없는 이야기! 반드시 봐야 합니다!",
                    "metadata": {
                        "title": "충격적인 진실! 당신이 몰랐던 사실!",
                        "description": "믿을 수 없는 이야기입니다."
                    }
                }
            },
            {
                "name": "교육 영상",
                "data": {
                    "video_id": "test_education_1",
                    "transcript": "이 강의에서는 과학적 방법론을 통해 검증된 내용을 다룹니다. 전문가들의 연구 결과를 바탕으로 설명합니다.",
                    "metadata": {
                        "title": "과학적 교육 강의",
                        "description": "검증된 교육 내용입니다."
                    }
                }
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"테스트 케이스 {i+1}: {test_case['name']}")
            
            try:
                # AI 서비스 호출
                response = requests.post(
                    "http://localhost:8000/analyze",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ 성공 - 신뢰도 점수: {result['data']['credibility_score']}")
                    logger.info(f"   등급: {result['data']['credibility_grade']}")
                    logger.info(f"   설명: {result['data']['explanation']}")
                    
                    results.append({
                        "test_case": test_case["name"],
                        "success": True,
                        "credibility_score": result['data']['credibility_score'],
                        "grade": result['data']['credibility_grade'],
                        "processing_time": result['processing_time']
                    })
                else:
                    logger.error(f"❌ 실패 - 상태 코드: {response.status_code}")
                    logger.error(f"   응답: {response.text}")
                    
                    results.append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    })
                    
            except Exception as e:
                logger.error(f"❌ 예외 발생: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        # 결과 요약
        logger.info("=== 테스트 결과 요약 ===")
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        logger.info(f"성공: {len(successful_tests)}/{len(results)}")
        logger.info(f"실패: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_score = sum(r["credibility_score"] for r in successful_tests) / len(successful_tests)
            avg_time = sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
            logger.info(f"평균 신뢰도 점수: {avg_score:.1f}")
            logger.info(f"평균 처리 시간: {avg_time:.2f}초")
        
        if failed_tests:
            logger.error("실패한 테스트:")
            for test in failed_tests:
                logger.error(f"  - {test['test_case']}: {test['error']}")
        
        return results
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        return []

def test_service_health():
    """서비스 상태 확인"""
    try:
        logger.info("서비스 상태 확인 중...")
        
        # 헬스 체크
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✅ 서비스 정상 - 모델 로드: {health_data['models_loaded']}")
            logger.info(f"   업타임: {health_data['uptime']:.1f}초")
            return True
        else:
            logger.error(f"❌ 서비스 비정상 - 상태 코드: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 서비스 연결 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("학습된 모델 서비스 테스트 시작")
    
    # 1. 서비스 상태 확인
    logger.info("=== 1. 서비스 상태 확인 ===")
    if not test_service_health():
        logger.error("서비스가 실행되지 않았습니다. 먼저 서비스를 시작하세요.")
        return
    
    # 2. AI 서비스 테스트
    logger.info("=== 2. AI 서비스 테스트 ===")
    results = test_ai_service()
    
    # 3. 결과 요약
    logger.info("=== 3. 최종 결과 ===")
    if results:
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"총 {len(results)}개 테스트 중 {success_count}개 성공")
        
        if success_count == len(results):
            logger.info("🎉 모든 테스트 통과!")
        else:
            logger.info("⚠️ 일부 테스트 실패")
    else:
        logger.error("❌ 테스트 결과가 없습니다")

if __name__ == "__main__":
    main() 