"""
AI 모델 로더
RTX 4060Ti 16GB에 최적화된 모델 로딩 및 관리
"""

import os
import logging
import gc
from typing import Dict, Optional, Any, List
from pathlib import Path

import torch
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    AutoModelForTokenClassification, AutoModelForQuestionAnswering,
    pipeline, BitsAndBytesConfig
)
from sentence_transformers import SentenceTransformer
import numpy as np

from utils.config import settings, get_model_loading_config, get_cuda_settings


class ModelLoader:
    """AI 모델 로더 및 관리자"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}
        self.device = self._setup_device()
        
        # 모델 캐시 디렉토리 생성
        self.cache_dir = Path(settings.MODEL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # CUDA 메모리 최적화
        self._optimize_cuda_memory()
    
    def _setup_device(self) -> torch.device:
        """CUDA 디바이스 설정"""
        if torch.cuda.is_available():
            # RTX 4060Ti 설정
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            
            # 메모리 할당 전략
            torch.cuda.set_per_process_memory_fraction(0.85)  # 16GB의 85% 사용
            
            device = torch.device("cuda:0")
            self.logger.info(f"CUDA 디바이스 사용: {torch.cuda.get_device_name(0)}")
            self.logger.info(f"CUDA 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        else:
            device = torch.device("cpu")
            self.logger.warning("CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
        
        return device
    
    def _optimize_cuda_memory(self):
        """CUDA 메모리 최적화"""
        if self.device.type == "cuda":
            # 메모리 정리
            torch.cuda.empty_cache()
            gc.collect()
            
            # 메모리 할당 전략 설정
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
            
            # 그래디언트 체크포인팅 활성화
            if settings.GRADIENT_CHECKPOINTING:
                torch.utils.checkpoint.checkpoint_sequential = True
    
    def load_sentiment_model(self, model_name: str = "klue/bert-base") -> Any:
        """감정 분석 모델 로드"""
        cache_key = f"sentiment_{model_name}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        try:
            self.logger.info(f"감정 분석 모델 로딩 중: {model_name}")
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 모델 로드 (RTX 4060Ti 최적화)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if settings.MIXED_PRECISION else torch.float32,
                low_cpu_mem_usage=settings.LOW_CPU_MEM_USAGE,
                device_map="auto" if settings.DEVICE_MAP == "auto" else None
            )
            
            if settings.DEVICE_MAP != "auto":
                model = model.to(self.device)
            
            # 그래디언트 체크포인팅 활성화
            if settings.GRADIENT_CHECKPOINTING:
                model.gradient_checkpointing_enable()
            
            # 캐시에 저장
            self.models[cache_key] = model
            self.tokenizers[cache_key] = tokenizer
            
            self.logger.info("감정 분석 모델 로딩 완료")
            return model
            
        except Exception as e:
            self.logger.error(f"감정 분석 모델 로딩 실패: {e}")
            raise
    
    def load_bias_detection_model(self, model_name: str = "microsoft/DialoGPT-medium") -> Any:
        """편향 감지 모델 로드"""
        cache_key = f"bias_{model_name}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        try:
            self.logger.info(f"편향 감지 모델 로딩 중: {model_name}")
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 모델 로드
            model = AutoModel.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if settings.MIXED_PRECISION else torch.float32,
                low_cpu_mem_usage=settings.LOW_CPU_MEM_USAGE,
                device_map="auto" if settings.DEVICE_MAP == "auto" else None
            )
            
            if settings.DEVICE_MAP != "auto":
                model = model.to(self.device)
            
            # 그래디언트 체크포인팅 활성화
            if settings.GRADIENT_CHECKPOINTING:
                model.gradient_checkpointing_enable()
            
            # 캐시에 저장
            self.models[cache_key] = model
            self.tokenizers[cache_key] = tokenizer
            
            self.logger.info("편향 감지 모델 로딩 완료")
            return model
            
        except Exception as e:
            self.logger.error(f"편향 감지 모델 로딩 실패: {e}")
            raise
    
    def load_fact_checking_model(self, model_name: str = "google/t5-base") -> Any:
        """사실 확인 모델 로드"""
        cache_key = f"fact_{model_name}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        try:
            self.logger.info(f"사실 확인 모델 로딩 중: {model_name}")
            
            # 토크나이저 로드
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 모델 로드
            model = AutoModel.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float16 if settings.MIXED_PRECISION else torch.float32,
                low_cpu_mem_usage=settings.LOW_CPU_MEM_USAGE,
                device_map="auto" if settings.DEVICE_MAP == "auto" else None
            )
            
            if settings.DEVICE_MAP != "auto":
                model = model.to(self.device)
            
            # 그래디언트 체크포인팅 활성화
            if settings.GRADIENT_CHECKPOINTING:
                model.gradient_checkpointing_enable()
            
            # 캐시에 저장
            self.models[cache_key] = model
            self.tokenizers[cache_key] = tokenizer
            
            self.logger.info("사실 확인 모델 로딩 완료")
            return model
            
        except Exception as e:
            self.logger.error(f"사실 확인 모델 로딩 실패: {e}")
            raise
    
    def load_sentence_embedding_model(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Any:
        """문장 임베딩 모델 로드"""
        cache_key = f"embedding_{model_name}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        try:
            self.logger.info(f"문장 임베딩 모델 로딩 중: {model_name}")
            
            # SentenceTransformer 모델 로드
            model = SentenceTransformer(
                model_name,
                cache_folder=str(self.cache_dir),
                device=str(self.device)
            )
            
            # 캐시에 저장
            self.models[cache_key] = model
            
            self.logger.info("문장 임베딩 모델 로딩 완료")
            return model
            
        except Exception as e:
            self.logger.error(f"문장 임베딩 모델 로딩 실패: {e}")
            raise
    
    def load_custom_model(self, model_name: str, model_type: str = "auto") -> Any:
        """커스텀 모델 로드"""
        cache_key = f"custom_{model_name}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        try:
            self.logger.info(f"커스텀 모델 로딩 중: {model_name}")
            
            # 모델 타입에 따른 로딩
            if model_type == "sequence_classification":
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    **get_model_loading_config()
                )
            elif model_type == "token_classification":
                model = AutoModelForTokenClassification.from_pretrained(
                    model_name,
                    **get_model_loading_config()
                )
            elif model_type == "question_answering":
                model = AutoModelForQuestionAnswering.from_pretrained(
                    model_name,
                    **get_model_loading_config()
                )
            else:
                model = AutoModel.from_pretrained(
                    model_name,
                    **get_model_loading_config()
                )
            
            # 토크나이저도 로드
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True
                )
                self.tokenizers[cache_key] = tokenizer
            except Exception:
                self.logger.warning(f"토크나이저 로딩 실패: {model_name}")
            
            # 캐시에 저장
            self.models[cache_key] = model
            
            self.logger.info("커스텀 모델 로딩 완료")
            return model
            
        except Exception as e:
            self.logger.error(f"커스텀 모델 로딩 실패: {e}")
            raise
    
    def get_tokenizer(self, model_name: str) -> Optional[Any]:
        """토크나이저 반환"""
        # 캐시에서 찾기
        for key, tokenizer in self.tokenizers.items():
            if model_name in key:
                return tokenizer
        
        # 직접 로드 시도
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            return tokenizer
        except Exception:
            return None
    
    def unload_model(self, model_name: str):
        """모델 언로드 및 메모리 정리"""
        cache_key = None
        
        # 캐시에서 찾기
        for key in list(self.models.keys()):
            if model_name in key:
                cache_key = key
                break
        
        if cache_key:
            # 모델 제거
            del self.models[cache_key]
            
            # 토크나이저도 제거
            if cache_key in self.tokenizers:
                del self.tokenizers[cache_key]
            
            # CUDA 메모리 정리
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
                gc.collect()
            
            self.logger.info(f"모델 언로드 완료: {model_name}")
    
    def get_loaded_models(self) -> List[str]:
        """로드된 모델 목록 반환"""
        return list(self.models.keys())
    
    def get_memory_usage(self) -> Dict[str, float]:
        """메모리 사용량 반환"""
        if self.device.type == "cuda":
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            return {
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "usage_percent": round((allocated / total) * 100, 1)
            }
        else:
            return {"cpu_mode": True}
    
    def cleanup(self):
        """모든 모델 정리 및 메모리 해제"""
        self.logger.info("모든 모델 정리 중...")
        
        # 모델 정리
        self.models.clear()
        self.tokenizers.clear()
        
        # CUDA 메모리 정리
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        
        # 가비지 컬렉션
        gc.collect()
        
        self.logger.info("모든 모델 정리 완료")
    
    def __del__(self):
        """소멸자에서 정리"""
        self.cleanup()


# 전역 모델 로더 인스턴스
model_loader = ModelLoader()
