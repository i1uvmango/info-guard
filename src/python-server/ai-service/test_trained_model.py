"""
학습된 모델 테스트 스크립트
"""

import torch
import time
import logging
from models.multitask_credibility_model import MultiTaskCredibilityModel

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_loading():
    """모델 로딩 테스트"""
    try:
        logger.info("모델 로딩 테스트 시작...")
        
        # 모델 인스턴스 생성
        model = MultiTaskCredibilityModel()
        logger.info("모델 인스턴스 생성 완료")
        
        # 학습된 가중치 로드
        model.load_state_dict(
            torch.load('multitask_credibility_model_optimized.pth', 
                      map_location=model.device)
        )
        logger.info("학습된 가중치 로드 완료")
        
        # 평가 모드로 설정
        model.eval()
        logger.info("모델을 평가 모드로 설정")
        
        return model
        
    except Exception as e:
        logger.error(f"모델 로딩 실패: {e}")
        raise

def test_model_prediction(model):
    """모델 예측 테스트"""
    try:
        logger.info("모델 예측 테스트 시작...")
        
        # 테스트 텍스트들
        test_texts = [
            "이 뉴스는 사실을 바탕으로 작성되었습니다.",  # 높은 신뢰도
            "충격적인 진실! 당신이 몰랐던 놀라운 사실!",  # 낮은 신뢰도
            "과학적 연구 결과에 따르면 이 방법이 효과적입니다.",  # 중간 신뢰도
            "믿을 수 없는 이야기! 반드시 봐야 합니다!",  # 낮은 신뢰도
            "전문가들의 합의에 따르면 이 정책이 효과적일 것으로 예상됩니다."  # 높은 신뢰도
        ]
        
        results = []
        
        for i, text in enumerate(test_texts):
            logger.info(f"텍스트 {i+1} 분석 중: {text[:50]}...")
            
            start_time = time.time()
            
            # 단일 태스크 예측
            single_result = model.predict_credibility(text, "harmlessness")
            
            # 멀티태스크 예측
            multi_result = model.predict_multiple_tasks(text)
            
            processing_time = time.time() - start_time
            
            result = {
                'text': text,
                'single_task': single_result,
                'multi_task': multi_result,
                'processing_time': processing_time
            }
            
            results.append(result)
            
            logger.info(f"텍스트 {i+1} 분석 완료 - 처리시간: {processing_time:.2f}초")
            logger.info(f"  단일 태스크 점수: {single_result['safety_score']:.1f}")
            logger.info(f"  멀티태스크 점수: {multi_result['overall']['credibility_score']:.1f}")
        
        return results
        
    except Exception as e:
        logger.error(f"모델 예측 테스트 실패: {e}")
        raise

def test_gpu_memory_usage():
    """GPU 메모리 사용량 테스트"""
    try:
        if torch.cuda.is_available():
            logger.info("GPU 메모리 사용량 테스트...")
            
            # 초기 메모리 상태
            torch.cuda.empty_cache()
            initial_memory = torch.cuda.memory_allocated() / 1024**2
            logger.info(f"초기 GPU 메모리: {initial_memory:.1f}MB")
            
            # 모델 로드 후 메모리
            model = test_model_loading()
            model_memory = torch.cuda.memory_allocated() / 1024**2
            logger.info(f"모델 로드 후 GPU 메모리: {model_memory:.1f}MB")
            logger.info(f"모델 사용 메모리: {model_memory - initial_memory:.1f}MB")
            
            # 예측 후 메모리
            test_model_prediction(model)
            final_memory = torch.cuda.memory_allocated() / 1024**2
            logger.info(f"예측 후 GPU 메모리: {final_memory:.1f}MB")
            
            # 메모리 정리
            del model
            torch.cuda.empty_cache()
            cleaned_memory = torch.cuda.memory_allocated() / 1024**2
            logger.info(f"정리 후 GPU 메모리: {cleaned_memory:.1f}MB")
            
        else:
            logger.info("GPU를 사용할 수 없습니다. CPU 모드로 테스트합니다.")
            
    except Exception as e:
        logger.error(f"GPU 메모리 테스트 실패: {e}")

def test_input_output_format():
    """입력/출력 형식 테스트"""
    try:
        logger.info("입력/출력 형식 테스트...")
        
        model = test_model_loading()
        
        # 테스트 입력
        test_input = {
            "text": "이것은 테스트 텍스트입니다.",
            "title": "테스트 제목",
            "description": "테스트 설명",
            "transcript": "테스트 자막"
        }
        
        # 텍스트 결합
        combined_text = " ".join([
            test_input["title"],
            test_input["description"], 
            test_input["transcript"]
        ])
        
        logger.info(f"결합된 텍스트: {combined_text}")
        
        # 예측 실행
        result = model.predict_multiple_tasks(combined_text)
        
        # 출력 형식 확인
        expected_keys = ['harmlessness', 'honesty', 'helpfulness', 'overall']
        for key in expected_keys:
            assert key in result, f"결과에 {key} 키가 없습니다"
        
        logger.info("출력 형식 테스트 통과")
        logger.info(f"결과 구조: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        logger.error(f"입력/출력 형식 테스트 실패: {e}")
        raise

def main():
    """메인 테스트 함수"""
    logger.info("학습된 모델 테스트 시작")
    
    try:
        # 1. 모델 로딩 테스트
        logger.info("=== 1. 모델 로딩 테스트 ===")
        model = test_model_loading()
        logger.info("✅ 모델 로딩 테스트 통과")
        
        # 2. 입력/출력 형식 테스트
        logger.info("=== 2. 입력/출력 형식 테스트 ===")
        format_result = test_input_output_format()
        logger.info("✅ 입력/출력 형식 테스트 통과")
        
        # 3. 모델 예측 테스트
        logger.info("=== 3. 모델 예측 테스트 ===")
        prediction_results = test_model_prediction(model)
        logger.info("✅ 모델 예측 테스트 통과")
        
        # 4. GPU 메모리 사용량 테스트
        logger.info("=== 4. GPU 메모리 사용량 테스트 ===")
        test_gpu_memory_usage()
        logger.info("✅ GPU 메모리 사용량 테스트 통과")
        
        # 5. 결과 요약
        logger.info("=== 테스트 결과 요약 ===")
        logger.info(f"총 {len(prediction_results)}개 텍스트 분석 완료")
        
        for i, result in enumerate(prediction_results):
            overall_score = result['multi_task']['overall']['credibility_score']
            processing_time = result['processing_time']
            logger.info(f"텍스트 {i+1}: 점수 {overall_score:.1f}, 처리시간 {processing_time:.2f}초")
        
        logger.info("🎉 모든 테스트 통과!")
        
    except Exception as e:
        logger.error(f"테스트 실패: {e}")
        raise

if __name__ == "__main__":
    main() 