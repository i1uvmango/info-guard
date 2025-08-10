import os
from typing import Optional
try:
    from pydantic import BaseSettings
except ImportError:
    from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Info-Guard AI Service"
    
    # YouTube API 설정
    YOUTUBE_API_KEY: Optional[str] = None
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379"
    
    # 모델 설정
    MODEL_CACHE_DIR: str = "./models"
    MAX_TEXT_LENGTH: int = 512
    
    # GPU 최적화 설정
    BATCH_SIZE: int = 16  # 4에서 16으로 증가
    MAX_WORKERS: int = 4
    GPU_MEMORY_FRACTION: float = 0.8  # GPU 메모리의 80% 사용
    MIXED_PRECISION: bool = True  # FP16 사용
    GRADIENT_ACCUMULATION_STEPS: int = 2  # 그래디언트 누적
    
    # 성능 설정
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1시간
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 외부 API 설정
    FACT_CHECK_API_URL: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 