#!/usr/bin/env python3
"""
Info-Guard 통합 테스트 스크립트
Python 서버와 Node.js 서버 간의 연동을 테스트합니다.
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTester:
    def __init__(self):
        self.python_server_url = "http://localhost:8000"
        self.nodejs_server_url = "http://localhost:3000"
        self.test_results = []
        
    async def test_python_server_health(self) -> Dict[str, Any]:
        """Python 서버 헬스체크 테스트"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.python_server_url}/health/") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Python 서버 헬스체크 성공")
                        return {"status": "success", "data": data}
                    else:
                        logger.error(f"❌ Python 서버 헬스체크 실패: {response.status}")
                        return {"status": "error", "status_code": response.status}
        except Exception as e:
            logger.error(f"❌ Python 서버 연결 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_python_server_analysis(self) -> Dict[str, Any]:
        """Python 서버 분석 API 테스트"""
        try:
            test_data = {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "analysis_type": "comprehensive"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.python_server_url}/api/v1/analysis/analyze",
                    json=test_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Python 서버 분석 API 성공")
                        return {"status": "success", "data": data}
                    else:
                        logger.error(f"❌ Python 서버 분석 API 실패: {response.status}")
                        return {"status": "error", "status_code": response.status}
        except Exception as e:
            logger.error(f"❌ Python 서버 분석 API 테스트 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_nodejs_server_health(self) -> Dict[str, Any]:
        """Node.js 서버 헬스체크 테스트"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.nodejs_server_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Node.js 서버 헬스체크 성공")
                        return {"status": "success", "data": data}
                    else:
                        logger.error(f"❌ Node.js 서버 헬스체크 실패: {response.status}")
                        return {"status": "error", "status_code": response.status}
        except Exception as e:
            logger.error(f"❌ Node.js 서버 연결 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_nodejs_server_analysis(self) -> Dict[str, Any]:
        """Node.js 서버 분석 API 테스트"""
        try:
            test_data = {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "user_id": "test_user_123"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.nodejs_server_url}/api/analysis",
                    json=test_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ Node.js 서버 분석 API 성공")
                        return {"status": "success", "data": data}
                    else:
                        logger.error(f"❌ Node.js 서버 분석 API 실패: {response.status}")
                        return {"status": "error", "status_code": response.status}
        except Exception as e:
            logger.error(f"❌ Node.js 서버 분석 API 테스트 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """WebSocket 연결 테스트"""
        try:
            import websockets
            
            websocket_url = f"ws://localhost:8000/ws/analysis/test_user/123"
            
            async with websockets.connect(websocket_url) as websocket:
                # 연결 확인 메시지 수신 대기
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "connection_established":
                    logger.info("✅ WebSocket 연결 성공")
                    
                    # 핑 메시지 전송
                    await websocket.send(json.dumps({"type": "ping"}))
                    
                    # 퐁 응답 수신 대기
                    pong_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    pong_data = json.loads(pong_message)
                    
                    if pong_data.get("type") == "pong":
                        logger.info("✅ WebSocket 핑/퐁 테스트 성공")
                        return {"status": "success", "message": "WebSocket 연결 및 통신 성공"}
                    else:
                        logger.warning("⚠️ WebSocket 핑/퐁 응답 형식 이상")
                        return {"status": "warning", "message": "핑/퐁 응답 형식 이상"}
                else:
                    logger.error("❌ WebSocket 연결 확인 메시지 수신 실패")
                    return {"status": "error", "message": "연결 확인 메시지 수신 실패"}
                    
        except ImportError:
            logger.warning("⚠️ websockets 라이브러리가 설치되지 않음")
            return {"status": "warning", "message": "websockets 라이브러리 미설치"}
        except Exception as e:
            logger.error(f"❌ WebSocket 테스트 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_server_integration(self) -> Dict[str, Any]:
        """서버 간 연동 테스트"""
        try:
            # Python 서버에서 분석 요청
            analysis_data = {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "analysis_type": "comprehensive"
            }
            
            async with aiohttp.ClientSession() as session:
                # Python 서버에 분석 요청
                async with session.post(
                    f"{self.python_server_url}/api/v1/analysis/analyze",
                    json=analysis_data
                ) as response:
                    if response.status == 200:
                        python_result = await response.json()
                        analysis_id = python_result.get("analysis_id")
                        
                        if analysis_id:
                            # Node.js 서버에서 분석 결과 조회
                            async with session.get(
                                f"{self.nodejs_server_url}/api/analysis/{analysis_id}"
                            ) as node_response:
                                if node_response.status == 200:
                                    node_result = await node_response.json()
                                    logger.info("✅ 서버 간 연동 테스트 성공")
                                    return {
                                        "status": "success",
                                        "python_result": python_result,
                                        "nodejs_result": node_result
                                    }
                                else:
                                    logger.error(f"❌ Node.js 서버 결과 조회 실패: {node_response.status}")
                                    return {"status": "error", "message": "Node.js 서버 결과 조회 실패"}
                        else:
                            logger.error("❌ Python 서버에서 분석 ID 반환 실패")
                            return {"status": "error", "message": "분석 ID 반환 실패"}
                    else:
                        logger.error(f"❌ Python 서버 분석 요청 실패: {response.status}")
                        return {"status": "error", "message": "Python 서버 분석 요청 실패"}
                        
        except Exception as e:
            logger.error(f"❌ 서버 연동 테스트 실패: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("🚀 Info-Guard 통합 테스트 시작")
        logger.info("=" * 50)
        
        tests = [
            ("Python 서버 헬스체크", self.test_python_server_health),
            ("Python 서버 분석 API", self.test_python_server_analysis),
            ("Node.js 서버 헬스체크", self.test_nodejs_server_health),
            ("Node.js 서버 분석 API", self.test_nodejs_server_analysis),
            ("WebSocket 연결", self.test_websocket_connection),
            ("서버 간 연동", self.test_server_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 {test_name} 테스트 실행 중...")
            result = await test_func()
            self.test_results.append({
                "test_name": test_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            # 테스트 결과에 따른 대기
            if result.get("status") == "error":
                logger.warning(f"⚠️ {test_name} 실패로 인해 잠시 대기...")
                await asyncio.sleep(2)
        
        # 결과 요약
        self.print_test_summary()
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 테스트 결과 요약")
        logger.info("=" * 50)
        
        success_count = 0
        error_count = 0
        warning_count = 0
        
        for result in self.test_results:
            status = result["result"].get("status")
            if status == "success":
                success_count += 1
                logger.info(f"✅ {result['test_name']}: 성공")
            elif status == "error":
                error_count += 1
                logger.error(f"❌ {result['test_name']}: 실패")
            elif status == "warning":
                warning_count += 1
                logger.warning(f"⚠️ {result['test_name']}: 경고")
        
        logger.info(f"\n📈 총 테스트: {len(self.test_results)}")
        logger.info(f"✅ 성공: {success_count}")
        logger.info(f"❌ 실패: {error_count}")
        logger.info(f"⚠️ 경고: {warning_count}")
        
        if error_count == 0:
            logger.info("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            logger.warning(f"\n⚠️ {error_count}개의 테스트가 실패했습니다.")
        
        # 결과를 JSON 파일로 저장
        self.save_test_results()
    
    def save_test_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        try:
            with open("test_results.json", "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info("💾 테스트 결과가 test_results.json 파일로 저장되었습니다.")
        except Exception as e:
            logger.error(f"❌ 테스트 결과 저장 실패: {e}")

async def main():
    """메인 함수"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ 테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류 발생: {e}")
