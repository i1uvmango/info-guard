"""
콘텐츠 전처리 모듈

유튜브 영상의 제목, 설명, 태그를 전처리하여 모델 입력에 적합한 형태로 변환합니다.
"""

import re
import json
from typing import Dict, List, Optional
from pathlib import Path


class ContentPreprocessor:
    """콘텐츠 전처리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 설정 파일 경로 (선택사항)
        """
        self.stop_words = self._load_korean_stopwords()
        self.category_mapping = {
            0: "정치", 1: "경제", 2: "시사", 3: "기타"
        }
        self.reverse_category_mapping = {v: k for k, v in self.category_mapping.items()}
        
        # 한국어 특수 표현 패턴
        self.korean_patterns = {
            '줄임말': r'[가-힣]+[ㄱ-ㅎㅏ-ㅣ]*',
            '이모티콘': r'[😀-🙿🌀-🗿]',
            'URL': r'https?://[^\s]+',
            '해시태그': r'#[가-힣a-zA-Z0-9_]+',
            '멘션': r'@[가-힣a-zA-Z0-9_]+'
        }
    
    def _load_korean_stopwords(self) -> set:
        """한국어 불용어 목록을 로드합니다."""
        # 기본 한국어 불용어
        basic_stopwords = {
            '이', '그', '저', '것', '수', '등', '때', '곳', '말', '일',
            '그것', '이것', '저것', '그때', '이때', '저때', '그곳', '이곳', '저곳',
            '그래서', '그러면', '그런데', '그리고', '하지만', '또는', '또한',
            '아', '어', '오', '우', '으', '이', '야', '여', '요', '유'
        }
        
        # 파일에서 추가 불용어 로드 시도
        try:
            stopwords_file = Path(__file__).parent.parent.parent / "data" / "stopwords.txt"
            if stopwords_file.exists():
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    file_stopwords = set(line.strip() for line in f if line.strip())
                basic_stopwords.update(file_stopwords)
        except Exception:
            pass  # 파일이 없어도 기본 불용어로 동작
        
        return basic_stopwords
    
    def preprocess_text(self, title: str, description: str, tags: List[str]) -> Dict:
        """
        제목, 설명, 태그를 전처리합니다.
        
        Args:
            title: 영상 제목
            description: 영상 설명
            tags: 영상 태그 리스트
            
        Returns:
            전처리된 텍스트 정보를 담은 딕셔너리
        """
        # 입력 검증
        if not title or not isinstance(title, str):
            raise ValueError("제목은 비어있지 않은 문자열이어야 합니다.")
        
        # 텍스트 정규화
        normalized_title = self._normalize_text(title)
        normalized_description = self._normalize_text(description) if description else ""
        normalized_tags = [self._normalize_text(tag) for tag in tags] if tags else []
        
        # 불용어 제거
        cleaned_title = self._remove_stopwords(normalized_title)
        cleaned_description = self._remove_stopwords(normalized_description)
        cleaned_tags = [self._remove_stopwords(tag) for tag in normalized_tags]
        
        # 결합된 텍스트 생성
        combined_text = self._combine_texts(cleaned_title, cleaned_description, cleaned_tags)
        
        return {
            "original": {
                "title": title,
                "description": description,
                "tags": tags
            },
            "processed": {
                "title": cleaned_title,
                "description": cleaned_description,
                "tags": cleaned_tags,
                "combined": combined_text
            },
            "metadata": {
                "title_length": len(title),
                "description_length": len(description) if description else 0,
                "tags_count": len(tags) if tags else 0,
                "processed_length": len(combined_text)
            }
        }
    
    def _normalize_text(self, text: str) -> str:
        """텍스트를 정규화합니다."""
        if not text:
            return ""
        
        # 소문자 변환 (한국어는 대소문자 구분이 없지만 일관성을 위해)
        text = text.lower()
        
        # URL 제거
        text = re.sub(self.korean_patterns['URL'], '', text)
        
        # 해시태그에서 # 제거
        text = re.sub(self.korean_patterns['해시태그'], lambda m: m.group()[1:], text)
        
        # 멘션 제거
        text = re.sub(self.korean_patterns['멘션'], '', text)
        
        # 이모티콘 제거
        text = re.sub(self.korean_patterns['이모티콘'], '', text)
        
        # 특수문자 정리 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
        
        # 연속된 공백을 단일 공백으로 변환
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _remove_stopwords(self, text: str) -> str:
        """불용어를 제거합니다."""
        if not text:
            return ""
        
        words = text.split()
        filtered_words = [word for word in words if word not in self.stop_words]
        
        return ' '.join(filtered_words)
    
    def _combine_texts(self, title: str, description: str, tags: List[str]) -> str:
        """전처리된 텍스트들을 결합합니다."""
        parts = []
        
        if title:
            parts.append(title)
        
        if description:
            parts.append(description)
        
        if tags:
            parts.extend(tags)
        
        return ' '.join(parts)
    
    def get_category_id(self, category_name: str) -> int:
        """카테고리 이름을 ID로 변환합니다."""
        return self.reverse_category_mapping.get(category_name, 3)  # 기본값: 기타
    
    def get_category_name(self, category_id: int) -> str:
        """카테고리 ID를 이름으로 변환합니다."""
        return self.category_mapping.get(category_id, "기타")
    
    def validate_input(self, title: str, description: str, tags: List[str]) -> bool:
        """입력 데이터의 유효성을 검증합니다."""
        if not title or len(title.strip()) == 0:
            return False
        
        if len(title) > 1000:  # 제목 길이 제한
            return False
        
        if description and len(description) > 5000:  # 설명 길이 제한
            return False
        
        if tags and len(tags) > 50:  # 태그 개수 제한
            return False
        
        return True
