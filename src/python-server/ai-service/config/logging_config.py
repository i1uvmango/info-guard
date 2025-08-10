import logging
import structlog
from typing import Dict, Any
from .settings import settings

def setup_logging():
    """로깅 시스템을 설정합니다."""
    
    # 기본 로깅 설정
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ai_service.log")
        ]
    )
    
    # structlog 설정
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """로거를 반환합니다."""
    return structlog.get_logger(name)

# 성능 모니터링을 위한 메트릭 로거
class MetricsLogger:
    def __init__(self):
        self.logger = get_logger("metrics")
    
    def log_analysis_time(self, model_name: str, processing_time: float):
        """분석 시간을 로깅합니다."""
        self.logger.info(
            "analysis_time",
            model=model_name,
            processing_time=processing_time
        )
    
    def log_accuracy(self, model_name: str, accuracy: float):
        """모델 정확도를 로깅합니다."""
        self.logger.info(
            "model_accuracy",
            model=model_name,
            accuracy=accuracy
        )
    
    def log_error(self, model_name: str, error: str, details: Dict[str, Any] = None):
        """에러를 로깅합니다."""
        self.logger.error(
            "model_error",
            model=model_name,
            error=error,
            details=details or {}
        )

metrics_logger = MetricsLogger() 