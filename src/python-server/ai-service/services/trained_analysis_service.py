"""
학습된 모델 기반 분석 서비스
"""

import time
import logging
from typing import Dict, Any, Optional
from services.trained_model_service import trained_model_service
from services.preprocessing_service import preprocessing_service

logger = logging.getLogger(__name__)

class TrainedAnalysisService:
    """학습된 모델 기반 분석 서비스"""
    
    def __init__(self):
        self.model_service = trained_model_service
        self.preprocessing_service = preprocessing_service
        logger.info("학습된 모델 분석 서비스 초기화 완료")
    
    def analyze_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """영상 신뢰도 분석"""
        try:
            start_time = time.time()
            logger.info("영상 분석 시작")
            
            # 1. 데이터 검증
            validation_result = self.preprocessing_service.validate_video_data(video_data)
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": f"데이터 검증 실패: {', '.join(validation_result['errors'])}",
                    "processing_time": 0
                }
            
            # 2. 전처리
            processed_data = self.preprocessing_service.preprocess_video_data(video_data)
            
            if not processed_data["has_content"]:
                return {
                    "success": False,
                    "error": "분석할 수 있는 텍스트가 부족합니다. 제목과 설명을 확인해주세요.",
                    "processing_time": 0,
                    "details": {
                        "title_available": bool(processed_data.get("title", "")),
                        "description_available": bool(processed_data.get("description", "")),
                        "transcript_available": bool(processed_data.get("transcript", ""))
                    }
                }
            
            # 3. 모델 분석
            analysis_result = self.model_service.analyze_text(processed_data["text"])
            
            # 4. 결과 후처리
            final_result = self._postprocess_result(analysis_result, processed_data, video_data)
            
            processing_time = time.time() - start_time
            final_result["processing_time"] = processing_time
            
            logger.info(f"영상 분석 완료 - 처리시간: {processing_time:.2f}초")
            return final_result
            
        except Exception as e:
            logger.error(f"영상 분석 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": 0
            }
    
    def _postprocess_result(self, analysis_result: Dict[str, Any], 
                          processed_data: Dict[str, Any], 
                          video_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과 후처리"""
        try:
            if not analysis_result["success"]:
                return analysis_result
            
            # 기본 분석 결과
            result = analysis_result.copy()
            
            # 추가 메타데이터
            result["metadata"] = {
                "video_id": video_data.get("video_id", ""),
                "video_url": video_data.get("video_url", ""),
                "text_length": processed_data["text_length"],
                "keywords": self.preprocessing_service.extract_keywords(processed_data["text"]),
                "model_version": "trained_v1.0"
            }
            
            # 신뢰도 등급 결정
            credibility_score = result["data"]["credibility_score"]
            result["data"]["credibility_grade"] = self._determine_grade(credibility_score)
            
            # 상세 분석 결과
            result["data"]["detailed_analysis"] = {
                "harmlessness": {
                    "score": result["data"]["analysis_breakdown"]["harmlessness"],
                    "grade": self._determine_grade(result["data"]["analysis_breakdown"]["harmlessness"]),
                    "description": "무해성 - 콘텐츠의 안전성"
                },
                "honesty": {
                    "score": result["data"]["analysis_breakdown"]["honesty"],
                    "grade": self._determine_grade(result["data"]["analysis_breakdown"]["honesty"]),
                    "description": "정보 정확성 - 사실 기반 여부"
                },
                "helpfulness": {
                    "score": result["data"]["analysis_breakdown"]["helpfulness"],
                    "grade": self._determine_grade(result["data"]["analysis_breakdown"]["helpfulness"]),
                    "description": "도움적 정성 - 유용성"
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"결과 후처리 실패: {e}")
            return analysis_result
    
    def _determine_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 80:
            return "높음"
        elif score >= 60:
            return "중간"
        else:
            return "낮음"
    
    def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "model_loaded": self.model_service.is_model_loaded(),
            "model_info": self.model_service.get_model_info(),
            "service_ready": self.model_service.is_model_loaded()
        }
    
    def analyze_batch(self, video_list: list) -> list:
        """배치 분석"""
        results = []
        
        for i, video_data in enumerate(video_list):
            logger.info(f"배치 분석 진행 중: {i+1}/{len(video_list)}")
            result = self.analyze_video(video_data)
            results.append(result)
        
        return results

# 전역 분석 서비스 인스턴스
trained_analysis_service = TrainedAnalysisService() 