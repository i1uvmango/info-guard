"""
배치 처리 서비스
여러 분석 요청을 묶어서 효율적으로 처리하는 시스템입니다.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import time
from collections import deque, defaultdict

from app.core.logging import get_logger
from app.core.gpu_config import get_gpu_config
from app.services.ai_models import AIModelService

logger = get_logger(__name__)


class BatchStatus(Enum):
    """배치 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchRequest:
    """배치 요청"""
    request_id: str
    text: str
    analysis_type: str
    priority: int = 1
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchResult:
    """배치 결과"""
    request_id: str
    result: Any
    processing_time: float
    status: str
    error: Optional[str] = None


@dataclass
class BatchMetrics:
    """배치 처리 메트릭"""
    total_requests: int = 0
    total_processed: int = 0
    total_failed: int = 0
    total_cancelled: int = 0
    average_processing_time: float = 0.0
    average_wait_time: float = 0.0
    throughput_per_minute: float = 0.0
    success_rate: float = 0.0
    gpu_utilization: float = 0.0
    memory_usage: float = 0.0


class BatchProcessor:
    """배치 처리기"""
    
    def __init__(self):
        self.ai_service = AIModelService()
        self.gpu_config = get_gpu_config()
        
        # 배치 설정
        self.max_batch_size = self.gpu_config.batch_size
        self.min_batch_size = max(1, self.max_batch_size // 4)  # 최소 배치 크기
        self.current_batch_size = self.max_batch_size  # 현재 배치 크기
        
        # 적응형 대기 시간
        self.max_wait_time = 5.0  # 최대 대기 시간 (초)
        self.min_wait_time = 0.5  # 최소 대기 시간 (초)
        self.current_wait_time = self.max_wait_time  # 현재 대기 시간
        
        self.processing_interval = 0.1  # 처리 간격 (초)
        
        # 배치 큐
        self.pending_requests: List[BatchRequest] = []
        self.processing_batches: Dict[str, List[BatchRequest]] = {}
        self.completed_results: Dict[str, BatchResult] = {}
        
        # 상태 관리
        self.is_running = False
        self.total_processed = 0
        self.total_failed = 0
        self.total_cancelled = 0
        
        # 성능 모니터링
        self.performance_history = deque(maxlen=1000)  # 최근 1000개 요청의 성능 데이터
        self.batch_history = deque(maxlen=100)  # 최근 100개 배치의 성능 데이터
        self.start_time = time.time()
        
        # 메트릭 수집
        self.metrics = BatchMetrics()
        self.last_metrics_update = time.time()
        self.metrics_update_interval = 60.0  # 1분마다 메트릭 업데이트
        
        # 적응형 최적화
        self.optimization_interval = 30.0  # 30초마다 최적화 수행
        self.last_optimization = time.time()
        self.performance_window = 300  # 5분간의 성능 데이터로 최적화
        
        logger.info(f"배치 처리기 초기화됨 (최대 배치 크기: {self.max_batch_size}, 최소: {self.min_batch_size})")
    
    async def add_request(
        self, 
        text: str, 
        analysis_type: str = "full",
        priority: int = 1,
        metadata: Dict[str, Any] = None
    ) -> str:
        """분석 요청을 배치 큐에 추가합니다."""
        request_id = str(uuid.uuid4())
        request = BatchRequest(
            request_id=request_id,
            text=text,
            analysis_type=analysis_type,
            priority=priority,
            metadata=metadata
        )
        
        # 우선순위에 따라 큐에 삽입
        self._insert_by_priority(request)
        
        # 성능 모니터링 데이터 수집
        self._record_request_added(request)
        
        logger.info(f"배치 요청 추가됨: {request_id} (우선순위: {priority})")
        
        # 배치 처리 시작
        if not self.is_running:
            asyncio.create_task(self._start_processing())
        
        return request_id
    
    def _insert_by_priority(self, request: BatchRequest):
        """우선순위에 따라 요청을 삽입합니다."""
        for i, existing_request in enumerate(self.pending_requests):
            if request.priority > existing_request.priority:
                self.pending_requests.insert(i, request)
                return
        
        # 우선순위가 낮으면 맨 뒤에 추가
        self.pending_requests.append(request)
    
    def _record_request_added(self, request: BatchRequest):
        """요청 추가 시 성능 데이터를 기록합니다."""
        self.performance_history.append({
            'timestamp': time.time(),
            'action': 'request_added',
            'request_id': request.request_id,
            'priority': request.priority,
            'queue_length': len(self.pending_requests)
        })
    
    async def _start_processing(self):
        """배치 처리를 시작합니다."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("배치 처리 시작됨")
        
        try:
            while self.is_running and (self.pending_requests or self.processing_batches):
                await self._process_batch_cycle()
                await asyncio.sleep(self.processing_interval)
                
                # 메트릭 업데이트
                if time.time() - self.last_metrics_update >= self.metrics_update_interval:
                    await self._update_metrics()
                
                # 적응형 최적화 수행
                if time.time() - self.last_optimization >= self.optimization_interval:
                    await self._perform_adaptive_optimization()
                
        except Exception as e:
            logger.error(f"배치 처리 중 오류 발생: {e}")
        finally:
            self.is_running = False
            logger.info("배치 처리 종료됨")
    
    async def _perform_adaptive_optimization(self):
        """적응형 최적화를 수행합니다."""
        try:
            current_time = time.time()
            self.last_optimization = current_time
            
            # 최근 성능 데이터 수집
            recent_performance = [
                p for p in self.performance_history
                if current_time - p['timestamp'] <= self.performance_window
            ]
            
            if len(recent_performance) < 10:  # 충분한 데이터가 없으면 스킵
                return
            
            # 성공률 계산
            completed_requests = [p for p in recent_performance if p['action'] == 'request_completed']
            if not completed_requests:
                return
            
            success_count = len([p for p in completed_requests if p.get('success', False)])
            success_rate = success_count / len(completed_requests) if completed_requests else 0
            
            # 평균 처리 시간 계산
            processing_times = [p.get('processing_time', 0) for p in completed_requests if 'processing_time' in p]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # 평균 대기 시간 계산
            wait_times = [p.get('wait_time', 0) for p in completed_requests if 'wait_time' in p]
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            
            # 큐 길이 분석
            queue_lengths = [p.get('queue_length', 0) for p in recent_performance if 'queue_length' in p]
            avg_queue_length = sum(queue_lengths) / len(queue_lengths) if queue_lengths else 0
            
            # 최적화 전략 결정
            await self._apply_optimization_strategy(
                success_rate, avg_processing_time, avg_wait_time, avg_queue_length
            )
            
            logger.debug(f"적응형 최적화 완료: 성공률 {success_rate:.2f}, 처리시간 {avg_processing_time:.3f}s, 대기시간 {avg_wait_time:.3f}s")
            
        except Exception as e:
            logger.error(f"적응형 최적화 실패: {e}")
    
    async def _apply_optimization_strategy(self, success_rate: float, avg_processing_time: float, 
                                         avg_wait_time: float, avg_queue_length: float):
        """최적화 전략을 적용합니다."""
        # 성공률이 낮으면 배치 크기 줄이기
        if success_rate < 0.8 and self.current_batch_size > self.min_batch_size:
            self.current_batch_size = max(self.min_batch_size, self.current_batch_size - 1)
            logger.info(f"성공률 저하로 배치 크기 감소: {self.current_batch_size}")
        
        # 성공률이 높고 처리 시간이 빠르면 배치 크기 늘리기
        elif success_rate > 0.95 and avg_processing_time < 2.0 and self.current_batch_size < self.max_batch_size:
            self.current_batch_size = min(self.max_batch_size, self.current_batch_size + 1)
            logger.info(f"성능 향상으로 배치 크기 증가: {self.current_batch_size}")
        
        # 대기 시간이 길면 대기 시간 줄이기
        if avg_wait_time > 3.0 and self.current_wait_time > self.min_wait_time:
            self.current_wait_time = max(self.min_wait_time, self.current_wait_time - 0.5)
            logger.info(f"대기 시간 단축: {self.current_wait_time:.1f}s")
        
        # 큐가 비어있으면 대기 시간 늘리기
        elif avg_queue_length < 2 and self.current_wait_time < self.max_wait_time:
            self.current_wait_time = min(self.max_wait_time, self.current_wait_time + 0.5)
            logger.info(f"대기 시간 증가: {self.current_wait_time:.1f}s")
    
    async def _process_batch_cycle(self):
        """배치 처리 사이클을 실행합니다."""
        # 완료된 배치 확인
        await self._check_completed_batches()
        
        # 새로운 배치 시작
        if self.pending_requests and len(self.processing_batches) < 3:  # 최대 3개 배치 동시 처리
            await self._start_new_batch()
    
    async def _start_new_batch(self):
        """새로운 배치를 시작합니다."""
        # 현재 최적화된 배치 크기만큼 요청 수집
        batch_requests = []
        batch_id = str(uuid.uuid4())
        
        # 우선순위가 높은 요청부터 처리
        while (len(batch_requests) < self.current_batch_size and 
               self.pending_requests and 
               self._should_start_batch(batch_requests)):
            
            request = self.pending_requests.pop(0)
            batch_requests.append(request)
        
        if not batch_requests:
            return
        
        # 배치 처리 시작
        self.processing_batches[batch_id] = batch_requests
        batch_start_time = time.time()
        
        # 배치 성능 데이터 기록
        self.batch_history.append({
            'batch_id': batch_id,
            'start_time': batch_start_time,
            'request_count': len(batch_requests),
            'batch_size': self.current_batch_size,
            'wait_time': self.current_wait_time,
            'average_priority': sum(r.priority for r in batch_requests) / len(batch_requests)
        })
        
        logger.info(f"배치 {batch_id} 시작됨: {len(batch_requests)}개 요청 (배치 크기: {self.current_batch_size})")
        
        # 비동기로 배치 처리
        asyncio.create_task(self._process_batch(batch_id, batch_requests, batch_start_time))
    
    def _should_start_batch(self, current_batch: List[BatchRequest]) -> bool:
        """배치를 시작해야 하는지 결정합니다."""
        if not current_batch:
            return True
        
        # 첫 번째 요청의 대기 시간 확인
        first_request = current_batch[0]
        wait_time = (datetime.utcnow() - first_request.created_at).total_seconds()
        
        # 현재 최적화된 대기 시간을 초과했거나 배치가 가득 찬 경우
        return wait_time >= self.current_wait_time or len(current_batch) >= self.current_batch_size
    
    async def _process_batch(self, batch_id: str, requests: List[BatchRequest], batch_start_time: float):
        """배치를 처리합니다."""
        start_time = time.time()
        
        try:
            logger.info(f"배치 {batch_id} 처리 시작: {len(requests)}개 요청")
            
            # 배치 내 모든 요청을 병렬로 처리
            tasks = []
            for request in requests:
                task = self._process_single_request(request)
                tasks.append(task)
            
            # 모든 요청 완료 대기
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for i, result in enumerate(results):
                request = requests[i]
                processing_time = time.time() - start_time
                
                if isinstance(result, Exception):
                    # 오류 발생
                    batch_result = BatchResult(
                        request_id=request.request_id,
                        result=None,
                        processing_time=processing_time,
                        status=BatchStatus.FAILED.value,
                        error=str(result)
                    )
                    self.total_failed += 1
                    self._record_request_completed(request, batch_result, False)
                else:
                    # 성공
                    batch_result = BatchResult(
                        request_id=request.request_id,
                        result=result,
                        processing_time=processing_time,
                        status=BatchStatus.COMPLETED.value
                    )
                    self.total_processed += 1
                    self._record_request_completed(request, batch_result, True)
                
                self.completed_results[request.request_id] = batch_result
            
            # 배치 완료 성능 데이터 기록
            batch_processing_time = time.time() - batch_start_time
            self._record_batch_completed(batch_id, len(requests), batch_processing_time)
            
            logger.info(f"배치 {batch_id} 처리 완료: 성공 {self.total_processed}, 실패 {self.total_failed}")
            
        except Exception as e:
            logger.error(f"배치 {batch_id} 처리 실패: {e}")
            
            # 모든 요청을 실패로 표시
            for request in requests:
                batch_result = BatchResult(
                    request_id=request.request_id,
                    result=None,
                    processing_time=0.0,
                    status=BatchStatus.FAILED.value,
                    error=str(e)
                )
                self.completed_results[request.request_id] = batch_result
                self.total_failed += 1
                self._record_request_completed(request, batch_result, False)
        
        finally:
            # 처리 중인 배치에서 제거
            if batch_id in self.processing_batches:
                del self.processing_batches[batch_id]
    
    def _record_request_completed(self, request: BatchRequest, result: BatchResult, success: bool):
        """요청 완료 시 성능 데이터를 기록합니다."""
        wait_time = (datetime.utcnow() - request.created_at).total_seconds()
        
        self.performance_history.append({
            'timestamp': time.time(),
            'action': 'request_completed',
            'request_id': request.request_id,
            'success': success,
            'processing_time': result.processing_time,
            'wait_time': wait_time,
            'priority': request.priority
        })
    
    def _record_batch_completed(self, batch_id: str, request_count: int, processing_time: float):
        """배치 완료 시 성능 데이터를 기록합니다."""
        # 배치 히스토리에서 해당 배치 찾기
        for batch_data in self.batch_history:
            if batch_data['batch_id'] == batch_id:
                batch_data['processing_time'] = processing_time
                batch_data['completed'] = True
                break
    
    async def _process_single_request(self, request: BatchRequest):
        """단일 요청을 처리합니다."""
        try:
            # AI 모델 서비스로 분석 수행
            result = await self.ai_service.analyze_content(
                text=request.text,
                analysis_type=request.analysis_type,
                video_metadata=request.metadata.get("video_metadata")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"요청 {request.request_id} 처리 실패: {e}")
            raise
    
    async def _check_completed_batches(self):
        """완료된 배치를 확인합니다."""
        # 이미 완료된 배치는 processing_batches에서 제거됨
        # 이 메서드는 향후 확장을 위해 유지
        pass
    
    async def _update_metrics(self):
        """메트릭을 업데이트합니다."""
        try:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            # 기본 통계
            total_requests = self.total_processed + self.total_failed + self.total_cancelled
            success_rate = (self.total_processed / total_requests * 100) if total_requests > 0 else 0
            
            # 성능 통계 계산
            if self.performance_history:
                processing_times = [p['processing_time'] for p in self.performance_history 
                                 if p['action'] == 'request_completed' and 'processing_time' in p]
                wait_times = [p['wait_time'] for p in self.performance_history 
                            if p['action'] == 'request_completed' and 'wait_time' in p]
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            else:
                avg_processing_time = 0
                avg_wait_time = 0
            
            # 처리량 계산 (분당)
            recent_requests = [p for p in self.performance_history 
                             if p['action'] == 'request_completed' and 
                             current_time - p['timestamp'] <= 60]
            throughput_per_minute = len(recent_requests)
            
            # GPU 사용률 및 메모리 사용량 (간단한 추정)
            gpu_utilization = min(100, len(self.processing_batches) * 30)  # 배치당 30% 사용률로 추정
            memory_usage = min(100, len(self.completed_results) * 0.1)  # 결과당 0.1% 메모리 사용률로 추정
            
            # 메트릭 업데이트
            self.metrics = BatchMetrics(
                total_requests=total_requests,
                total_processed=self.total_processed,
                total_failed=self.total_failed,
                total_cancelled=self.total_cancelled,
                average_processing_time=avg_processing_time,
                average_wait_time=avg_wait_time,
                throughput_per_minute=throughput_per_minute,
                success_rate=success_rate,
                gpu_utilization=gpu_utilization,
                memory_usage=memory_usage
            )
            
            self.last_metrics_update = current_time
            
            # 메트릭 로깅 (디버그 레벨)
            logger.debug(f"메트릭 업데이트됨: 성공률 {success_rate:.1f}%, 처리량 {throughput_per_minute}/분")
            
        except Exception as e:
            logger.error(f"메트릭 업데이트 실패: {e}")
    
    async def get_result(self, request_id: str, timeout: float = 30.0) -> Optional[BatchResult]:
        """요청 결과를 가져옵니다."""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if request_id in self.completed_results:
                return self.completed_results[request_id]
            
            await asyncio.sleep(0.1)
        
        # 타임아웃
        logger.warning(f"요청 {request_id} 결과 대기 타임아웃")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """배치 처리기 상태를 반환합니다."""
        return {
            "is_running": self.is_running,
            "pending_requests": len(self.pending_requests),
            "processing_batches": len(self.processing_batches),
            "completed_results": len(self.completed_results),
            "total_processed": self.total_processed,
            "total_failed": self.total_failed,
            "total_cancelled": self.total_cancelled,
            "max_batch_size": self.max_batch_size,
            "min_batch_size": self.min_batch_size,
            "current_batch_size": self.current_batch_size,
            "max_wait_time": self.max_wait_time,
            "min_wait_time": self.min_wait_time,
            "current_wait_time": self.current_wait_time,
            "gpu_device": self.gpu_config.device,
            "uptime_seconds": time.time() - self.start_time,
            "last_optimization": time.time() - self.last_optimization,
            "optimization_interval": self.optimization_interval
        }
    
    def get_metrics(self) -> BatchMetrics:
        """배치 처리 메트릭을 반환합니다."""
        return self.metrics
    
    def get_performance_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """성능 히스토리를 반환합니다."""
        return list(self.performance_history)[-limit:]
    
    def get_batch_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """배치 히스토리를 반환합니다."""
        return list(self.batch_history)[-limit:]
    
    async def stop(self):
        """배치 처리를 중지합니다."""
        self.is_running = False
        logger.info("배치 처리 중지 요청됨")
    
    async def clear_completed_results(self, max_age_hours: int = 24):
        """오래된 완료 결과를 정리합니다."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        old_results = []
        
        for request_id, result in self.completed_results.items():
            # 결과 생성 시간을 추정 (정확한 시간은 request_id에서 추출 불가)
            # 간단한 정리 로직 사용
            if len(self.completed_results) > 1000:  # 결과가 많으면 오래된 것부터 정리
                old_results.append(request_id)
        
        # 오래된 결과 제거
        for request_id in old_results[:100]:  # 한 번에 최대 100개 제거
            del self.completed_results[request_id]
        
        if old_results:
            logger.info(f"오래된 완료 결과 {len(old_results)}개 정리됨")
    
    async def reset_metrics(self):
        """메트릭을 초기화합니다."""
        self.performance_history.clear()
        self.batch_history.clear()
        self.start_time = time.time()
        self.last_metrics_update = time.time()
        self.metrics = BatchMetrics()
        logger.info("메트릭 초기화됨")


# 전역 배치 처리기 인스턴스
batch_processor = BatchProcessor()


def get_batch_processor() -> BatchProcessor:
    """배치 처리기 인스턴스를 반환합니다."""
    return batch_processor


async def add_batch_request(
    text: str, 
    analysis_type: str = "full",
    priority: int = 1,
    metadata: Dict[str, Any] = None
) -> str:
    """배치 분석 요청을 추가합니다."""
    return await batch_processor.add_request(text, analysis_type, priority, metadata)


async def get_batch_result(request_id: str, timeout: float = 30.0) -> Optional[BatchResult]:
    """배치 분석 결과를 가져옵니다."""
    return await batch_processor.get_result(request_id, timeout)
