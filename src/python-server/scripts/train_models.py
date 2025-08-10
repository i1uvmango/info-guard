#!/usr/bin/env python3
"""
AI 모델 학습 스크립트
RTX 4060Ti 16GB에 최적화된 학습 파이프라인
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import time
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from transformers import (
    TrainingArguments, Trainer, DataCollatorWithPadding,
    EarlyStoppingCallback, IntervalStrategy, get_linear_schedule_with_warmup
)
from datasets import Dataset, load_dataset, concatenate_datasets
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from sklearn.model_selection import train_test_split
import pandas as pd
from tqdm import tqdm

from src.python_server.ai_models.model_loader import model_loader
from src.python_server.utils.config import settings, get_training_config
from src.python_server.data_processing.youtube_client import YouTubeClient


class ModelTrainer:
    """AI 모델 학습기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.youtube_client = YouTubeClient()
        
        # 로깅 설정
        self._setup_logging()
        
        # 학습 결과 저장 디렉토리
        self.output_dir = Path("./training_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # 학습 통계
        self.training_stats = {
            'start_time': None,
            'end_time': None,
            'models_trained': [],
            'total_parameters': 0,
            'gpu_memory_used': 0
        }
    
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(settings.LOG_FILE),
                logging.StreamHandler()
            ]
        )
    
    def _validate_data(self, data_path: str) -> bool:
        """데이터 유효성 검증"""
        try:
            if not os.path.exists(data_path):
                self.logger.error(f"데이터 파일이 존재하지 않습니다: {data_path}")
                return False
            
            # 파일 크기 확인
            file_size = os.path.getsize(data_path) / (1024 * 1024)  # MB
            if file_size < 0.1:  # 100KB 미만
                self.logger.warning(f"데이터 파일이 너무 작습니다: {file_size:.2f}MB")
            
            # 파일 형식 확인
            if data_path.endswith('.json'):
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, (list, dict)):
                        self.logger.error("JSON 파일 형식이 올바르지 않습니다")
                        return False
            elif data_path.endswith('.csv'):
                df = pd.read_csv(data_path, nrows=5)  # 처음 5행만 읽어서 확인
                if df.empty:
                    self.logger.error("CSV 파일이 비어있습니다")
                    return False
            
            self.logger.info(f"데이터 검증 완료: {data_path} ({file_size:.2f}MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"데이터 검증 실패: {e}")
            return False
    
    def _split_dataset(self, dataset: Dataset, test_size: float = 0.2, val_size: float = 0.1) -> Tuple[Dataset, Dataset, Dataset]:
        """데이터셋을 훈련/검증/테스트로 분할"""
        try:
            # 데이터셋을 pandas DataFrame으로 변환
            df = dataset.to_pandas()
            
            # 먼저 테스트셋 분리
            train_val_df, test_df = train_test_split(
                df, test_size=test_size, random_state=42, stratify=df['label']
            )
            
            # 훈련셋과 검증셋 분리
            train_df, val_df = train_test_split(
                train_val_df, test_size=val_size/(1-test_size), random_state=42, stratify=train_val_df['label']
            )
            
            # 다시 Dataset으로 변환
            train_dataset = Dataset.from_pandas(train_df)
            val_dataset = Dataset.from_pandas(val_df)
            test_dataset = Dataset.from_pandas(test_df)
            
            self.logger.info(f"데이터셋 분할 완료: 훈련({len(train_dataset)}), 검증({len(val_dataset)}), 테스트({len(test_dataset)})")
            
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            self.logger.error(f"데이터셋 분할 실패: {e}")
            raise
    
    def prepare_sentiment_dataset(self, data_path: str) -> Tuple[Dataset, Dataset, Dataset]:
        """감정 분석 데이터셋 준비"""
        try:
            if not self._validate_data(data_path):
                raise ValueError("데이터 검증 실패")
            
            # 데이터 로드
            if data_path.endswith('.json'):
                dataset = load_dataset('json', data_files=data_path)
            elif data_path.endswith('.csv'):
                dataset = load_dataset('csv', data_files=data_path)
            else:
                raise ValueError("지원하지 않는 데이터 형식입니다.")
            
            # 데이터 전처리
            def preprocess_function(examples):
                texts = [str(text).strip() for text in examples['text']]
                
                # 라벨 인코딩
                label_mapping = {'positive': 2, 'neutral': 1, 'negative': 0}
                labels = [label_mapping.get(label, 1) for label in examples['label']]
                
                return {
                    'text': texts,
                    'label': labels
                }
            
            # 데이터셋 전처리
            processed_dataset = dataset['train'].map(
                preprocess_function,
                remove_columns=dataset['train'].column_names
            )
            
            # 토크나이저 적용
            tokenizer = model_loader.get_tokenizer("klue/bert-base")
            if tokenizer is None:
                raise ValueError("토크나이저를 찾을 수 없습니다.")
            
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    padding='max_length',
                    max_length=512,
                    return_tensors='pt'
                )
            
            tokenized_dataset = processed_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=processed_dataset.column_names
            )
            
            # 데이터셋 분할
            train_dataset, val_dataset, test_dataset = self._split_dataset(tokenized_dataset)
            
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            self.logger.error(f"감정 분석 데이터셋 준비 실패: {e}")
            raise
    
    def train_sentiment_model(self, data_path: str, model_name: str = "klue/bert-base"):
        """감정 분석 모델 학습"""
        try:
            self.logger.info("감정 분석 모델 학습 시작")
            
            # 데이터셋 준비
            train_dataset, val_dataset, test_dataset = self.prepare_sentiment_dataset(data_path)
            
            # 모델 로드
            model = model_loader.load_sentiment_model(model_name)
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(
                tokenizer=model_loader.get_tokenizer(model_name),
                padding=True,
                return_tensors='pt'
            )
            
            # 학습 인수 설정 (RTX 4060Ti 최적화)
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "sentiment_model"),
                num_train_epochs=3,
                per_device_train_batch_size=settings.TRAINING_BATCH_SIZE,
                per_device_eval_batch_size=settings.INFERENCE_BATCH_SIZE,
                gradient_accumulation_steps=settings.GRADIENT_ACCUMULATION_STEPS,
                learning_rate=2e-5,
                weight_decay=0.01,
                warmup_steps=500,
                logging_steps=100,
                evaluation_strategy=IntervalStrategy.STEPS,
                eval_steps=500,
                save_steps=1000,
                save_total_limit=3,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=settings.MIXED_PRECISION,
                dataloader_pin_memory=False,
                remove_unused_columns=True,
                group_by_length=True,
                report_to="tensorboard" if settings.ENABLE_TENSORBOARD else None,
                run_name="sentiment_training",
                # 추가 최적화 설정
                gradient_checkpointing=True,
                optim="adamw_torch",
                lr_scheduler_type="linear",
                warmup_ratio=0.1,
                save_strategy="steps",
                logging_dir=str(self.output_dir / "sentiment_model" / "logs")
            )
            
            # 메트릭 계산 함수
            def compute_metrics(eval_pred):
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
            
            # 트레이너 초기화
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # 학습 실행
            trainer.train()
            
            # 모델 저장
            trainer.save_model()
            
            # 테스트셋으로 평가
            test_results = self.evaluate_model(trainer, test_dataset)
            
            # 학습 통계 업데이트
            self.training_stats['models_trained'].append({
                'name': 'sentiment_model',
                'test_results': test_results,
                'model_path': str(self.output_dir / "sentiment_model")
            })
            
            self.logger.info("감정 분석 모델 학습 완료")
            
            return trainer
            
        except Exception as e:
            self.logger.error(f"감정 분석 모델 학습 실패: {e}")
            raise
    
    def prepare_bias_dataset(self, data_path: str) -> Tuple[Dataset, Dataset, Dataset]:
        """편향 감지 데이터셋 준비"""
        try:
            if not self._validate_data(data_path):
                raise ValueError("데이터 검증 실패")
            
            # 데이터 로드
            if data_path.endswith('.json'):
                dataset = load_dataset('json', data_files=data_path)
            elif data_path.endswith('.csv'):
                dataset = load_dataset('csv', data_files=data_path)
            else:
                raise ValueError("지원하지 않는 데이터 형식입니다.")
            
            # 데이터 전처리
            def preprocess_function(examples):
                texts = [str(text).strip() for text in examples['text']]
                
                # 편향 라벨 (0: 중립, 1: 편향)
                bias_labels = [1 if label == 'biased' else 0 for label in examples['bias_label']]
                
                return {
                    'text': texts,
                    'label': bias_labels
                }
            
            processed_dataset = dataset['train'].map(
                preprocess_function,
                remove_columns=dataset['train'].column_names
            )
            
            # 토크나이저 적용
            tokenizer = model_loader.get_tokenizer("microsoft/DialoGPT-medium")
            if tokenizer is None:
                raise ValueError("토크나이저를 찾을 수 없습니다.")
            
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    padding='max_length',
                    max_length=256,
                    return_tensors='pt'
                )
            
            tokenized_dataset = processed_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=processed_dataset.column_names
            )
            
            # 데이터셋 분할
            train_dataset, val_dataset, test_dataset = self._split_dataset(tokenized_dataset)
            
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            self.logger.error(f"편향 감지 데이터셋 준비 실패: {e}")
            raise
    
    def train_bias_detection_model(self, data_path: str, model_name: str = "microsoft/DialoGPT-medium"):
        """편향 감지 모델 학습"""
        try:
            self.logger.info("편향 감지 모델 학습 시작")
            
            # 데이터셋 준비
            train_dataset, val_dataset, test_dataset = self.prepare_bias_dataset(data_path)
            
            # 모델 로드
            model = model_loader.load_bias_detection_model(model_name)
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(
                tokenizer=model_loader.get_tokenizer(model_name),
                padding=True,
                return_tensors='pt'
            )
            
            # 학습 인수 설정
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "bias_detection_model"),
                num_train_epochs=5,
                per_device_train_batch_size=settings.TRAINING_BATCH_SIZE,
                per_device_eval_batch_size=settings.INFERENCE_BATCH_SIZE,
                gradient_accumulation_steps=settings.GRADIENT_ACCUMULATION_STEPS,
                learning_rate=1e-4,
                weight_decay=0.01,
                warmup_steps=300,
                logging_steps=100,
                evaluation_strategy=IntervalStrategy.STEPS,
                eval_steps=500,
                save_steps=1000,
                save_total_limit=3,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=settings.MIXED_PRECISION,
                dataloader_pin_memory=False,
                remove_unused_columns=True,
                group_by_length=True,
                report_to="tensorboard" if settings.ENABLE_TENSORBOARD else None,
                run_name="bias_detection_training",
                # 추가 최적화 설정
                gradient_checkpointing=True,
                optim="adamw_torch",
                lr_scheduler_type="linear",
                warmup_ratio=0.1,
                logging_dir=str(self.output_dir / "bias_detection_model" / "logs")
            )
            
            # 메트릭 계산 함수
            def compute_metrics(eval_pred):
                predictions, labels = eval_pred
                predictions = np.argmax(predictions, axis=1)
                
                precision, recall, f1, _ = precision_recall_fscore_support(
                    labels, predictions, average='binary'
                )
                acc = accuracy_score(labels, predictions)
                
                return {
                    'accuracy': acc,
                    'f1': f1,
                    'precision': precision,
                    'recall': recall
                }
            
            # 트레이너 초기화
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # 학습 실행
            trainer.train()
            
            # 모델 저장
            trainer.save_model()
            
            # 테스트셋으로 평가
            test_results = self.evaluate_model(trainer, test_dataset)
            
            # 학습 통계 업데이트
            self.training_stats['models_trained'].append({
                'name': 'bias_detection_model',
                'test_results': test_results,
                'model_path': str(self.output_dir / "bias_detection_model")
            })
            
            self.logger.info("편향 감지 모델 학습 완료")
            
            return trainer
            
        except Exception as e:
            self.logger.error(f"편향 감지 모델 학습 실패: {e}")
            raise
    
    def prepare_credibility_dataset(self, data_path: str) -> Tuple[Dataset, Dataset, Dataset]:
        """신뢰도 분석 데이터셋 준비"""
        try:
            if not self._validate_data(data_path):
                raise ValueError("데이터 검증 실패")
            
            # 데이터 로드
            if data_path.endswith('.json'):
                dataset = load_dataset('json', data_files=data_path)
            elif data_path.endswith('.csv'):
                dataset = load_dataset('csv', data_files=data_path)
            else:
                raise ValueError("지원하지 않는 데이터 형식입니다.")
            
            # 데이터 전처리
            def preprocess_function(examples):
                texts = [str(text).strip() for text in examples['text']]
                
                # 신뢰도 라벨 (0: 신뢰할 수 없음, 1: 부분적으로 신뢰, 2: 신뢰할 수 있음)
                credibility_mapping = {
                    'unreliable': 0, 'partially_reliable': 1, 'reliable': 2
                }
                labels = [credibility_mapping.get(label, 1) for label in examples['credibility_label']]
                
                return {
                    'text': texts,
                    'label': labels
                }
            
            # 데이터셋 전처리
            processed_dataset = dataset['train'].map(
                preprocess_function,
                remove_columns=dataset['train'].column_names
            )
            
            # 토크나이저 적용
            tokenizer = model_loader.get_tokenizer("klue/roberta-large")
            if tokenizer is None:
                raise ValueError("토크나이저를 찾을 수 없습니다.")
            
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    padding='max_length',
                    max_length=512,
                    return_tensors='pt'
                )
            
            tokenized_dataset = processed_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=processed_dataset.column_names
            )
            
            # 데이터셋 분할
            train_dataset, val_dataset, test_dataset = self._split_dataset(tokenized_dataset)
            
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            self.logger.error(f"신뢰도 분석 데이터셋 준비 실패: {e}")
            raise
    
    def train_credibility_model(self, data_path: str, model_name: str = "klue/roberta-large"):
        """신뢰도 분석 모델 학습"""
        try:
            self.logger.info("신뢰도 분석 모델 학습 시작")
            
            # 데이터셋 준비
            train_dataset, val_dataset, test_dataset = self.prepare_credibility_dataset(data_path)
            
            # 모델 로드
            model = model_loader.load_credibility_model(model_name)
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(
                tokenizer=model_loader.get_tokenizer(model_name),
                padding=True,
                return_tensors='pt'
            )
            
            # 학습 인수 설정
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "credibility_model"),
                num_train_epochs=4,
                per_device_train_batch_size=settings.TRAINING_BATCH_SIZE,
                per_device_eval_batch_size=settings.INFERENCE_BATCH_SIZE,
                gradient_accumulation_steps=settings.GRADIENT_ACCUMULATION_STEPS,
                learning_rate=1e-5,
                weight_decay=0.01,
                warmup_steps=400,
                logging_steps=100,
                evaluation_strategy=IntervalStrategy.STEPS,
                eval_steps=500,
                save_steps=1000,
                save_total_limit=3,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=settings.MIXED_PRECISION,
                dataloader_pin_memory=False,
                remove_unused_columns=True,
                group_by_length=True,
                report_to="tensorboard" if settings.ENABLE_TENSORBOARD else None,
                run_name="credibility_training",
                # 추가 최적화 설정
                gradient_checkpointing=True,
                optim="adamw_torch",
                lr_scheduler_type="linear",
                warmup_ratio=0.1,
                logging_dir=str(self.output_dir / "credibility_model" / "logs")
            )
            
            # 메트릭 계산 함수
            def compute_metrics(eval_pred):
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
            
            # 트레이너 초기화
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # 학습 실행
            trainer.train()
            
            # 모델 저장
            trainer.save_model()
            
            # 테스트셋으로 평가
            test_results = self.evaluate_model(trainer, test_dataset)
            
            # 학습 통계 업데이트
            self.training_stats['models_trained'].append({
                'name': 'credibility_model',
                'test_results': test_results,
                'model_path': str(self.output_dir / "credibility_model")
            })
            
            self.logger.info("신뢰도 분석 모델 학습 완료")
            
            return trainer
            
        except Exception as e:
            self.logger.error(f"신뢰도 분석 모델 학습 실패: {e}")
            raise
    
    def prepare_content_classification_dataset(self, data_path: str) -> Tuple[Dataset, Dataset, Dataset]:
        """콘텐츠 분류 데이터셋 준비"""
        try:
            if not self._validate_data(data_path):
                raise ValueError("데이터 검증 실패")
            
            # 데이터 로드
            if data_path.endswith('.json'):
                dataset = load_dataset('json', data_files=data_path)
            elif data_path.endswith('.csv'):
                dataset = load_dataset('csv', data_files=data_path)
            else:
                raise ValueError("지원하지 않는 데이터 형식입니다.")
            
            # 데이터 전처리
            def preprocess_function(examples):
                texts = [str(text).strip() for text in examples['text']]
                
                # 콘텐츠 카테고리 라벨
                category_mapping = {
                    'news': 0, 'entertainment': 1, 'education': 2, 'technology': 3,
                    'politics': 4, 'sports': 5, 'health': 6, 'business': 7
                }
                labels = [category_mapping.get(label, 0) for label in examples['category_label']]
                
                return {
                    'text': texts,
                    'label': labels
                }
            
            # 데이터셋 전처리
            processed_dataset = dataset['train'].map(
                preprocess_function,
                remove_columns=dataset['train'].column_names
            )
            
            # 토크나이저 적용
            tokenizer = model_loader.get_tokenizer("klue/bert-base")
            if tokenizer is None:
                raise ValueError("토크나이저를 찾을 수 없습니다.")
            
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    padding='max_length',
                    max_length=256,
                    return_tensors='pt'
                )
            
            tokenized_dataset = processed_dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=processed_dataset.column_names
            )
            
            # 데이터셋 분할
            train_dataset, val_dataset, test_dataset = self._split_dataset(tokenized_dataset)
            
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            self.logger.error(f"콘텐츠 분류 데이터셋 준비 실패: {e}")
            raise
    
    def train_content_classification_model(self, data_path: str, model_name: str = "klue/bert-base"):
        """콘텐츠 분류 모델 학습"""
        try:
            self.logger.info("콘텐츠 분류 모델 학습 시작")
            
            # 데이터셋 준비
            train_dataset, val_dataset, test_dataset = self.prepare_content_classification_dataset(data_path)
            
            # 모델 로드
            model = model_loader.load_content_classification_model(model_name)
            
            # 데이터 콜레이터
            data_collator = DataCollatorWithPadding(
                tokenizer=model_loader.get_tokenizer(model_name),
                padding=True,
                return_tensors='pt'
            )
            
            # 학습 인수 설정
            training_args = TrainingArguments(
                output_dir=str(self.output_dir / "content_classification_model"),
                num_train_epochs=3,
                per_device_train_batch_size=settings.TRAINING_BATCH_SIZE,
                per_device_eval_batch_size=settings.INFERENCE_BATCH_SIZE,
                gradient_accumulation_steps=settings.GRADIENT_ACCUMULATION_STEPS,
                learning_rate=3e-5,
                weight_decay=0.01,
                warmup_steps=300,
                logging_steps=100,
                evaluation_strategy=IntervalStrategy.STEPS,
                eval_steps=500,
                save_steps=1000,
                save_total_limit=3,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=settings.MIXED_PRECISION,
                dataloader_pin_memory=False,
                remove_unused_columns=True,
                group_by_length=True,
                report_to="tensorboard" if settings.ENABLE_TENSORBOARD else None,
                run_name="content_classification_training",
                # 추가 최적화 설정
                gradient_checkpointing=True,
                optim="adamw_torch",
                lr_scheduler_type="linear",
                warmup_ratio=0.1,
                logging_dir=str(self.output_dir / "content_classification_model" / "logs")
            )
            
            # 메트릭 계산 함수
            def compute_metrics(eval_pred):
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
            
            # 트레이너 초기화
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                compute_metrics=compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # 학습 실행
            trainer.train()
            
            # 모델 저장
            trainer.save_model()
            
            # 테스트셋으로 평가
            test_results = self.evaluate_model(trainer, test_dataset)
            
            # 학습 통계 업데이트
            self.training_stats['models_trained'].append({
                'name': 'content_classification_model',
                'test_results': test_results,
                'model_path': str(self.output_dir / "content_classification_model")
            })
            
            self.logger.info("콘텐츠 분류 모델 학습 완료")
            
            return trainer
            
        except Exception as e:
            self.logger.error(f"콘텐츠 분류 모델 학습 실패: {e}")
            raise

    def evaluate_model(self, trainer: Trainer, test_dataset: Dataset):
        """모델 평가"""
        try:
            self.logger.info("모델 평가 시작")
            
            # 평가 실행
            results = trainer.evaluate(test_dataset)
            
            self.logger.info("모델 평가 결과:")
            for key, value in results.items():
                self.logger.info(f"{key}: {value:.4f}")
            
            # 상세 분류 리포트 생성
            predictions = trainer.predict(test_dataset)
            pred_labels = np.argmax(predictions.predictions, axis=1)
            true_labels = test_dataset['label']
            
            # 분류 리포트
            report = classification_report(true_labels, pred_labels, output_dict=True)
            self.logger.info("상세 분류 리포트:")
            self.logger.info(f"정확도: {report['accuracy']:.4f}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"모델 평가 실패: {e}")
            raise
    
    def save_training_summary(self):
        """학습 요약 저장"""
        try:
            summary = {
                'training_session': {
                    'start_time': self.training_stats['start_time'].isoformat() if self.training_stats['start_time'] else None,
                    'end_time': self.training_stats['end_time'].isoformat() if self.training_stats['end_time'] else None,
                    'duration_minutes': None
                },
                'models_trained': self.training_stats['models_trained'],
                'system_info': {
                    'device': str(self.device),
                    'cuda_available': torch.cuda.is_available(),
                    'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
                }
            }
            
            if self.training_stats['start_time'] and self.training_stats['end_time']:
                duration = (self.training_stats['end_time'] - self.training_stats['start_time']).total_seconds() / 60
                summary['training_session']['duration_minutes'] = round(duration, 2)
            
            # 요약 파일 저장
            summary_file = self.output_dir / f"training_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"학습 요약 저장 완료: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"학습 요약 저장 실패: {e}")
    
    def cleanup(self):
        """리소스 정리"""
        try:
            # 학습 통계 완료 시간 설정
            self.training_stats['end_time'] = datetime.now()
            
            # 학습 요약 저장
            self.save_training_summary()
            
            # 리소스 정리
            self.youtube_client.close()
            model_loader.cleanup()
            
            # GPU 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("리소스 정리 완료")
        except Exception as e:
            self.logger.error(f"리소스 정리 실패: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="AI 모델 학습 스크립트")
    parser.add_argument("--model", choices=["sentiment", "bias", "credibility", "content", "all"], 
                       default="all", help="학습할 모델 타입")
    parser.add_argument("--data-path", required=True, help="학습 데이터 경로")
    parser.add_argument("--output-dir", default="./training_outputs", 
                       help="출력 디렉토리")
    parser.add_argument("--validate-only", action="store_true", help="데이터 검증만 수행")
    
    args = parser.parse_args()
    
    trainer = ModelTrainer()
    
    try:
        # 학습 시작 시간 기록
        trainer.training_stats['start_time'] = datetime.now()
        
        if args.validate_only:
            # 데이터 검증만 수행
            if trainer._validate_data(args.data_path):
                trainer.logger.info("데이터 검증 성공")
            else:
                trainer.logger.error("데이터 검증 실패")
                sys.exit(1)
        else:
            # 모델 학습 수행
            if args.model in ["sentiment", "all"]:
                trainer.train_sentiment_model(args.data_path)
            
            if args.model in ["bias", "all"]:
                trainer.train_bias_detection_model(args.data_path)
            
            if args.model in ["credibility", "all"]:
                trainer.train_credibility_model(args.data_path)
            
            if args.model in ["content", "all"]:
                trainer.train_content_classification_model(args.data_path)
            
            trainer.logger.info("모든 모델 학습 완료")
        
    except Exception as e:
        trainer.logger.error(f"학습 실패: {e}")
        sys.exit(1)
    
    finally:
        trainer.cleanup()


if __name__ == "__main__":
    main()
