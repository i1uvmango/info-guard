"""
모니터링 서비스
성능 메트릭 수집, 에러 로깅, 시스템 상태 모니터링
"""

import time
import json
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 모델"""
    timestamp: datetime
    metric_type: str
    value: float
    unit: str
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

@dataclass
class SystemHealth:
    """시스템 헬스 데이터 모델"""
    status: str  # "healthy", "warning", "critical"
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    error_rate: float
    response_time_avg: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class MonitoringService:
    """
    모니터링 서비스
    성능 메트릭 수집, 에러 로깅, 시스템 상태 모니터링
    """
    
    def __init__(self):
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.error_log: List[Dict[str, Any]] = []
        self.performance_log: List[Dict[str, Any]] = []
        self.active_connections = 0
        self.total_requests = 0
        self.total_errors = 0
        self.response_times: deque = deque(maxlen=1000)
        self.logger = logger
        
        # 모니터링 시작
        asyncio.create_task(self._start_monitoring())
    
    async def _start_monitoring(self):
        """모니터링 시작"""
        while True:
            try:
                # 시스템 메트릭 수집
                await self._collect_system_metrics()
                
                # 성능 메트릭 수집
                await self._collect_performance_metrics()
                
                # 30초마다 수집
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"모니터링 오류: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기
    
    async def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric("cpu_usage", cpu_percent, "percent")
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            await self.record_metric("memory_usage", memory.percent, "percent")
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            await self.record_metric("disk_usage", (disk.used / disk.total) * 100, "percent")
            
            # 네트워크 I/O
            network = psutil.net_io_counters()
            await self.record_metric("network_bytes_sent", network.bytes_sent, "bytes")
            await self.record_metric("network_bytes_recv", network.bytes_recv, "bytes")
            
        except Exception as e:
            self.logger.error(f"시스템 메트릭 수집 실패: {e}")
    
    async def _collect_performance_metrics(self):
        """성능 메트릭 수집"""
        try:
            # 응답 시간 평균
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                await self.record_metric("response_time_avg", avg_response_time, "seconds")
            
            # 요청률
            await self.record_metric("requests_per_minute", self.total_requests, "requests")
            
            # 에러율
            error_rate = (self.total_errors / max(self.total_requests, 1)) * 100
            await self.record_metric("error_rate", error_rate, "percent")
            
            # 활성 연결 수
            await self.record_metric("active_connections", self.active_connections, "connections")
            
        except Exception as e:
            self.logger.error(f"성능 메트릭 수집 실패: {e}")
    
    async def record_metric(self, metric_type: str, value: float, unit: str, tags: Dict[str, str] = None):
        """메트릭 기록"""
        try:
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                metric_type=metric_type,
                value=value,
                unit=unit,
                tags=tags or {}
            )
            
            self.metrics_history[metric_type].append(metric)
            
            # 로그에 기록
            self.logger.info(f"메트릭 기록: {metric_type}={value}{unit}")
            
        except Exception as e:
            self.logger.error(f"메트릭 기록 실패: {metric_type}, 오류: {e}")
    
    def record_request(self, response_time: float, success: bool = True):
        """요청 기록"""
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if not success:
            self.total_errors += 1
    
    def record_connection(self, connected: bool):
        """연결 기록"""
        if connected:
            self.active_connections += 1
        else:
            self.active_connections = max(0, self.active_connections - 1)
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """에러 기록"""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self.error_log.append(error_entry)
        
        # 로그 크기 제한
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-1000:]
        
        self.logger.error(f"에러 기록: {error_type} - {error_message}")
    
    async def get_system_health(self) -> SystemHealth:
        """시스템 헬스 상태 조회"""
        try:
            # 최근 메트릭들 가져오기
            cpu_usage = self._get_latest_metric("cpu_usage", 0.0)
            memory_usage = self._get_latest_metric("memory_usage", 0.0)
            disk_usage = self._get_latest_metric("disk_usage", 0.0)
            error_rate = self._get_latest_metric("error_rate", 0.0)
            response_time_avg = self._get_latest_metric("response_time_avg", 0.0)
            
            # 상태 결정
            status = "healthy"
            if cpu_usage > 80 or memory_usage > 80 or error_rate > 10:
                status = "warning"
            if cpu_usage > 95 or memory_usage > 95 or error_rate > 20:
                status = "critical"
            
            return SystemHealth(
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                active_connections=self.active_connections,
                error_rate=error_rate,
                response_time_avg=response_time_avg
            )
            
        except Exception as e:
            self.logger.error(f"시스템 헬스 조회 실패: {e}")
            return SystemHealth(
                status="unknown",
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                active_connections=0,
                error_rate=0.0,
                response_time_avg=0.0
            )
    
    def _get_latest_metric(self, metric_type: str, default_value: float) -> float:
        """최신 메트릭 값 조회"""
        if metric_type in self.metrics_history and self.metrics_history[metric_type]:
            return self.metrics_history[metric_type][-1].value
        return default_value
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 조회"""
        try:
            summary = {
                "system_health": asdict(await self.get_system_health()),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "active_connections": self.active_connections,
                "metrics_count": len(self.metrics_history),
                "error_log_count": len(self.error_log),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 최근 메트릭들 추가
            recent_metrics = {}
            for metric_type, metrics in self.metrics_history.items():
                if metrics:
                    recent_metrics[metric_type] = {
                        "latest": metrics[-1].value,
                        "unit": metrics[-1].unit,
                        "count": len(metrics)
                    }
            
            summary["recent_metrics"] = recent_metrics
            
            return summary
            
        except Exception as e:
            self.logger.error(f"메트릭 요약 조회 실패: {e}")
            return {"error": str(e)}
    
    async def get_error_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """에러 로그 조회"""
        return self.error_log[-limit:] if self.error_log else []
    
    async def get_performance_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """성능 로그 조회"""
        return self.performance_log[-limit:] if self.performance_log else []
    
    async def clear_old_metrics(self, days: int = 7):
        """오래된 메트릭 삭제"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            for metric_type in list(self.metrics_history.keys()):
                # 오래된 메트릭 제거
                self.metrics_history[metric_type] = deque(
                    [m for m in self.metrics_history[metric_type] if m.timestamp > cutoff_time],
                    maxlen=1000
                )
            
            # 오래된 에러 로그 제거
            self.error_log = [
                error for error in self.error_log 
                if datetime.fromisoformat(error["timestamp"]) > cutoff_time
            ]
            
            self.logger.info(f"{days}일 이상 된 메트릭 삭제 완료")
            
        except Exception as e:
            self.logger.error(f"오래된 메트릭 삭제 실패: {e}")
    
    async def export_metrics(self, format_type: str = "json") -> str:
        """메트릭 내보내기"""
        try:
            if format_type == "json":
                export_data = {
                    "metrics": {
                        metric_type: [asdict(m) for m in metrics]
                        for metric_type, metrics in self.metrics_history.items()
                    },
                    "error_log": self.error_log,
                    "performance_log": self.performance_log,
                    "exported_at": datetime.utcnow().isoformat()
                }
                return json.dumps(export_data, indent=2)
            
            elif format_type == "csv":
                csv_lines = ["timestamp,metric_type,value,unit"]
                for metric_type, metrics in self.metrics_history.items():
                    for metric in metrics:
                        csv_lines.append(f"{metric.timestamp},{metric.metric_type},{metric.value},{metric.unit}")
                return "\n".join(csv_lines)
            
            else:
                raise ValueError(f"지원하지 않는 형식: {format_type}")
                
        except Exception as e:
            self.logger.error(f"메트릭 내보내기 실패: {e}")
            return f"Error: {str(e)}"
    
    async def health_check(self) -> Dict[str, Any]:
        """모니터링 서비스 헬스 체크"""
        try:
            system_health = await self.get_system_health()
            
            return {
                "status": "healthy",
                "system_health": asdict(system_health),
                "metrics_count": len(self.metrics_history),
                "error_log_count": len(self.error_log),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"모니터링 서비스 헬스 체크 실패: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# 전역 모니터링 서비스 인스턴스
monitoring_service = MonitoringService() 