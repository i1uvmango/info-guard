"""
AI 모델 기본 클래스
모든 AI 모델이 상속받아야 하는 기본 클래스입니다.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModel
from loguru import logger

from app.core.gpu_config import get_gpu_config, is_gpu_available


class BaseAIModel(ABC):
    """AI 모델의 기본 클래스"""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.is_loaded = False
        self.model = None
        self.tokenizer = None
        self.gpu_config = get_gpu_config()
        self.device = device
        
    @abstractmethod
    def analyze(self, text: str, **kwargs) -> Any:
        """텍스트를 분석합니다."""
        pass
    
    @abstractmethod
    def load_model(self) -> bool:
        """모델을 로드합니다. 하위 클래스에서 구현해야 합니다."""
        pass
    
    def load_huggingface_model(self, model_name: str, task: str) -> bool:
        """Hugging Face 모델을 로드합니다."""
        try:
            logger.info(f"Hugging Face 모델 로딩 시작: {model_name}")
            
            # 모델 및 토크나이저 로드
            self.model = AutoModel.from_pretrained(model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # GPU 사용 가능시 GPU로 이동
            if self.device.startswith("cuda") and torch.cuda.is_available():
                self.model = self.model.to(self.device)
                logger.info(f"모델을 GPU로 이동: {self.device}")
            else:
                self.device = "cpu"
                logger.info("모델을 CPU로 이동")
            
            self.is_loaded = True
            logger.info(f"✅ Hugging Face 모델 로딩 완료: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Hugging Face 모델 로딩 실패: {e}")
            self.is_loaded = False
            return False
    
    def unload_model(self) -> bool:
        """모델을 언로드합니다."""
        try:
            if not self.is_loaded:
                return True
            
            # 모델 및 토크나이저 정리
            if hasattr(self, 'model'):
                del self.model
                self.model = None
            
            if hasattr(self, 'tokenizer'):
                del self.tokenizer
                self.tokenizer = None
            
            self.is_loaded = False
            logger.info("모델 언로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 언로드 실패: {e}")
            return False
    
    def ensure_model_loaded(self) -> bool:
        """모델이 로드되어 있는지 확인하고, 필요시 로드합니다."""
        if not self.is_loaded:
            logger.info(f"🔄 {self.model_name} 모델이 로드되지 않았습니다. 로딩을 시작합니다.")
            return self.load_model()
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """모델 상태를 반환합니다."""
        status = {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "device": self.device,
            "gpu_available": is_gpu_available()
        }
        
        if is_gpu_available():
            status.update({
                "gpu_memory_allocated": torch.cuda.memory_allocated() / 1024**2,
                "gpu_memory_reserved": torch.cuda.memory_reserved() / 1024**2
            })
        
        return status
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보를 반환합니다."""
        if not self.is_loaded:
            return {"error": "모델이 로드되지 않았습니다."}
        
        info = {
            "model_name": self.model_name,
            "model_type": type(self.model).__name__,
            "tokenizer_type": type(self.tokenizer).__name__,
            "device": str(next(self.model.parameters()).device) if self.model else None,
            "parameters": sum(p.numel() for p in self.model.parameters()) if self.model else 0
        }
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """모델 상태를 확인합니다."""
        try:
            status = {
                "model_name": self.model_name,
                "is_loaded": self.is_loaded,
                "device": self.device,
                "gpu_available": torch.cuda.is_available() if self.device.startswith("cuda") else False
            }
            
            if self.is_loaded:
                status.update({
                    "model_type": type(self.model).__name__ if self.model else None,
                    "tokenizer_type": type(self.tokenizer).__name__ if self.tokenizer else None
                })
            
            return status
            
        except Exception as e:
            logger.error(f"헬스 체크 실패: {e}")
            return {
                "model_name": self.model_name,
                "error": str(e)
            }
    
    def __del__(self):
        """소멸자: GPU 메모리 정리"""
        try:
            if hasattr(self, 'model') and self.model is not None:
                if is_gpu_available():
                    del self.model
                    torch.cuda.empty_cache()
        except:
            pass
