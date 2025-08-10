"""
학습된 모델 서비스
"""

import torch
import time
import logging
from typing import Dict, Any, Optional
from models.multitask_credibility_model import MultiTaskCredibilityModel

logger = logging.getLogger(__name__)

class TrainedModelService:
    """학습된 모델 서비스"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """학습된 모델 로드"""
        try:
            logger.info("학습된 모델 로딩 시작...")
            
            # 모델 인스턴스 생성
            self.model = MultiTaskCredibilityModel()
            
            # 학습된 가중치 로드
            self.model.load_state_dict(
                torch.load('multitask_credibility_model_optimized.pth', 
                          map_location=self.device)
            )
            
            # 모델을 평가 모드로 설정
            self.model.eval()
            
            self.model_loaded = True
            logger.info("✅ 학습된 모델 로드 완료")
            
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {e}")
            self.model_loaded = False
            raise
    
    def is_model_loaded(self) -> bool:
        """모델 로드 상태 확인"""
        return self.model_loaded and self.model is not None
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """텍스트 분석"""
        if not self.is_model_loaded():
            raise RuntimeError("모델이 로드되지 않았습니다")
        
        try:
            start_time = time.time()
            
            # 멀티태스크 분석 실행
            result = self.model.predict_multiple_tasks(text)
            
            processing_time = time.time() - start_time
            
            # 결과 포맷팅
            formatted_result = {
                "success": True,
                "data": {
                    "credibility_score": result['overall']['credibility_score'],
                    "harmlessness_score": result['harmlessness']['safety_score'],
                    "honesty_score": result['honesty']['confidence_score'],
                    "helpfulness_score": result['helpfulness']['confidence_score'],
                    "analysis_breakdown": {
                        "harmlessness": result['harmlessness']['safety_score'],
                        "honesty": result['honesty']['confidence_score'],
                        "helpfulness": result['helpfulness']['confidence_score']
                    },
                    "overall_grade": self._get_grade(result['overall']['credibility_score']),
                    "explanation": self._generate_explanation(result),
                    "confidence": result['overall']['credibility_score'] / 100.0
                },
                "processing_time": processing_time,
                "model_version": "trained_v1.0"
            }
            
            logger.info(f"텍스트 분석 완료 - 처리시간: {processing_time:.2f}초")
            return formatted_result
            
        except Exception as e:
            logger.error(f"텍스트 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0
            }
    
    def _get_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 80:
            return "높음"
        elif score >= 60:
            return "중간"
        else:
            return "낮음"
    
    def _generate_explanation(self, result: Dict[str, Any]) -> str:
        """분석 결과 설명 생성"""
        overall_score = result['overall']['credibility_score']
        harmlessness = result['harmlessness']['safety_score']
        honesty = result['honesty']['confidence_score']
        helpfulness = result['helpfulness']['confidence_score']
        
        explanation_parts = []
        
        # 전체 신뢰도
        if overall_score >= 80:
            explanation_parts.append("전체적으로 신뢰도가 높습니다")
        elif overall_score >= 60:
            explanation_parts.append("전체적으로 신뢰도가 보통입니다")
        else:
            explanation_parts.append("전체적으로 신뢰도가 낮습니다")
        
        # 세부 분석
        if harmlessness >= 80:
            explanation_parts.append("무해성 측면에서 안전합니다")
        elif harmlessness < 60:
            explanation_parts.append("무해성 측면에서 주의가 필요합니다")
        
        if honesty >= 80:
            explanation_parts.append("정보 정확성이 높습니다")
        elif honesty < 60:
            explanation_parts.append("정보 정확성에 의문이 있습니다")
        
        if helpfulness >= 80:
            explanation_parts.append("도움적 정성이 높습니다")
        elif helpfulness < 60:
            explanation_parts.append("도움적 정성이 낮습니다")
        
        return " | ".join(explanation_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_loaded": self.is_model_loaded(),
            "device": str(self.device),
            "model_version": "trained_v1.0",
            "model_type": "MultiTaskCredibilityModel",
            "gpu_available": torch.cuda.is_available()
        }

# 전역 모델 서비스 인스턴스
trained_model_service = TrainedModelService() 