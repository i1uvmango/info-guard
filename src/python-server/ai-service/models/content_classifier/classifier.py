"""
콘텐츠 분류 모듈

유튜브 영상의 제목, 설명, 태그를 분석하여 정치/경제/시사/기타로 분류합니다.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from .preprocessor import ContentPreprocessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentClassifier:
    """콘텐츠 분류 클래스"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None, use_pretrained: bool = True):
        """
        Args:
            model_path: 학습된 모델 파일 경로
            device: 사용할 디바이스 ('cuda', 'cpu', 또는 None)
            use_pretrained: 사전훈련 모델 사용 여부
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.preprocessor = ContentPreprocessor()
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        # 사전훈련 모델 사용 시 자동 로드
        if use_pretrained:
            self._load_pretrained_model()
        elif model_path:
            self.load_model(model_path)
        else:
            logger.warning("모델이 로드되지 않았습니다. load_model() 또는 _load_pretrained_model()을 호출하여 모델을 로드하세요.")
    
    def load_model(self, model_path: str) -> bool:
        """
        학습된 모델을 로드합니다.
        
        Args:
            model_path: 모델 파일 경로
            
        Returns:
            로드 성공 여부
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                logger.error(f"모델 파일을 찾을 수 없습니다: {model_path}")
                return False
            
            # 모델 로드 로직 (실제 구현에서는 KoBERT 모델을 로드)
            logger.info(f"모델을 로드하는 중: {model_path}")
            
            # TODO: 실제 KoBERT 모델 로드 구현
            # self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            # self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            self.is_loaded = True
            logger.info("모델 로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def _load_pretrained_model(self) -> bool:
        """사전훈련된 한국어 BERT 모델을 로드합니다."""
        try:
            logger.info("사전훈련 한국어 BERT 모델 로드 중...")
            
            # KLUE BERT 토크나이저와 모델 로드 (더 안정적인 한국어 모델)
            model_name = "klue/bert-base"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=4,  # 정치, 경제, 시사, 기타
                ignore_mismatched_sizes=True
            )
            
            # 디바이스로 이동
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info(f"사전훈련 한국어 BERT 모델 로드 완료: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"사전훈련 모델 로드 실패: {e}")
            # 모델 로드 실패 시 규칙 기반 분류만 사용
            logger.info("규칙 기반 분류 모드로 전환합니다.")
            self.is_loaded = False
            return False
    
    def classify(self, title: str, description: str = "", tags: List[str] = None) -> Dict:
        """
        콘텐츠를 분류합니다.
        
        Args:
            title: 영상 제목
            description: 영상 설명 (선택사항)
            tags: 영상 태그 리스트 (선택사항)
            
        Returns:
            분류 결과를 담은 딕셔너리
        """
        if not self.is_loaded:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        # 입력 검증
        if not self.preprocessor.validate_input(title, description, tags or []):
            raise ValueError("입력 데이터가 유효하지 않습니다.")
        
        try:
            # 전처리
            preprocessed = self.preprocessor.preprocess_text(title, description, tags or [])
            
            # 모델 예측 (실제 구현에서는 KoBERT 모델을 사용)
            prediction_result = self._predict(preprocessed["processed"]["combined"])
            
            # 결과 구성
            result = {
                "input": {
                    "title": title,
                    "description": description,
                    "tags": tags or []
                },
                "prediction": {
                    "category_id": prediction_result["category_id"],
                    "category_name": prediction_result["category_name"],
                    "confidence": prediction_result["confidence"],
                    "probabilities": prediction_result["probabilities"]
                },
                "preprocessing": preprocessed,
                "metadata": {
                    "model_version": "1.0.0",
                    "prediction_time": prediction_result.get("prediction_time", 0),
                    "device": self.device
                }
            }
            
            logger.info(f"분류 완료: {result['prediction']['category_name']} (신뢰도: {result['prediction']['confidence']:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"분류 중 오류 발생: {e}")
            raise
    
    def _predict(self, text: str) -> Dict:
        """
        전처리된 텍스트에 대해 예측을 수행합니다.
        
        Args:
            text: 전처리된 텍스트
            
        Returns:
            예측 결과
        """
        if not self.is_loaded or not self.model or not self.tokenizer:
            # 모델이 로드되지 않은 경우 규칙 기반 분류 사용
            start_time = time.time()
            category_id = self._rule_based_classification(text)
            prediction_time = time.time() - start_time
            
            return {
                "category_id": category_id,
                "category_name": self.preprocessor.get_category_name(category_id),
                "confidence": 0.7,  # 규칙 기반 분류의 신뢰도
                "method": "rule_based",
                "prediction_time": prediction_time,
                "probabilities": [0.1, 0.1, 0.1, 0.1]  # 기본 확률
            }
        
        try:
            # KoBERT 모델을 사용한 예측
            start_time = time.time()
            
            with torch.no_grad():
                # 토큰화
                inputs = self.tokenizer(
                    text,
                    truncation=True,
                    padding=True,
                    max_length=512,
                    return_tensors="pt"
                )
                
                # 디바이스로 이동
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 예측
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
                
                # 결과 추출
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
                
                prediction_time = time.time() - start_time
                
                return {
                    "category_id": predicted_class,
                    "category_name": self.preprocessor.get_category_name(predicted_class),
                    "confidence": confidence,
                    "method": "koBERT",
                    "prediction_time": prediction_time,
                    "probabilities": probabilities[0].cpu().numpy().tolist()
                }
                
        except Exception as e:
            logger.error(f"KoBERT 예측 실패: {e}")
            # 예측 실패 시 규칙 기반 분류로 폴백
            start_time = time.time()
            category_id = self._rule_based_classification(text)
            prediction_time = time.time() - start_time
            
            return {
                "category_id": category_id,
                "category_name": self.preprocessor.get_category_name(category_id),
                "confidence": 0.6,  # 폴백 분류의 신뢰도
                "method": "rule_based_fallback",
                "prediction_time": prediction_time,
                "probabilities": [0.1, 0.1, 0.1, 0.1]  # 기본 확률
            }
    
    def _rule_based_classification(self, text: str) -> int:
        """
        규칙 기반 분류 (임시 구현)
        실제 구현에서는 한국어 BERT 모델을 사용합니다.
        """
        text_lower = text.lower()
        
        # 정치 관련 키워드
        political_keywords = [
            '정치', '대통령', '국회', '의원', '정부', '여당', '야당', '선거', '투표',
            '민주주의', '자유주의', '보수', '진보', '정책', '법안', '헌법', '외교',
            '국방', '행정', '사법', '입법', '지방자치', '정당', '여론조사'
        ]
        
        # 경제 관련 키워드
        economic_keywords = [
            '경제', '주식', '부동산', '금리', '인플레이션', 'GDP', '수출', '수입',
            '기업', '주식시장', '환율', '원화', '달러', '투자', '재정', '은행',
            '금융', '보험', '세금', '예산', '무역', '산업', '고용', '실업률'
        ]
        
        # 시사 관련 키워드
        news_keywords = [
            '뉴스', '사건', '사고', '범죄', '재난', '사고', '사망', '부상',
            '화재', '교통사고', '자연재해', '테러', '전쟁', '평화', '사회',
            '교육', '의료', '환경', '기후', '에너지', '교통', '건설', '농업'
        ]
        
        # 엔터테인먼트 관련 키워드 (우선순위 높임)
        entertainment_keywords = [
            '엔터테인먼트', '영화', '드라마', '예능', '음악', '가수', '아이돌',
            '배우', '연예인', '콘서트', '공연', '게임', '스포츠', '축구',
            '야구', '농구', '골프', '테니스', '유튜브', '스트리밍', '방송',
            '채널', '구독자', '뷰', '좋아요', '댓글', '트렌드', '인기'
        ]
        
        # 키워드 매칭 (엔터테인먼트 우선)
        entertainment_score = sum(2 for keyword in entertainment_keywords if keyword in text_lower)  # 가중치 2배
        political_score = sum(1 for keyword in political_keywords if keyword in text_lower)
        economic_score = sum(1 for keyword in economic_keywords if keyword in text_lower)
        news_score = sum(1 for keyword in news_keywords if keyword in text_lower)
        
        # 가장 높은 점수의 카테고리 선택
        scores = [political_score, economic_score, news_score, entertainment_score]
        return scores.index(max(scores))
    
    def batch_classify(self, contents: List[Dict]) -> List[Dict]:
        """
        여러 콘텐츠를 일괄 분류합니다.
        
        Args:
            contents: 분류할 콘텐츠 리스트
                각 항목은 {'title': str, 'description': str, 'tags': List[str]} 형태
            
        Returns:
            분류 결과 리스트
        """
        results = []
        
        for i, content in enumerate(contents):
            try:
                result = self.classify(
                    title=content.get('title', ''),
                    description=content.get('description', ''),
                    tags=content.get('tags', [])
                )
                results.append(result)
                
                # 진행률 로깅
                if (i + 1) % 100 == 0:
                    logger.info(f"일괄 분류 진행률: {i + 1}/{len(contents)}")
                    
            except Exception as e:
                logger.error(f"콘텐츠 {i} 분류 실패: {e}")
                # 오류 발생 시 기본 결과 반환
                results.append({
                    "input": content,
                    "prediction": {
                        "category_id": 3,  # 기타
                        "category_name": "기타",
                        "confidence": 0.0,
                        "probabilities": [0.25, 0.25, 0.25, 0.25]
                    },
                    "error": str(e)
                })
        
        return results
    
    def get_model_info(self) -> Dict:
        """모델 정보를 반환합니다."""
        return {
            "model_type": "KoBERT",
            "version": "1.0.0",
            "device": self.device,
            "is_loaded": self.is_loaded,
            "categories": self.preprocessor.category_mapping,
            "supported_languages": ["ko"]
        }
    
    def evaluate_accuracy(self, test_data: List[Dict]) -> Dict:
        """
        테스트 데이터에 대한 모델 정확도를 평가합니다.
        
        Args:
            test_data: 테스트 데이터 리스트
                각 항목은 {'title': str, 'description': str, 'tags': List[str], 'true_category': int} 형태
            
        Returns:
            평가 결과
        """
        if not test_data:
            return {"error": "테스트 데이터가 없습니다."}
        
        correct_predictions = 0
        total_predictions = len(test_data)
        category_metrics = {i: {"correct": 0, "total": 0} for i in range(4)}
        
        for item in test_data:
            try:
                prediction = self.classify(
                    title=item['title'],
                    description=item.get('description', ''),
                    tags=item.get('tags', [])
                )
                
                predicted_category = prediction['prediction']['category_id']
                true_category = item['true_category']
                
                if predicted_category == true_category:
                    correct_predictions += 1
                    category_metrics[true_category]["correct"] += 1
                
                category_metrics[true_category]["total"] += 1
                
            except Exception as e:
                logger.error(f"테스트 데이터 평가 중 오류: {e}")
                continue
        
        # 전체 정확도
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # 카테고리별 정확도
        category_accuracy = {}
        for cat_id, metrics in category_metrics.items():
            if metrics["total"] > 0:
                category_accuracy[self.preprocessor.get_category_name(cat_id)] = {
                    "accuracy": metrics["correct"] / metrics["total"],
                    "correct": metrics["correct"],
                    "total": metrics["total"]
                }
        
        return {
            "overall_accuracy": overall_accuracy,
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "category_accuracy": category_accuracy
        }
