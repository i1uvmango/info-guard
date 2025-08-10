"""
콘텐츠 분류 모델 패키지

이 패키지는 유튜브 콘텐츠를 정치/경제/시사/기타로 분류하는 AI 모델을 포함합니다.
"""

from .classifier import ContentClassifier
from .preprocessor import ContentPreprocessor
from .trainer import ContentClassifierTrainer

__all__ = [
    'ContentClassifier',
    'ContentPreprocessor', 
    'ContentClassifierTrainer'
]

__version__ = '1.0.0'
