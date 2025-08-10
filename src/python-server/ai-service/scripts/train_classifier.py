#!/usr/bin/env python3
"""
콘텐츠 분류 모델 학습 스크립트

수집된 데이터를 사용하여 KoBERT 기반 콘텐츠 분류 모델을 학습시킵니다.
"""

import os
import json
import argparse
from pathlib import Path
import logging
from typing import Dict, List, Optional
import torch

# 프로젝트 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.content_classifier.trainer import ContentClassifierTrainer
from models.content_classifier.preprocessor import ContentPreprocessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentClassifierTrainingPipeline:
    """콘텐츠 분류 모델 학습 파이프라인"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 학습 설정
        """
        self.config = config
        self.trainer = None
        self.preprocessor = ContentPreprocessor()
        
        # 출력 디렉토리 설정
        self.output_dir = Path(config.get('output_dir', './content_classifier_model'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 디렉토리
        self.log_dir = self.output_dir / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        logger.info(f"출력 디렉토리: {self.output_dir}")
        logger.info(f"로그 디렉토리: {self.log_dir}")
    
    def load_training_data(self, data_path: str) -> List[Dict]:
        """
        학습 데이터를 로드합니다.
        
        Args:
            data_path: 데이터 파일 경로
            
        Returns:
            학습 데이터 리스트
        """
        logger.info(f"학습 데이터 로드 중: {data_path}")
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"데이터 로드 완료: {len(data)}개 샘플")
            
            # 데이터 검증
            validated_data = self._validate_data(data)
            logger.info(f"검증된 데이터: {len(validated_data)}개 샘플")
            
            return validated_data
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise
    
    def _validate_data(self, data: List[Dict]) -> List[Dict]:
        """
        데이터 유효성을 검증합니다.
        
        Args:
            data: 원본 데이터
            
        Returns:
            검증된 데이터
        """
        validated_data = []
        
        for item in data:
            try:
                # 필수 필드 확인
                if not all(key in item for key in ['title', 'category']):
                    continue
                
                # 제목이 비어있지 않은지 확인
                if not item['title'] or not item['title'].strip():
                    continue
                
                # 카테고리가 유효한지 확인
                if not isinstance(item['category'], int) or item['category'] not in [0, 1, 2, 3]:
                    continue
                
                validated_data.append(item)
                
            except Exception as e:
                logger.warning(f"데이터 항목 검증 실패: {e}")
                continue
        
        return validated_data
    
    def setup_trainer(self) -> bool:
        """학습기를 설정합니다."""
        try:
            logger.info("학습기 설정 중...")
            
            # 학습기 생성
            self.trainer = ContentClassifierTrainer(
                model_name=self.config.get('model_name', 'skt/koBERT-base-v1'),
                device=self.config.get('device', None)
            )
            
            # 모델 설정
            if not self.trainer.setup_model():
                logger.error("모델 설정 실패")
                return False
            
            logger.info("학습기 설정 완료")
            return True
            
        except Exception as e:
            logger.error(f"학습기 설정 실패: {e}")
            return False
    
    def prepare_datasets(self, data: List[Dict]) -> tuple:
        """
        데이터셋을 준비합니다.
        
        Args:
            data: 학습 데이터
            
        Returns:
            (train_dataset, val_dataset, test_dataset)
        """
        logger.info("데이터셋 준비 중...")
        
        try:
            # 데이터 전처리 및 분할
            train_dataset, val_dataset, test_dataset = self.trainer.prepare_data(data)
            
            logger.info("데이터셋 준비 완료")
            return train_dataset, val_dataset, test_dataset
            
        except Exception as e:
            logger.error(f"데이터셋 준비 실패: {e}")
            raise
    
    def train_model(self, train_dataset, val_dataset) -> bool:
        """
        모델을 학습시킵니다.
        
        Args:
            train_dataset: 학습 데이터셋
            val_dataset: 검증 데이터셋
            
        Returns:
            학습 성공 여부
        """
        logger.info("모델 학습 시작...")
        
        try:
            # 학습 설정
            training_config = {
                'num_epochs': self.config.get('num_epochs', 3),
                'train_batch_size': self.config.get('train_batch_size', 16),
                'eval_batch_size': self.config.get('eval_batch_size', 16),
                'learning_rate': self.config.get('learning_rate', 2e-5),
                'warmup_steps': self.config.get('warmup_steps', 500),
                'weight_decay': self.config.get('weight_decay', 0.01),
                'gradient_accumulation_steps': self.config.get('gradient_accumulation_steps', 1),
                'fp16': self.config.get('fp16', torch.cuda.is_available()),
                'num_workers': self.config.get('num_workers', 2)
            }
            
            # 학습 실행
            success = self.trainer.train(
                train_dataset=train_dataset,
                val_dataset=val_dataset,
                output_dir=str(self.output_dir),
                **training_config
            )
            
            if success:
                logger.info("모델 학습 완료!")
                return True
            else:
                logger.error("모델 학습 실패")
                return False
                
        except Exception as e:
            logger.error(f"모델 학습 실패: {e}")
            return False
    
    def evaluate_model(self, test_dataset) -> Dict:
        """
        학습된 모델을 평가합니다.
        
        Args:
            test_dataset: 테스트 데이터셋
            
        Returns:
            평가 결과
        """
        logger.info("모델 평가 중...")
        
        try:
            evaluation_results = self.trainer.evaluate(test_dataset)
            
            logger.info("모델 평가 완료!")
            logger.info(f"정확도: {evaluation_results['accuracy']:.4f}")
            logger.info(f"F1 점수: {evaluation_results['f1']:.4f}")
            logger.info(f"정밀도: {evaluation_results['precision']:.4f}")
            logger.info(f"재현율: {evaluation_results['recall']:.4f}")
            
            # 평가 결과 저장
            eval_file = self.output_dir / 'evaluation_results.json'
            with open(eval_file, 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"평가 결과 저장: {eval_file}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"모델 평가 실패: {e}")
            raise
    
    def save_training_summary(self, training_data: List[Dict], evaluation_results: Dict):
        """학습 요약 정보를 저장합니다."""
        try:
            summary = {
                'training_config': self.config,
                'data_summary': {
                    'total_samples': len(training_data),
                    'categories': self._get_category_distribution(training_data)
                },
                'evaluation_results': evaluation_results,
                'model_info': self.trainer.get_training_summary() if self.trainer else {},
                'output_directory': str(self.output_dir)
            }
            
            summary_file = self.output_dir / 'training_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"학습 요약 저장: {summary_file}")
            
        except Exception as e:
            logger.error(f"학습 요약 저장 실패: {e}")
    
    def _get_category_distribution(self, data: List[Dict]) -> Dict[str, int]:
        """카테고리별 분포를 계산합니다."""
        distribution = {}
        category_names = {0: "정치", 1: "경제", 2: "시사", 3: "기타"}
        
        for item in data:
            category = item.get('category')
            if category in category_names:
                cat_name = category_names[category]
                distribution[cat_name] = distribution.get(cat_name, 0) + 1
        
        return distribution
    
    def run_training_pipeline(self, data_path: str) -> bool:
        """
        전체 학습 파이프라인을 실행합니다.
        
        Args:
            data_path: 학습 데이터 파일 경로
            
        Returns:
            학습 성공 여부
        """
        try:
            # 1. 데이터 로드
            training_data = self.load_training_data(data_path)
            
            # 2. 학습기 설정
            if not self.setup_trainer():
                return False
            
            # 3. 데이터셋 준비
            train_dataset, val_dataset, test_dataset = self.prepare_datasets(training_data)
            
            # 4. 모델 학습
            if not self.train_model(train_dataset, val_dataset):
                return False
            
            # 5. 모델 평가
            evaluation_results = self.evaluate_model(test_dataset)
            
            # 6. 학습 요약 저장
            self.save_training_summary(training_data, evaluation_results)
            
            logger.info("학습 파이프라인 완료!")
            return True
            
        except Exception as e:
            logger.error(f"학습 파이프라인 실패: {e}")
            return False


def load_config(config_path: str) -> Dict:
    """설정 파일을 로드합니다."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return {}


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='콘텐츠 분류 모델 학습')
    parser.add_argument('--data', required=True, help='학습 데이터 파일 경로')
    parser.add_argument('--config', help='설정 파일 경로')
    parser.add_argument('--output-dir', default='./content_classifier_model', help='출력 디렉토리')
    parser.add_argument('--epochs', type=int, default=3, help='학습 에포크 수')
    parser.add_argument('--batch-size', type=int, default=16, help='배치 크기')
    parser.add_argument('--learning-rate', type=float, default=2e-5, help='학습률')
    parser.add_argument('--device', help='사용할 디바이스 (cuda/cpu)')
    
    args = parser.parse_args()
    
    # 기본 설정
    config = {
        'output_dir': args.output_dir,
        'num_epochs': args.epochs,
        'train_batch_size': args.batch_size,
        'eval_batch_size': args.batch_size,
        'learning_rate': args.learning_rate,
        'device': args.device
    }
    
    # 설정 파일이 있으면 로드
    if args.config:
        file_config = load_config(args.config)
        config.update(file_config)
    
    # 학습 파이프라인 실행
    pipeline = ContentClassifierTrainingPipeline(config)
    success = pipeline.run_training_pipeline(args.data)
    
    if success:
        logger.info("모델 학습이 성공적으로 완료되었습니다!")
        exit(0)
    else:
        logger.error("모델 학습에 실패했습니다.")
        exit(1)


if __name__ == "__main__":
    main()
