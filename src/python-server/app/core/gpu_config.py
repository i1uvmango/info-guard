"""
GPU 가속 설정 및 모델 최적화 설정
RTX 4060Ti 16GB 최적화를 위한 설정
"""

import os
import torch
from typing import Dict, Any, Optional
from loguru import logger


class GPUConfig:
    """GPU 설정 및 최적화 관리"""
    
    def __init__(self):
        self.device = self._get_optimal_device()
        self.gpu_memory_limit = self._get_gpu_memory_limit()
        self.batch_size = self._get_optimal_batch_size()
        self.model_precision = self._get_optimal_precision()
        
    def _get_optimal_device(self) -> str:
        """최적의 디바이스 선택"""
        if torch.cuda.is_available():
            # CUDA 디바이스 정보 확인
            gpu_count = torch.cuda.device_count()
            logger.info(f"🖥️  사용 가능한 GPU: {gpu_count}개")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"  GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
            
            # RTX 4060Ti 우선 선택 (16GB VRAM)
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                if "4060" in gpu_name or "16GB" in gpu_name:
                    torch.cuda.set_device(i)
                    logger.info(f"✅ RTX 4060Ti 선택됨: GPU {i}")
                    return f"cuda:{i}"
            
            # 첫 번째 GPU 사용
            torch.cuda.set_device(0)
            logger.info(f"✅ GPU 0 선택됨")
            return "cuda:0"
        else:
            logger.warning("⚠️  CUDA를 사용할 수 없습니다. CPU 모드로 실행됩니다.")
            return "cpu"
    
    def _get_gpu_memory_limit(self) -> int:
        """GPU 메모리 제한 설정 (MB)"""
        if self.device.startswith("cuda"):
            # RTX 4060Ti 16GB 중 14GB 사용 (2GB 여유)
            return 14 * 1024
        return 0
    
    def _get_optimal_batch_size(self) -> int:
        """최적 배치 크기 계산"""
        if self.device.startswith("cuda"):
            # GPU 메모리에 따른 배치 크기 조정
            if self.gpu_memory_limit >= 14 * 1024:  # 14GB 이상
                return 8
            elif self.gpu_memory_limit >= 8 * 1024:  # 8GB 이상
                return 4
            else:
                return 2
        return 1
    
    def _get_optimal_precision(self) -> str:
        """최적 정밀도 선택"""
        if self.device.startswith("cuda"):
            # RTX 4060Ti는 FP16 지원
            return "fp16"
        return "fp32"
    
    def get_torch_config(self) -> Dict[str, Any]:
        """PyTorch 설정 반환"""
        config = {
            "device": self.device,
            "dtype": torch.float16 if self.model_precision == "fp16" else torch.float32,
            "batch_size": self.batch_size,
            "precision": self.model_precision
        }
        
        if self.device.startswith("cuda"):
            config.update({
                "cuda_available": True,
                "gpu_memory_limit": self.gpu_memory_limit,
                "gpu_name": torch.cuda.get_device_name(),
                "gpu_memory_allocated": torch.cuda.memory_allocated() / 1024**2,
                "gpu_memory_reserved": torch.cuda.memory_reserved() / 1024**2
            })
        
        return config
    
    def optimize_memory(self):
        """GPU 메모리 최적화"""
        if self.device.startswith("cuda"):
            # 메모리 캐시 정리
            torch.cuda.empty_cache()
            
            # 메모리 사용량 확인
            allocated = torch.cuda.memory_allocated() / 1024**2
            reserved = torch.cuda.memory_reserved() / 1024**2
            
            logger.info(f"💾 GPU 메모리 상태: 할당됨 {allocated:.1f}MB, 예약됨 {reserved:.1f}MB")
    
    def get_model_loading_config(self) -> Dict[str, Any]:
        """모델 로딩 최적화 설정"""
        return {
            "device_map": "auto" if self.device.startswith("cuda") else None,
            "torch_dtype": torch.float16 if self.model_precision == "fp16" else torch.float32,
            "low_cpu_mem_usage": True,
            "offload_folder": "offload" if self.device.startswith("cuda") else None
        }


# 전역 GPU 설정 인스턴스
gpu_config = GPUConfig()


def get_gpu_config() -> GPUConfig:
    """GPU 설정 인스턴스 반환"""
    return gpu_config


def is_gpu_available() -> bool:
    """GPU 사용 가능 여부 확인"""
    return gpu_config.device.startswith("cuda")


def get_optimal_device() -> str:
    """최적 디바이스 반환"""
    return gpu_config.device
