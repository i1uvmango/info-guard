#!/usr/bin/env python3
"""
BERT 기반 신뢰성 모델 테스트 스크립트
저장된 가중치 파일과 호환되는 모델을 테스트합니다.
"""

import sys
import os
import torch
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from models.bert_credibility_model import BertCredibilityModel
from config.logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

def test_model_loading():
    """모델 로딩 테스트"""
    try:
        logger.info("=== BERT 모델 로딩 테스트 시작 ===")
        
        # 모델 인스턴스 생성
        model = BertCredibilityModel()
        logger.info("✅ BERT 모델 인스턴스 생성 성공")
        
        # 모델 정보 출력
        model_info = model.get_model_info()
        logger.info(f"모델 정보: {model_info}")
        
        # 학습된 가중치 로드
        model_path = Path(__file__).parent / "models" / "credibility_model.pth"
        if not model_path.exists():
            logger.error(f"❌ 모델 파일을 찾을 수 없습니다: {model_path}")
            return False
        
        # 모델 가중치 로드
        success = model.load_pretrained_weights(str(model_path))
        if not success:
            logger.error("❌ 가중치 로드 실패")
            return False
        
        logger.info("✅ 모델 가중치 로드 성공")
        
        # 모델을 평가 모드로 설정
        model.eval()
        logger.info("✅ 모델을 평가 모드로 설정")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 모델 로딩 실패: {e}")
        return False

def test_model_prediction():
    """모델 예측 테스트"""
    try:
        logger.info("=== 모델 예측 테스트 시작 ===")
        
        # 모델 로드
        model = BertCredibilityModel()
        model_path = Path(__file__).parent / "models" / "credibility_model.pth"
        model.load_pretrained_weights(str(model_path))
        model.eval()
        
        # 테스트 텍스트
        test_texts = [
            "이 영상은 매우 신뢰할 수 있는 정보를 제공합니다.",
            "이 내용은 사실과 다를 수 있습니다.",
            "이 정보는 검증되지 않았습니다."
        ]
        
        for i, text in enumerate(test_texts, 1):
            logger.info(f"테스트 {i}: {text}")
            
            # 예측 실행
            result = model.predict_multiple_tasks(text)
            
            logger.info(f"  결과: {result}")
            
            # 기본적인 결과 검증
            assert 'harmlessness' in result, "무해성 점수가 없습니다"
            assert 'honesty' in result, "정확성 점수가 없습니다"
            assert 'helpfulness' in result, "도움성 점수가 없습니다"
            
            # 점수 범위 검증 (0.0 ~ 1.0)
            for key, value in result.items():
                assert 0.0 <= value <= 1.0, f"{key} 점수가 범위를 벗어났습니다: {value}"
            
            logger.info(f"  ✅ 테스트 {i} 통과")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 모델 예측 테스트 실패: {e}")
        return False

def test_gpu_optimization():
    """GPU 최적화 테스트"""
    try:
        logger.info("=== GPU 최적화 테스트 시작 ===")
        
        if not torch.cuda.is_available():
            logger.warning("⚠️ GPU를 사용할 수 없습니다. CPU 모드로 테스트합니다.")
            return True
        
        # GPU 정보 출력
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU: {gpu_name}")
        logger.info(f"GPU 메모리: {gpu_memory:.1f}GB")
        
        # 모델 로드
        model = BertCredibilityModel()
        model_path = Path(__file__).parent / "models" / "credibility_model.pth"
        model.load_pretrained_weights(str(model_path))
        model.eval()
        
        # GPU 메모리 사용량 확인
        allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
        cached_memory = torch.cuda.memory_reserved(0) / 1024**3
        
        logger.info(f"할당된 GPU 메모리: {allocated_memory:.2f}GB")
        logger.info(f"캐시된 GPU 메모리: {cached_memory:.2f}GB")
        
        # 메모리 사용량이 적절한지 확인 (전체 메모리의 80% 이하)
        if allocated_memory < gpu_memory * 0.8:
            logger.info("✅ GPU 메모리 사용량이 적절합니다")
        else:
            logger.warning("⚠️ GPU 메모리 사용량이 높습니다")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GPU 최적화 테스트 실패: {e}")
        return False

def test_model_performance():
    """모델 성능 테스트"""
    try:
        logger.info("=== 모델 성능 테스트 시작 ===")
        
        # 모델 로드
        model = BertCredibilityModel()
        model_path = Path(__file__).parent / "models" / "credibility_model.pth"
        model.load_pretrained_weights(str(model_path))
        model.eval()
        
        # 긴 텍스트로 성능 테스트
        long_text = "이것은 매우 긴 텍스트입니다. " * 100
        logger.info(f"긴 텍스트 길이: {len(long_text)} 문자")
        
        import time
        start_time = time.time()
        
        # 예측 실행
        result = model.predict_multiple_tasks(long_text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info(f"처리 시간: {processing_time:.3f}초")
        logger.info(f"결과: {result}")
        
        # 처리 시간이 적절한지 확인 (5초 이하)
        if processing_time < 5.0:
            logger.info("✅ 처리 시간이 적절합니다")
        else:
            logger.warning("⚠️ 처리 시간이 길 수 있습니다")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 모델 성능 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    logger.info("🚀 BERT 기반 신뢰성 모델 테스트 시작")
    
    tests = [
        ("모델 로딩", test_model_loading),
        ("모델 예측", test_model_prediction),
        ("GPU 최적화", test_gpu_optimization),
        ("모델 성능", test_model_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 테스트 통과")
            else:
                logger.error(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            logger.error(f"❌ {test_name} 테스트에서 예외 발생: {e}")
    
    logger.info(f"\n=== 테스트 결과 ===")
    logger.info(f"통과: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 모든 테스트가 통과했습니다!")
        return True
    else:
        logger.error("💥 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
