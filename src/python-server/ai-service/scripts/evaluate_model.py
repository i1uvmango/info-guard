#!/usr/bin/env python3
"""
콘텐츠 분류 모델 평가 스크립트

학습된 모델의 성능을 다양한 메트릭으로 평가합니다.
"""

import os
import json
import argparse
from pathlib import Path
import logging
from typing import Dict, List, Optional
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, 
    confusion_matrix, classification_report
)

# 프로젝트 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.content_classifier.classifier import ContentClassifier
from models.content_classifier.preprocessor import ContentPreprocessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentClassifierEvaluator:
    """콘텐츠 분류 모델 평가 클래스"""
    
    def __init__(self, model_path: str, device: Optional[str] = None):
        """
        Args:
            model_path: 학습된 모델 경로
            device: 사용할 디바이스
        """
        self.model_path = model_path
        self.device = device
        self.classifier = None
        self.preprocessor = ContentPreprocessor()
        
        # 카테고리 매핑
        self.category_names = {0: "정치", 1: "경제", 2: "시사", 3: "기타"}
        
        # 출력 디렉토리
        self.output_dir = Path('./evaluation_results')
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"모델 경로: {model_path}")
        logger.info(f"출력 디렉토리: {self.output_dir}")
    
    def load_model(self) -> bool:
        """학습된 모델을 로드합니다."""
        try:
            logger.info("모델 로드 중...")
            
            self.classifier = ContentClassifier(
                model_path=self.model_path,
                device=self.device,
                use_pretrained=False
            )
            
            if not self.classifier.is_loaded:
                logger.error("모델 로드 실패")
                return False
            
            logger.info("모델 로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def load_test_data(self, data_path: str) -> List[Dict]:
        """
        테스트 데이터를 로드합니다.
        
        Args:
            data_path: 테스트 데이터 파일 경로
            
        Returns:
            테스트 데이터 리스트
        """
        logger.info(f"테스트 데이터 로드 중: {data_path}")
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"테스트 데이터 로드 완료: {len(data)}개 샘플")
            return data
            
        except Exception as e:
            logger.error(f"테스트 데이터 로드 실패: {e}")
            raise
    
    def run_predictions(self, test_data: List[Dict]) -> List[Dict]:
        """
        테스트 데이터에 대해 예측을 실행합니다.
        
        Args:
            test_data: 테스트 데이터
            
        Returns:
            예측 결과 리스트
        """
        logger.info("예측 실행 중...")
        
        predictions = []
        
        for i, item in enumerate(test_data):
            try:
                # 예측 실행
                result = self.classifier.classify(
                    title=item['title'],
                    description=item.get('description', ''),
                    tags=item.get('tags', [])
                )
                
                # 결과 구성
                prediction = {
                    'true_label': item['category'],
                    'true_category': self.category_names.get(item['category'], 'Unknown'),
                    'predicted_label': result['prediction']['category_id'],
                    'predicted_category': result['prediction']['category_name'],
                    'confidence': result['prediction']['confidence'],
                    'probabilities': result['prediction'].get('probabilities', []),
                    'prediction_time': result['metadata'].get('prediction_time', 0),
                    'method': result['prediction'].get('method', 'unknown')
                }
                
                predictions.append(prediction)
                
                # 진행률 표시
                if (i + 1) % 100 == 0:
                    logger.info(f"예측 진행률: {i + 1}/{len(test_data)}")
                
            except Exception as e:
                logger.warning(f"항목 {i} 예측 실패: {e}")
                continue
        
        logger.info(f"예측 완료: {len(predictions)}개")
        return predictions
    
    def calculate_metrics(self, predictions: List[Dict]) -> Dict:
        """
        성능 메트릭을 계산합니다.
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            성능 메트릭
        """
        logger.info("성능 메트릭 계산 중...")
        
        # 실제 라벨과 예측 라벨 추출
        true_labels = [p['true_label'] for p in predictions]
        pred_labels = [p['predicted_label'] for p in predictions]
        
        # 기본 메트릭 계산
        accuracy = accuracy_score(true_labels, pred_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='weighted'
        )
        
        # 카테고리별 메트릭
        category_metrics = {}
        for category_id in range(4):
            category_name = self.category_names[category_id]
            
            # 해당 카테고리에 대한 이진 분류 메트릭
            binary_true = [1 if label == category_id else 0 for label in true_labels]
            binary_pred = [1 if label == category_id else 0 for label in pred_labels]
            
            cat_precision, cat_recall, cat_f1, _ = precision_recall_fscore_support(
                binary_true, binary_pred, average='binary'
            )
            
            category_metrics[category_name] = {
                'precision': cat_precision,
                'recall': cat_recall,
                'f1': cat_f1
            }
        
        # 혼동 행렬
        cm = confusion_matrix(true_labels, pred_labels)
        
        # 예측 시간 통계
        prediction_times = [p['prediction_time'] for p in predictions if p['prediction_time'] > 0]
        avg_prediction_time = np.mean(prediction_times) if prediction_times else 0
        
        # 신뢰도 통계
        confidences = [p['confidence'] for p in predictions]
        avg_confidence = np.mean(confidences)
        
        metrics = {
            'overall': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            },
            'category_metrics': category_metrics,
            'confusion_matrix': cm.tolist(),
            'performance': {
                'avg_prediction_time': avg_prediction_time,
                'avg_confidence': avg_confidence,
                'total_predictions': len(predictions)
            }
        }
        
        logger.info("성능 메트릭 계산 완료")
        return metrics
    
    def generate_classification_report(self, predictions: List[Dict]) -> str:
        """
        분류 보고서를 생성합니다.
        
        Args:
            predictions: 예측 결과 리스트
            
        Returns:
            분류 보고서 문자열
        """
        true_labels = [p['true_label'] for p in predictions]
        pred_labels = [p['predicted_label'] for p in predictions]
        
        report = classification_report(
            true_labels, pred_labels,
            target_names=list(self.category_names.values()),
            digits=4
        )
        
        return report
    
    def create_visualizations(self, metrics: Dict, predictions: List[Dict]):
        """
        시각화를 생성합니다.
        
        Args:
            metrics: 성능 메트릭
            predictions: 예측 결과
        """
        logger.info("시각화 생성 중...")
        
        try:
            # 1. 혼동 행렬 히트맵
            plt.figure(figsize=(10, 8))
            cm = np.array(metrics['confusion_matrix'])
            sns.heatmap(
                cm, 
                annot=True, 
                fmt='d',
                xticklabels=list(self.category_names.values()),
                yticklabels=list(self.category_names.values()),
                cmap='Blues'
            )
            plt.title('Confusion Matrix')
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
            plt.tight_layout()
            plt.savefig(self.output_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # 2. 카테고리별 성능 막대 그래프
            categories = list(metrics['category_metrics'].keys())
            f1_scores = [metrics['category_metrics'][cat]['f1'] for cat in categories]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(categories, f1_scores, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
            plt.title('Category-wise F1 Scores')
            plt.ylabel('F1 Score')
            plt.ylim(0, 1)
            
            # 막대 위에 값 표시
            for bar, score in zip(bars, f1_scores):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{score:.3f}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / 'category_f1_scores.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # 3. 신뢰도 분포 히스토그램
            confidences = [p['confidence'] for p in predictions]
            
            plt.figure(figsize=(10, 6))
            plt.hist(confidences, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Confidence Score Distribution')
            plt.xlabel('Confidence Score')
            plt.ylabel('Frequency')
            plt.axvline(np.mean(confidences), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(confidences):.3f}')
            plt.legend()
            plt.tight_layout()
            plt.savefig(self.output_dir / 'confidence_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("시각화 생성 완료")
            
        except Exception as e:
            logger.error(f"시각화 생성 실패: {e}")
    
    def save_results(self, metrics: Dict, predictions: List[Dict], classification_report: str):
        """평가 결과를 저장합니다."""
        try:
            # 전체 결과 저장
            results = {
                'metrics': metrics,
                'predictions': predictions,
                'classification_report': classification_report,
                'evaluation_info': {
                    'model_path': self.model_path,
                    'device': self.device,
                    'total_samples': len(predictions),
                    'evaluation_date': str(Path().cwd())
                }
            }
            
            results_file = self.output_dir / 'evaluation_results.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 메트릭 요약 저장
            summary_file = self.output_dir / 'metrics_summary.txt'
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=== 콘텐츠 분류 모델 평가 결과 ===\n\n")
                f.write(f"전체 정확도: {metrics['overall']['accuracy']:.4f}\n")
                f.write(f"전체 F1 점수: {metrics['overall']['f1']:.4f}\n")
                f.write(f"전체 정밀도: {metrics['overall']['precision']:.4f}\n")
                f.write(f"전체 재현율: {metrics['overall']['recall']:.4f}\n\n")
                
                f.write("카테고리별 성능:\n")
                for category, cat_metrics in metrics['category_metrics'].items():
                    f.write(f"  {category}: F1={cat_metrics['f1']:.4f}, "
                           f"Precision={cat_metrics['precision']:.4f}, "
                           f"Recall={cat_metrics['recall']:.4f}\n")
                
                f.write(f"\n평균 예측 시간: {metrics['performance']['avg_prediction_time']:.4f}초\n")
                f.write(f"평균 신뢰도: {metrics['performance']['avg_confidence']:.4f}\n")
                f.write(f"총 예측 수: {metrics['performance']['total_predictions']}\n")
            
            # 분류 보고서 저장
            report_file = self.output_dir / 'classification_report.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(classification_report)
            
            logger.info(f"평가 결과 저장 완료: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    def run_evaluation(self, test_data_path: str) -> bool:
        """
        전체 평가를 실행합니다.
        
        Args:
            test_data_path: 테스트 데이터 파일 경로
            
        Returns:
            평가 성공 여부
        """
        try:
            # 1. 모델 로드
            if not self.load_model():
                return False
            
            # 2. 테스트 데이터 로드
            test_data = self.load_test_data(test_data_path)
            
            # 3. 예측 실행
            predictions = self.run_predictions(test_data)
            
            if not predictions:
                logger.error("예측 결과가 없습니다.")
                return False
            
            # 4. 메트릭 계산
            metrics = self.calculate_metrics(predictions)
            
            # 5. 분류 보고서 생성
            classification_report = self.generate_classification_report(predictions)
            
            # 6. 시각화 생성
            self.create_visualizations(metrics, predictions)
            
            # 7. 결과 저장
            self.save_results(metrics, predictions, classification_report)
            
            # 8. 결과 출력
            self._print_summary(metrics)
            
            logger.info("평가 완료!")
            return True
            
        except Exception as e:
            logger.error(f"평가 실패: {e}")
            return False
    
    def _print_summary(self, metrics: Dict):
        """평가 결과 요약을 출력합니다."""
        print("\n" + "="*50)
        print("콘텐츠 분류 모델 평가 결과")
        print("="*50)
        print(f"전체 정확도: {metrics['overall']['accuracy']:.4f}")
        print(f"전체 F1 점수: {metrics['overall']['f1']:.4f}")
        print(f"전체 정밀도: {metrics['overall']['precision']:.4f}")
        print(f"전체 재현율: {metrics['overall']['recall']:.4f}")
        print()
        
        print("카테고리별 성능:")
        for category, cat_metrics in metrics['category_metrics'].items():
            print(f"  {category}: F1={cat_metrics['f1']:.4f}, "
                  f"Precision={cat_metrics['precision']:.4f}, "
                  f"Recall={cat_metrics['recall']:.4f}")
        print()
        
        print(f"평균 예측 시간: {metrics['performance']['avg_prediction_time']:.4f}초")
        print(f"평균 신뢰도: {metrics['performance']['avg_confidence']:.4f}")
        print(f"총 예측 수: {metrics['performance']['total_predictions']}")
        print("="*50)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='콘텐츠 분류 모델 평가')
    parser.add_argument('--model', required=True, help='학습된 모델 경로')
    parser.add_argument('--test-data', required=True, help='테스트 데이터 파일 경로')
    parser.add_argument('--device', help='사용할 디바이스 (cuda/cpu)')
    parser.add_argument('--output-dir', default='./evaluation_results', help='출력 디렉토리')
    
    args = parser.parse_args()
    
    # 평가기 생성 및 실행
    evaluator = ContentClassifierEvaluator(args.model, args.device)
    evaluator.output_dir = Path(args.output_dir)
    
    success = evaluator.run_evaluation(args.test_data)
    
    if success:
        logger.info("모델 평가가 성공적으로 완료되었습니다!")
        exit(0)
    else:
        logger.error("모델 평가에 실패했습니다.")
        exit(1)


if __name__ == "__main__":
    main()
