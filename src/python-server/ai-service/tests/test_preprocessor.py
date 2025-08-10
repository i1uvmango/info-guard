"""
ContentPreprocessor 클래스 단위 테스트
"""

import unittest
from unittest.mock import patch, mock_open
import tempfile
import os
from pathlib import Path

# 상위 디렉토리의 모듈을 import하기 위한 경로 설정
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.content_classifier.preprocessor import ContentPreprocessor


class TestContentPreprocessor(unittest.TestCase):
    """ContentPreprocessor 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.preprocessor = ContentPreprocessor()
    
    def test_init(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.preprocessor.stop_words)
        self.assertIsNotNone(self.preprocessor.category_mapping)
        self.assertIsNotNone(self.preprocessor.reverse_category_mapping)
        self.assertEqual(len(self.preprocessor.category_mapping), 4)
    
    def test_load_korean_stopwords(self):
        """한국어 불용어 로드 테스트"""
        stopwords = self.preprocessor._load_korean_stopwords()
        self.assertIsInstance(stopwords, set)
        self.assertGreater(len(stopwords), 0)
        
        # 기본 불용어가 포함되어 있는지 확인
        basic_stopwords = {'이', '그', '저', '것', '수', '등'}
        for word in basic_stopwords:
            self.assertIn(word, stopwords)
    
    def test_normalize_text(self):
        """텍스트 정규화 테스트"""
        # 기본 정규화
        text = "안녕하세요! 반갑습니다."
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "안녕하세요 반갑습니다")
        
        # URL 제거
        text = "링크: https://example.com 텍스트"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "링크 텍스트")
        
        # 해시태그 처리
        text = "#정치 #뉴스 내용"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "정치 뉴스 내용")
        
        # 멘션 제거
        text = "@사용자 안녕하세요"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "안녕하세요")
        
        # 이모티콘 제거
        text = "안녕 😊 반갑습니다"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "안녕 반갑습니다")
        
        # 특수문자 정리
        text = "특수문자!@#$%^&*()"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "특수문자")
        
        # 연속 공백 처리
        text = "여러    공백"
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "여러 공백")
        
        # 빈 문자열 처리
        text = ""
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "")
        
        # None 처리
        text = None
        normalized = self.preprocessor._normalize_text(text)
        self.assertEqual(normalized, "")
    
    def test_remove_stopwords(self):
        """불용어 제거 테스트"""
        text = "이것은 테스트 텍스트입니다"
        cleaned = self.preprocessor._remove_stopwords(text)
        self.assertNotIn("이것", cleaned)
        self.assertIn("테스트", cleaned)
        self.assertIn("텍스트", cleaned)
        
        # 빈 문자열 처리
        text = ""
        cleaned = self.preprocessor._remove_stopwords(text)
        self.assertEqual(cleaned, "")
    
    def test_combine_texts(self):
        """텍스트 결합 테스트"""
        title = "제목"
        description = "설명"
        tags = ["태그1", "태그2"]
        
        combined = self.preprocessor._combine_texts(title, description, tags)
        self.assertEqual(combined, "제목 설명 태그1 태그2")
        
        # 일부가 비어있는 경우
        combined = self.preprocessor._combine_texts(title, "", tags)
        self.assertEqual(combined, "제목 태그1 태그2")
        
        # 모두 비어있는 경우
        combined = self.preprocessor._combine_texts("", "", [])
        self.assertEqual(combined, "")
    
    def test_preprocess_text(self):
        """전체 전처리 파이프라인 테스트"""
        title = "정치 뉴스 제목"
        description = "정치 관련 설명입니다"
        tags = ["정치", "뉴스", "분석"]
        
        result = self.preprocessor.preprocess_text(title, description, tags)
        
        # 결과 구조 확인
        self.assertIn("original", result)
        self.assertIn("processed", result)
        self.assertIn("metadata", result)
        
        # 원본 데이터 확인
        self.assertEqual(result["original"]["title"], title)
        self.assertEqual(result["original"]["description"], description)
        self.assertEqual(result["original"]["tags"], tags)
        
        # 전처리된 데이터 확인
        self.assertIn("title", result["processed"])
        self.assertIn("description", result["processed"])
        self.assertIn("tags", result["processed"])
        self.assertIn("combined", result["processed"])
        
        # 메타데이터 확인
        self.assertIn("title_length", result["metadata"])
        self.assertIn("description_length", result["metadata"])
        self.assertIn("tags_count", result["metadata"])
        self.assertIn("processed_length", result["metadata"])
    
    def test_preprocess_text_validation(self):
        """전처리 입력 검증 테스트"""
        # 제목이 비어있는 경우
        with self.assertRaises(ValueError):
            self.preprocessor.preprocess_text("", "설명", ["태그"])
        
        # 제목이 None인 경우
        with self.assertRaises(ValueError):
            self.preprocessor.preprocess_text(None, "설명", ["태그"])
        
        # 제목이 문자열이 아닌 경우
        with self.assertRaises(ValueError):
            self.preprocessor.preprocess_text(123, "설명", ["태그"])
    
    def test_category_mapping(self):
        """카테고리 매핑 테스트"""
        # ID에서 이름으로
        self.assertEqual(self.preprocessor.get_category_name(0), "정치")
        self.assertEqual(self.preprocessor.get_category_name(1), "경제")
        self.assertEqual(self.preprocessor.get_category_name(2), "시사")
        self.assertEqual(self.preprocessor.get_category_name(3), "기타")
        
        # 이름에서 ID로
        self.assertEqual(self.preprocessor.get_category_id("정치"), 0)
        self.assertEqual(self.preprocessor.get_category_id("경제"), 1)
        self.assertEqual(self.preprocessor.get_category_id("시사"), 2)
        self.assertEqual(self.preprocessor.get_category_id("기타"), 3)
        
        # 알 수 없는 카테고리
        self.assertEqual(self.preprocessor.get_category_id("알수없음"), 3)  # 기본값
        self.assertEqual(self.preprocessor.get_category_name(999), "기타")  # 기본값
    
    def test_validate_input(self):
        """입력 검증 테스트"""
        # 정상 입력
        self.assertTrue(self.preprocessor.validate_input("제목", "설명", ["태그"]))
        self.assertTrue(self.preprocessor.validate_input("제목", "", []))
        
        # 제목이 비어있는 경우
        self.assertFalse(self.preprocessor.validate_input("", "설명", ["태그"]))
        self.assertFalse(self.preprocessor.validate_input("   ", "설명", ["태그"]))
        
        # 제목이 너무 긴 경우
        long_title = "a" * 1001
        self.assertFalse(self.preprocessor.validate_input(long_title, "설명", ["태그"]))
        
        # 설명이 너무 긴 경우
        long_description = "a" * 5001
        self.assertFalse(self.preprocessor.validate_input("제목", long_description, ["태그"]))
        
        # 태그가 너무 많은 경우
        many_tags = [f"태그{i}" for i in range(51)]
        self.assertFalse(self.preprocessor.validate_input("제목", "설명", many_tags))
    
    def test_stopwords_file_loading(self):
        """불용어 파일 로딩 테스트"""
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("추가불용어1\n추가불용어2\n추가불용어3\n")
            temp_file_path = f.name
        
        try:
            # 파일이 존재하는 경우 테스트
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data="추가불용어1\n추가불용어2\n")):
                    preprocessor = ContentPreprocessor()
                    # 기본 불용어 + 추가 불용어가 포함되어 있는지 확인
                    self.assertIn("추가불용어1", preprocessor.stop_words)
                    self.assertIn("추가불용어2", preprocessor.stop_words)
        finally:
            # 임시 파일 삭제
            os.unlink(temp_file_path)


if __name__ == '__main__':
    unittest.main()
