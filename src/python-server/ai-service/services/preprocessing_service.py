"""
전처리 서비스
"""

import re
import logging
from typing import Dict, Any, List
from data_preprocessor import AIHubDataPreprocessor as DataPreprocessor

logger = logging.getLogger(__name__)

class PreprocessingService:
    """전처리 서비스"""
    
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        logger.info("전처리 서비스 초기화 완료")
    
    def preprocess_video_data(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """영상 데이터 전처리"""
        try:
            logger.info("영상 데이터 전처리 시작")
            
            # 기본 데이터 추출
            title = video_data.get("title", "")
            description = video_data.get("description", "")
            transcript = video_data.get("transcript", "")
            
            # 텍스트 정제
            cleaned_title = self._clean_text(title)
            cleaned_description = self._clean_text(description)
            cleaned_transcript = self._clean_text(transcript)
            
            # 텍스트 결합
            combined_text = self._combine_text({
                "title": cleaned_title,
                "description": cleaned_description,
                "transcript": cleaned_transcript
            })
            
            # 전처리된 데이터 반환
            processed_data = {
                "text": combined_text,
                "title": cleaned_title,
                "description": cleaned_description,
                "transcript": cleaned_transcript,
                "text_length": len(combined_text),
                "has_content": len(combined_text) > 0
            }
            
            logger.info(f"전처리 완료 - 텍스트 길이: {len(combined_text)}")
            return processed_data
            
        except Exception as e:
            logger.error(f"전처리 실패: {e}")
            return {
                "text": "",
                "title": "",
                "description": "",
                "transcript": "",
                "text_length": 0,
                "has_content": False,
                "error": str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _combine_text(self, text_data: Dict[str, str]) -> str:
        """텍스트 결합"""
        texts = []
        
        # 제목 추가
        if text_data.get("title"):
            texts.append(text_data["title"])
        
        # 설명 추가
        if text_data.get("description"):
            texts.append(text_data["description"])
        
        # 자막 추가 (있는 경우에만)
        if text_data.get("transcript"):
            texts.append(text_data["transcript"])
        
        # 텍스트 결합
        combined = " ".join(texts)
        
        # 최소 길이 확인 (제목이나 설명이 있는 경우 분석 가능)
        if len(combined.strip()) < 5:
            logger.warning("분석할 수 있는 텍스트가 부족합니다")
            return ""
        
        # 최대 길이 제한 (모델 입력 제한)
        if len(combined) > 1000:
            combined = combined[:1000] + "..."
        
        return combined
    
    def extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        try:
            # 간단한 키워드 추출 (실제로는 더 정교한 방법 사용)
            words = text.split()
            word_freq = {}
            
            for word in words:
                if len(word) > 1:  # 1글자 단어 제외
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 빈도순 정렬
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # 상위 10개 키워드 반환
            keywords = [word for word, freq in sorted_words[:10]]
            
            return keywords
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return []
    
    def validate_video_data(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """영상 데이터 검증"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 필수 필드 확인
        required_fields = ["title", "description", "transcript"]
        for field in required_fields:
            if field not in video_data:
                validation_result["errors"].append(f"필수 필드 누락: {field}")
                validation_result["is_valid"] = False
        
        # 텍스트 길이 확인
        combined_text = self._combine_text(video_data)
        if len(combined_text) < 10:
            validation_result["warnings"].append("텍스트가 너무 짧습니다")
        
        if len(combined_text) > 5000:
            validation_result["warnings"].append("텍스트가 너무 깁니다")
        
        return validation_result

# 전역 전처리 서비스 인스턴스
preprocessing_service = PreprocessingService() 