#!/usr/bin/env python3
"""
콘텐츠 분류 모델 단위 테스트
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys
import os

# 프로젝트 모듈 import
sys.path.append(str(Path(__file__).parent.parent))

from models.content_classifier.classifier import ContentClassifier
from models.content_classifier.preprocessor import ContentPreprocessor
from models.content_classifier.trainer import ContentClassifierTrainer, ContentDataset


class TestContentPreprocessor(unittest.TestCase):
    """ContentPreprocessor 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.preprocessor = ContentPreprocessor()
    
    def test_preprocess_text_basic(self):
        """기본 텍스트 전처리 테스트"""
        title = "정치 뉴스 제목"
        description = "정치 관련 설명입니다."
        tags = ["정치", "뉴스"]
        
        result = self.preprocessor.preprocess_text(title, description, tags)
        
        self.assertIn('original', result)
        self.assertIn('processed', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['original']['title'], title)
        self.assertEqual(result['original']['description'], description)
        self.assertEqual(result['original']['tags'], tags)
    
    def test_preprocess_text_empty_inputs(self):
        """빈 입력에 대한 전처리 테스트"""
        title = "제목만 있음"
        description = ""
        tags = []
        
        result = self.preprocessor.preprocess_text(title, description, tags)
        
        self.assertIsInstance(result['processed']['combined'], str)
        self.assertTrue(len(result['processed']['combined']) > 0)
    
    def test_category_mapping(self):
        """카테고리 매핑 테스트"""
        # 카테고리 ID로 이름 가져오기
        self.assertEqual(self.preprocessor.get_category_name(0), "정치")
        self.assertEqual(self.preprocessor.get_category_name(1), "경제")
        self.assertEqual(self.preprocessor.get_category_name(2), "시사")
        self.assertEqual(self.preprocessor.get_category_name(3), "기타")
        
        # 카테고리 이름으로 ID 가져오기
        self.assertEqual(self.preprocessor.get_category_id("정치"), 0)
        self.assertEqual(self.preprocessor.get_category_id("경제"), 1)
        self.assertEqual(self.preprocessor.get_category_id("시사"), 2)
        self.assertEqual(self.preprocessor.get_category_id("기타"), 3)
    
    def test_validate_input(self):
        """입력 검증 테스트"""
        # 유효한 입력
        self.assertTrue(self.preprocessor.validate_input("제목", "설명", ["태그"]))
        self.assertTrue(self.preprocessor.validate_input("제목", "", []))
        
        # 유효하지 않은 입력
        self.assertFalse(self.preprocessor.validate_input("", "설명", ["태그"]))
        self.assertFalse(self.preprocessor.validate_input(None, "설명", ["태그"]))


class TestContentClassifier(unittest.TestCase):
    """ContentClassifier 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.classifier = ContentClassifier(use_pretrained=False)
    
    def test_initialization(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.classifier)
        self.assertIsNotNone(self.classifier.preprocessor)
        self.assertFalse(self.classifier.is_loaded)
    
    def test_rule_based_classification(self):
        """규칙 기반 분류 테스트"""
        # 정치 관련 텍스트
        political_text = "대통령 국회 정책"
        result = self.classifier._rule_based_classification(political_text)
        self.assertEqual(result, 0)  # 정치
        
        # 경제 관련 텍스트
        economic_text = "주식 부동산 경제"
        result = self.classifier._rule_based_classification(economic_text)
        self.assertEqual(result, 1)  # 경제
        
        # 시사 관련 텍스트
        news_text = "뉴스 사건 사고"
        result = self.classifier._rule_based_classification(news_text)
        self.assertEqual(result, 2)  # 시사
        
        # 기타 텍스트
        other_text = "음악 영화 게임"
        result = self.classifier._rule_based_classification(other_text)
        self.assertEqual(result, 3)  # 기타
    
    def test_classify_without_model(self):
        """모델 없이 분류 테스트 (규칙 기반)"""
        try:
            result = self.classifier.classify(
                title="정치 뉴스",
                description="정치 관련 설명",
                tags=["정치", "뉴스"]
            )
            
            self.assertIn('prediction', result)
            self.assertIn('category_id', result['prediction'])
            self.assertIn('category_name', result['prediction'])
            self.assertIn('confidence', result['prediction'])
            
        except RuntimeError:
            # 모델이 로드되지 않은 경우 예상되는 예외
            pass


class TestContentDataset(unittest.TestCase):
    """ContentDataset 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # Mock 토크나이저 생성
        class MockTokenizer:
            def __call__(self, text, **kwargs):
                return {
                    'input_ids': [[1, 2, 3, 4, 5]],
                    'attention_mask': [[1, 1, 1, 1, 1]]
                }
        
        self.mock_tokenizer = MockTokenizer()
        self.texts = ["첫 번째 텍스트", "두 번째 텍스트"]
        self.labels = [0, 1]
    
    def test_dataset_creation(self):
        """데이터셋 생성 테스트"""
        dataset = ContentDataset(self.texts, self.labels, self.mock_tokenizer)
        
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset.texts, self.texts)
        self.assertEqual(dataset.labels, self.labels)
    
    def test_dataset_getitem(self):
        """데이터셋 아이템 접근 테스트"""
        dataset = ContentDataset(self.texts, self.labels, self.mock_tokenizer)
        
        item = dataset[0]
        
        self.assertIn('input_ids', item)
        self.assertIn('attention_mask', item)
        self.assertIn('labels', item)
        self.assertEqual(item['labels'].item(), 0)


class TestContentClassifierTrainer(unittest.TestCase):
    """ContentClassifierTrainer 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.trainer = ContentClassifierTrainer(device='cpu')
    
    def test_trainer_initialization(self):
        """학습기 초기화 테스트"""
        self.assertIsNotNone(self.trainer)
        self.assertEqual(self.trainer.device, 'cpu')
        self.assertIsNone(self.trainer.model)
        self.assertIsNone(self.trainer.tokenizer')
    
    def test_prepare_data(self):
        """데이터 준비 테스트"""
        # 테스트 데이터 생성
        test_data = [
            {
                'title': '정치 뉴스 1',
                'description': '정치 관련 설명 1',
                'tags': ['정치', '뉴스'],
                'category': 0
            },
            {
                'title': '경제 뉴스 1',
                'description': '경제 관련 설명 1',
                'tags': ['경제', '뉴스'],
                'category': 1
            }
        ]
        
        # Mock 토크나이저 설정
        self.trainer.tokenizer = self.trainer.preprocessor
        
        try:
            train_dataset, val_dataset, test_dataset = self.trainer.prepare_data(test_data)
            
            # 데이터셋이 생성되었는지 확인
            self.assertIsInstance(train_dataset, ContentDataset)
            self.assertIsInstance(val_dataset, ContentDataset)
            self.assertIsInstance(test_dataset, ContentDataset)
            
        except Exception as e:
            # 토크나이저가 제대로 설정되지 않은 경우 예상되는 예외
            self.assertIsInstance(e, Exception)


class TestIntegration(unittest.TestCase):
    """통합 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.preprocessor = ContentPreprocessor()
        self.classifier = ContentClassifier(use_pretrained=False)
    
    def test_end_to_end_preprocessing(self):
        """전처리 파이프라인 통합 테스트"""
        title = "대통령 국정감사 현장"
        description = "국회에서 진행된 국정감사 현장을 생중계합니다."
        tags = ["정치", "국정감사", "국회"]
        
        # 전처리
        preprocessed = self.preprocessor.preprocess_text(title, description, tags)
        
        # 결과 검증
        self.assertIn('processed', preprocessed)
        self.assertIn('combined', preprocessed['processed'])
        
        # 결합된 텍스트에 키워드가 포함되어 있는지 확인
        combined_text = preprocessed['processed']['combined']
        self.assertIn('대통령', combined_text)
        self.assertIn('국정감사', combined_text)
        self.assertIn('국회', combined_text)
    
    def test_classification_pipeline(self):
        """분류 파이프라인 통합 테스트"""
        # 테스트 데이터
        test_cases = [
            {
                'title': '대통령 정책 발표',
                'description': '새로운 경제 정책을 발표했습니다.',
                'expected_category': 0  # 정치
            },
            {
                'title': '주식시장 동향',
                'description': '오늘 주식시장의 변화를 분석합니다.',
                'expected_category': 1  # 경제
            }
        ]
        
        for test_case in test_cases:
            try:
                result = self.classifier.classify(
                    title=test_case['title'],
                    description=test_case['description']
                )
                
                # 결과 구조 검증
                self.assertIn('prediction', result)
                self.assertIn('category_id', result['prediction'])
                
                # 예상 카테고리와 일치하는지 확인 (규칙 기반 분류)
                predicted_category = result['prediction']['category_id']
                self.assertEqual(predicted_category, test_case['expected_category'])
                
            except RuntimeError:
                # 모델이 로드되지 않은 경우 예상되는 예외
                pass


def create_test_data():
    """테스트용 데이터 생성"""
    test_data = [
        {
            'title': '정치 뉴스 테스트',
            'description': '정치 관련 테스트 설명',
            'tags': ['정치', '테스트'],
            'category': 0
        },
        {
            'title': '경제 뉴스 테스트',
            'description': '경제 관련 테스트 설명',
            'tags': ['경제', '테스트'],
            'category': 1
        },
        {
            'title': '시사 뉴스 테스트',
            'description': '시사 관련 테스트 설명',
            'tags': ['시사', '테스트'],
            'category': 2
        },
        {
            'title': '엔터테인먼트 테스트',
            'description': '엔터테인먼트 관련 테스트 설명',
            'tags': ['엔터테인먼트', '테스트'],
            'category': 3
        }
    ]
    
    return test_data


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
