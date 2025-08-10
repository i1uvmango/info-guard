"""
콘텐츠 분류 모델 학습 모듈

KoBERT 모델을 사용하여 콘텐츠 분류 모델을 학습시킵니다.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments, 
    Trainer,
    EarlyStoppingCallback
)
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from typing import Dict, List, Optional, Tuple
import json
import logging
from pathlib import Path
import time

from .preprocessor import ContentPreprocessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentDataset(Dataset):
    """콘텐츠 분류를 위한 데이터셋 클래스"""
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 512):
        """
        Args:
            texts: 전처리된 텍스트 리스트
            labels: 카테고리 라벨 리스트 (0-3)
            tokenizer: KoBERT 토크나이저
            max_length: 최대 토큰 길이
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # 토큰화
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class ContentClassifierTrainer:
    """콘텐츠 분류 모델 학습 클래스"""
    
    def __init__(self, model_name: str = "klue/bert-base", device: Optional[str] = None):
        """
        Args:
            model_name: 사용할 사전훈련 모델 이름
            device: 사용할 디바이스
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.preprocessor = ContentPreprocessor()
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        logger.info(f"디바이스: {self.device}")
        logger.info(f"모델: {model_name}")
    
    def setup_model(self):
        """모델과 토크나이저를 설정합니다."""
        try:
            logger.info("토크나이저 로드 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            logger.info("모델 로드 중...")
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=4,  # 정치, 경제, 시사, 기타
                ignore_mismatched_sizes=True
            )
            
            # 디바이스로 이동
            self.model.to(self.device)
            
            logger.info("모델 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 설정 실패: {e}")
            return False
    
    def prepare_data(self, data: List[Dict]) -> Tuple[ContentDataset, ContentDataset, ContentDataset]:
        """
        데이터를 학습용, 검증용, 테스트용으로 분할하고 데이터셋을 생성합니다.
        
        Args:
            data: 원본 데이터 리스트
                각 항목은 {'title': str, 'description': str, 'tags': List[str], 'category': int} 형태
        
        Returns:
            (train_dataset, val_dataset, test_dataset)
        """
        logger.info("데이터 준비 중...")
        
        # 텍스트 전처리
        processed_texts = []
        labels = []
        
        for item in data:
            try:
                preprocessed = self.preprocessor.preprocess_text(
                    title=item['title'],
                    description=item.get('description', ''),
                    tags=item.get('tags', [])
                )
                
                processed_texts.append(preprocessed['processed']['combined'])
                labels.append(item['category'])
                
            except Exception as e:
                logger.warning(f"데이터 전처리 실패: {e}")
                continue
        
        logger.info(f"전처리 완료: {len(processed_texts)}개 샘플")
        
        # 데이터 분할 (70:15:15)
        train_texts, temp_texts, train_labels, temp_labels = train_test_split(
            processed_texts, labels, test_size=0.3, random_state=42, stratify=labels
        )
        
        val_texts, test_texts, val_labels, test_labels = train_test_split(
            temp_texts, temp_labels, test_size=0.5, random_state=42, stratify=temp_labels
        )
        
        # 데이터셋 생성
        train_dataset = ContentDataset(train_texts, train_labels, self.tokenizer)
        val_dataset = ContentDataset(val_texts, val_labels, self.tokenizer)
        test_dataset = ContentDataset(test_texts, test_labels, self.tokenizer)
        
        logger.info(f"데이터 분할 완료:")
        logger.info(f"  학습: {len(train_dataset)}개")
        logger.info(f"  검증: {len(val_dataset)}개")
        logger.info(f"  테스트: {len(test_dataset)}개")
        
        return train_dataset, val_dataset, test_dataset
    
    def train(self, 
              train_dataset: ContentDataset, 
              val_dataset: ContentDataset,
              output_dir: str = "./content_classifier_model",
              **kwargs) -> bool:
        """
        모델을 학습시킵니다.
        
        Args:
            train_dataset: 학습 데이터셋
            val_dataset: 검증 데이터셋
            output_dir: 모델 저장 디렉토리
            **kwargs: 추가 학습 인자
        
        Returns:
            학습 성공 여부
        """
        if not self.model or not self.tokenizer:
            logger.error("모델이 설정되지 않았습니다. setup_model()을 먼저 호출하세요.")
            return False
        
        try:
            logger.info("모델 학습 시작...")
            
            # 학습 인자 설정
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=kwargs.get('num_epochs', 3),
                per_device_train_batch_size=kwargs.get('train_batch_size', 16),
                per_device_eval_batch_size=kwargs.get('eval_batch_size', 16),
                warmup_steps=kwargs.get('warmup_steps', 500),
                weight_decay=kwargs.get('weight_decay', 0.01),
                logging_dir=f"{output_dir}/logs",
                logging_steps=kwargs.get('logging_steps', 10),
                evaluation_strategy="steps",
                eval_steps=kwargs.get('eval_steps', 100),
                save_steps=kwargs.get('save_steps', 500),
                load_best_model_at_end=True,
                metric_for_best_model="eval_accuracy",
                greater_is_better=True,
                save_total_limit=3,
                dataloader_num_workers=kwargs.get('num_workers', 2),
                fp16=kwargs.get('fp16', torch.cuda.is_available()),
                gradient_accumulation_steps=kwargs.get('gradient_accumulation_steps', 1),
                learning_rate=kwargs.get('learning_rate', 2e-5),
                lr_scheduler_type=kwargs.get('lr_scheduler_type', 'linear'),
                remove_unused_columns=False
            )
            
            # Trainer 생성
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                tokenizer=self.tokenizer,
                compute_metrics=self._compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # 학습 실행
            start_time = time.time()
            train_result = self.trainer.train()
            training_time = time.time() - start_time
            
            # 모델 저장
            self.trainer.save_model()
            self.tokenizer.save_pretrained(output_dir)
            
            # 학습 결과 로깅
            logger.info("학습 완료!")
            logger.info(f"학습 시간: {training_time:.2f}초")
            logger.info(f"최종 손실: {train_result.training_loss:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"학습 실패: {e}")
            return False
    
    def _compute_metrics(self, eval_pred):
        """평가 메트릭을 계산합니다."""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='weighted'
        )
        acc = accuracy_score(labels, predictions)
        
        return {
            'accuracy': acc,
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
    
    def evaluate(self, test_dataset: ContentDataset) -> Dict:
        """
        테스트 데이터셋에 대해 모델을 평가합니다.
        
        Args:
            test_dataset: 테스트 데이터셋
        
        Returns:
            평가 결과
        """
        if not self.trainer:
            logger.error("학습된 모델이 없습니다. train()을 먼저 호출하세요.")
            return {}
        
        try:
            logger.info("모델 평가 중...")
            
            # 평가 실행
            eval_results = self.trainer.evaluate(test_dataset)
            
            # 예측 수행
            predictions = self.trainer.predict(test_dataset)
            pred_labels = np.argmax(predictions.predictions, axis=1)
            true_labels = predictions.label_ids
            
            # 카테고리별 정확도 계산
            category_accuracy = {}
            for i in range(4):
                mask = true_labels == i
                if np.sum(mask) > 0:
                    cat_acc = np.mean(pred_labels[mask] == true_labels[mask])
                    category_accuracy[self.preprocessor.get_category_name(i)] = {
                        "accuracy": cat_acc,
                        "count": int(np.sum(mask))
                    }
            
            # 결과 구성
            results = {
                "overall_metrics": {
                    "eval_loss": eval_results.get("eval_loss", 0),
                    "eval_accuracy": eval_results.get("eval_accuracy", 0),
                    "eval_f1": eval_results.get("eval_f1", 0),
                    "eval_precision": eval_results.get("eval_precision", 0),
                    "eval_recall": eval_results.get("eval_recall", 0)
                },
                "category_accuracy": category_accuracy,
                "predictions_count": len(predictions.predictions),
                "confusion_matrix": self._create_confusion_matrix(true_labels, pred_labels)
            }
            
            logger.info(f"평가 완료 - 정확도: {results['overall_metrics']['eval_accuracy']:.4f}")
            return results
            
        except Exception as e:
            logger.error(f"평가 실패: {e}")
            return {}
    
    def _create_confusion_matrix(self, true_labels: np.ndarray, pred_labels: np.ndarray) -> List[List[int]]:
        """혼동 행렬을 생성합니다."""
        matrix = [[0] * 4 for _ in range(4)]
        
        for true, pred in zip(true_labels, pred_labels):
            matrix[true][pred] += 1
        
        return matrix
    
    def save_model(self, output_dir: str) -> bool:
        """
        학습된 모델을 저장합니다.
        
        Args:
            output_dir: 저장할 디렉토리 경로
        
        Returns:
            저장 성공 여부
        """
        try:
            if not self.trainer:
                logger.error("저장할 모델이 없습니다.")
                return False
            
            # 모델 저장
            self.trainer.save_model(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            
            # 설정 정보 저장
            config = {
                "model_name": self.model_name,
                "num_labels": 4,
                "categories": self.preprocessor.category_mapping,
                "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "device": self.device
            }
            
            with open(f"{output_dir}/config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"모델 저장 완료: {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
            return False
    
    def load_trained_model(self, model_path: str) -> bool:
        """
        학습된 모델을 로드합니다.
        
        Args:
            model_path: 모델 경로
        
        Returns:
            로드 성공 여부
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                logger.error(f"모델 경로를 찾을 수 없습니다: {model_path}")
                return False
            
            # 토크나이저와 모델 로드
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
            
            # 디바이스로 이동
            self.model.to(self.device)
            
            logger.info(f"학습된 모델 로드 완료: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def get_training_summary(self) -> Dict:
        """학습 요약 정보를 반환합니다."""
        if not self.trainer:
            return {"error": "학습된 모델이 없습니다."}
        
        return {
            "model_name": self.model_name,
            "device": self.device,
            "training_args": self.trainer.args.to_dict() if self.trainer.args else {},
            "model_config": self.model.config.to_dict() if self.model else {}
        }
