"""
애플리케이션 설정 관리 모듈
환경 변수와 기본 설정을 중앙에서 관리합니다.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 기본 서버 설정
    APP_NAME: str = "Info-Guard Python Server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Info-Guard API"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 데이터베이스 설정
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"
    
    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # YouTube API 설정
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_API_QUOTA_LIMIT: int = 10000
    
    # AI 모델 설정
    AI_MODEL_PATH: str = "./models"
    USE_GPU: bool = True
    GPU_MEMORY_LIMIT: str = "14GB"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 캐시 설정
    CACHE_TTL: int = 3600  # 1시간
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스를 반환합니다."""
    return settings
