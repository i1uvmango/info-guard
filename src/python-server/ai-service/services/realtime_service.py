"""
실시간 분석 서비스
WebSocket을 통한 실시간 분석 진행률 표시
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from config.logging_config import get_logger
from services.analysis_service import AnalysisService

logger = get_logger(__name__)

# WebSocket 이벤트 타입
ANALYSIS_STARTED = "analysis_started"
ANALYSIS_PROGRESS = "analysis_progress"
ANALYSIS_COMPLETED = "analysis_completed"
ANALYSIS_ERROR = "analysis_error"

# 진행률 단계
PROGRESS_STEPS = {
    "data_collection": "데이터 수집 중...",
    "credibility_analysis": "신뢰도 분석 중...",
    "bias_detection": "편향 감지 중...",
    "fact_checking": "팩트 체크 중...",
    "source_validation": "출처 검증 중...",
    "result_synthesis": "결과 종합 중..."
}

class RealtimeAnalysisService:
    """
    실시간 분석 서비스
    WebSocket을 통한 실시간 분석 진행률 표시
    """
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.active_connections: Dict[str, WebSocket] = {}
        self.analysis_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, video_id: str):
        """WebSocket 연결"""
        await websocket.accept()
        self.active_connections[video_id] = websocket
        logger.info(f"WebSocket 연결됨: {video_id}")
    
    async def disconnect(self, video_id: str):
        """WebSocket 연결 해제"""
        if video_id in self.active_connections:
            del self.active_connections[video_id]
        if video_id in self.analysis_tasks:
            self.analysis_tasks[video_id].cancel()
            del self.analysis_tasks[video_id]
        logger.info(f"WebSocket 연결 해제: {video_id}")
    
    async def send_message(self, video_id: str, event_type: str, data: Dict[str, Any]):
        """메시지 전송"""
        if video_id in self.active_connections:
            try:
                message = {
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.active_connections[video_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"메시지 전송 실패: {video_id}, 오류: {e}")
                await self.disconnect(video_id)
    
    async def start_real_time_analysis(self, websocket: WebSocket, video_id: str, video_data: Dict[str, Any]):
        """실시간 분석 시작"""
        await self.connect(websocket, video_id)
        
        try:
            # 분석 시작 알림
            await self.send_message(video_id, ANALYSIS_STARTED, {
                "video_id": video_id,
                "message": "분석을 시작합니다.",
                "total_steps": len(PROGRESS_STEPS)
            })
            
            # 분석 단계별 실행
            await self._run_analysis_steps(video_id, video_data)
            
        except WebSocketDisconnect:
            await self.disconnect(video_id)
        except Exception as e:
            logger.error(f"실시간 분석 실패: {video_id}, 오류: {e}")
            await self.send_message(video_id, ANALYSIS_ERROR, {
                "error": str(e),
                "message": "분석 중 오류가 발생했습니다."
            })
            await self.disconnect(video_id)
    
    async def _run_analysis_steps(self, video_id: str, video_data: Dict[str, Any]):
        """분석 단계별 실행"""
        start_time = time.time()
        current_step = 0
        
        # 1. 데이터 수집 단계
        current_step += 1
        await self._update_progress(video_id, "data_collection", current_step, len(PROGRESS_STEPS))
        await asyncio.sleep(0.5)  # 실제 데이터 수집 시뮬레이션
        
        # 2. 신뢰도 분석 단계
        current_step += 1
        await self._update_progress(video_id, "credibility_analysis", current_step, len(PROGRESS_STEPS))
        credibility_result = await self._run_credibility_analysis(video_data)
        
        # 3. 편향 감지 단계
        current_step += 1
        await self._update_progress(video_id, "bias_detection", current_step, len(PROGRESS_STEPS))
        bias_result = await self._run_bias_detection(video_data)
        
        # 4. 팩트 체크 단계
        current_step += 1
        await self._update_progress(video_id, "fact_checking", current_step, len(PROGRESS_STEPS))
        fact_check_result = await self._run_fact_checking(video_data)
        
        # 5. 출처 검증 단계
        current_step += 1
        await self._update_progress(video_id, "source_validation", current_step, len(PROGRESS_STEPS))
        source_result = await self._run_source_validation(video_data)
        
        # 6. 결과 종합 단계
        current_step += 1
        await self._update_progress(video_id, "result_synthesis", current_step, len(PROGRESS_STEPS))
        
        # 최종 결과 생성
        final_result = await self._synthesize_results(
            credibility_result, bias_result, fact_check_result, source_result
        )
        
        processing_time = time.time() - start_time
        
        # 분석 완료 알림
        await self.send_message(video_id, ANALYSIS_COMPLETED, {
            "video_id": video_id,
            "result": final_result,
            "processing_time": processing_time,
            "message": "분석이 완료되었습니다."
        })
        
        logger.info(f"실시간 분석 완료: {video_id}, 처리시간: {processing_time:.2f}초")
    
    async def _update_progress(self, video_id: str, step_name: str, current: int, total: int):
        """진행률 업데이트"""
        progress_data = {
            "step": step_name,
            "step_name": PROGRESS_STEPS[step_name],
            "current": current,
            "total": total,
            "percentage": int((current / total) * 100)
        }
        
        await self.send_message(video_id, ANALYSIS_PROGRESS, progress_data)
        await asyncio.sleep(0.2)  # 진행률 업데이트 간격
    
    async def _run_credibility_analysis(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """신뢰도 분석 실행"""
        try:
            text = video_data.get('transcript', '')
            metadata = video_data.get('metadata', {})
            
            result = self.analysis_service.credibility_analyzer.analyze_credibility(text, metadata)
            return {
                "type": "credibility",
                "score": result.get('score', 0),
                "grade": result.get('grade', 'C'),
                "details": result.get('breakdown', {})
            }
        except Exception as e:
            logger.error(f"신뢰도 분석 실패: {e}")
            return {"type": "credibility", "error": str(e)}
    
    async def _run_bias_detection(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """편향 감지 실행"""
        try:
            text = video_data.get('transcript', '')
            
            result = self.analysis_service.bias_detector.detect(text)
            return {
                "type": "bias",
                "score": result.get('total_bias_score', 0),
                "details": result.get('bias_types', {})
            }
        except Exception as e:
            logger.error(f"편향 감지 실패: {e}")
            return {"type": "bias", "error": str(e)}
    
    async def _run_fact_checking(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """팩트 체크 실행"""
        try:
            text = video_data.get('transcript', '')
            
            result = self.analysis_service.fact_checker.verify(text)
            return {
                "type": "fact_check",
                "score": result.get('score', 0),
                "details": result.get('verified_claims', [])
            }
        except Exception as e:
            logger.error(f"팩트 체크 실패: {e}")
            return {"type": "fact_check", "error": str(e)}
    
    async def _run_source_validation(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """출처 검증 실행"""
        try:
            metadata = video_data.get('metadata', {})
            source_info = {
                "domain": metadata.get('source', 'unknown'),
                "author": metadata.get('author', 'unknown'),
                "publication_date": metadata.get('date', 'unknown')
            }
            
            result = self.analysis_service.source_validator.validate(source_info)
            return {
                "type": "source_validation",
                "score": result.get('score', 0),
                "details": result
            }
        except Exception as e:
            logger.error(f"출처 검증 실패: {e}")
            return {"type": "source_validation", "error": str(e)}
    
    async def _synthesize_results(self, credibility_result: Dict, bias_result: Dict, 
                                 fact_check_result: Dict, source_result: Dict) -> Dict[str, Any]:
        """결과 종합"""
        try:
            # 종합 점수 계산
            scores = []
            if 'score' in credibility_result:
                scores.append(credibility_result['score'])
            if 'score' in bias_result:
                scores.append(100 - bias_result['score'])  # 편향 점수를 신뢰도로 변환
            if 'score' in fact_check_result:
                scores.append(fact_check_result['score'])
            if 'score' in source_result:
                scores.append(source_result['score'])
            
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # 종합 등급 결정
            if overall_score >= 80:
                overall_grade = "A"
            elif overall_score >= 60:
                overall_grade = "B"
            elif overall_score >= 40:
                overall_grade = "C"
            elif overall_score >= 20:
                overall_grade = "D"
            else:
                overall_grade = "F"
            
            return {
                "overall_score": overall_score,
                "overall_grade": overall_grade,
                "analysis_results": {
                    "credibility": credibility_result,
                    "bias": bias_result,
                    "fact_check": fact_check_result,
                    "source_validation": source_result
                },
                "summary": self._generate_summary(overall_score, overall_grade)
            }
            
        except Exception as e:
            logger.error(f"결과 종합 실패: {e}")
            return {"error": str(e)}
    
    def _generate_summary(self, score: float, grade: str) -> str:
        """요약 생성"""
        if grade == "A":
            return f"이 영상은 높은 신뢰도를 보입니다. (점수: {score:.1f}%)"
        elif grade == "B":
            return f"이 영상은 보통 수준의 신뢰도를 보입니다. (점수: {score:.1f}%)"
        elif grade == "C":
            return f"이 영상은 낮은 신뢰도를 보입니다. (점수: {score:.1f}%)"
        elif grade == "D":
            return f"이 영상은 매우 낮은 신뢰도를 보입니다. (점수: {score:.1f}%)"
        else:
            return f"이 영상은 신뢰할 수 없습니다. (점수: {score:.1f}%)" 