"""
설정 관리 모듈
환경 변수와 애플리케이션 설정을 관리
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # YouTube API 설정
    YOUTUBE_API_KEY: Optional[str] = Field(default="", env="YOUTUBE_API_KEY", description="YouTube API 키 (로그에 출력되지 않음)")
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(
        default="postgresql://info_guard_user:secure_password@localhost:5432/info_guard",
        env="DATABASE_URL"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS 설정
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000,chrome-extension://*",
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1",
        env="ALLOWED_HOSTS"
    )
    
    # AI 모델 설정 (RTX 4060Ti 16GB 최적화)
    MODEL_CACHE_DIR: str = Field(default="./ai_models/cache", env="MODEL_CACHE_DIR")
    HUGGINGFACE_TOKEN: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")
    
    # CUDA 설정
    CUDA_VISIBLE_DEVICES: str = Field(default="0", env="CUDA_VISIBLE_DEVICES")
    CUDA_LAUNCH_BLOCKING: int = Field(default=1, env="CUDA_LAUNCH_BLOCKING")
    TORCH_CUDA_ARCH_LIST: str = Field(default="8.9", env="TORCH_CUDA_ARCH_LIST")  # RTX 4060Ti
    
    # 메모리 최적화 설정
    MAX_MEMORY_MB: int = Field(default=14000, env="MAX_MEMORY_MB")  # 16GB - 2GB 여유
    GRADIENT_CHECKPOINTING: bool = Field(default=True, env="GRADIENT_CHECKPOINTING")
    MIXED_PRECISION: bool = Field(default=True, env="MIXED_PRECISION")
    
    # 모델 로딩 설정
    MODEL_LOADING_STRATEGY: str = Field(default="auto", env="MODEL_LOADING_STRATEGY")
    DEVICE_MAP: str = Field(default="auto", env="DEVICE_MAP")
    LOW_CPU_MEM_USAGE: bool = Field(default=True, env="LOW_CPU_MEM_USAGE")
    
    # 배치 크기 설정
    TRAINING_BATCH_SIZE: int = Field(default=4, env="TRAINING_BATCH_SIZE")
    INFERENCE_BATCH_SIZE: int = Field(default=8, env="INFERENCE_BATCH_SIZE")
    GRADIENT_ACCUMULATION_STEPS: int = Field(default=4, env="GRADIENT_ACCUMULATION_STEPS")
    
    # 로깅 설정
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    LOG_MAX_SIZE: str = Field(default="10MB", env="LOG_MAX_SIZE")
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # 모니터링 설정
    ENABLE_WANDB: bool = Field(default=False, env="ENABLE_WANDB")
    WANDB_PROJECT: str = Field(default="info-guard", env="WANDB_PROJECT")
    ENABLE_TENSORBOARD: bool = Field(default=True, env="ENABLE_TENSORBOARD")
    
    # 캐시 설정
    ENABLE_MODEL_CACHE: bool = Field(default=True, env="ENABLE_MODEL_CACHE")
    CACHE_TTL_HOURS: int = Field(default=24, env="CACHE_TTL_HOURS")
    
    # API 제한 설정
    MAX_REQUESTS_PER_MINUTE: int = Field(default=100, env="MAX_REQUESTS_PER_MINUTE")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """ALLOWED_ORIGINS를 리스트로 변환"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [x.strip() for x in self.ALLOWED_ORIGINS.split(",") if x.strip()]
        return []
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """ALLOWED_HOSTS를 리스트로 변환"""
        if isinstance(self.ALLOWED_HOSTS, str):
            return [x.strip() for x in self.ALLOWED_HOSTS.split(",") if x.strip()]
        return []


# 전역 설정 인스턴스
settings = Settings()


def get_cuda_settings() -> dict:
    """CUDA 관련 설정 반환"""
    return {
        "device": "cuda:0" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu",
        "torch_dtype": "auto",
        "device_map": settings.DEVICE_MAP,
        "low_cpu_mem_usage": settings.LOW_CPU_MEM_USAGE,
        "max_memory": {0: f"{settings.MAX_MEMORY_MB}MB"},
        "gradient_checkpointing": settings.GRADIENT_CHECKPOINTING,
        "mixed_precision": settings.MIXED_PRECISION,
    }


def get_model_loading_config() -> dict:
    """모델 로딩 설정 반환"""
    return {
        "cache_dir": settings.MODEL_CACHE_DIR,
        "local_files_only": False,
        "trust_remote_code": True,
        "revision": "main",
        "use_auth_token": settings.HUGGINGFACE_TOKEN,
        **get_cuda_settings()
    }


def get_training_config() -> dict:
    """학습 설정 반환"""
    return {
        "per_device_train_batch_size": settings.TRAINING_BATCH_SIZE,
        "per_device_eval_batch_size": settings.INFERENCE_BATCH_SIZE,
        "gradient_accumulation_steps": settings.GRADIENT_ACCUMULATION_STEPS,
        "gradient_checkpointing": settings.GRADIENT_CHECKPOINTING,
        "fp16": settings.MIXED_PRECISION,
        "bf16": False,  # RTX 4060Ti는 FP16만 지원
        "dataloader_pin_memory": False,  # 메모리 절약
        "remove_unused_columns": True,
        "group_by_length": True,  # 배치 효율성 향상
    }
