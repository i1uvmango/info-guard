# AI 모델 학습 스크립트

이 디렉토리에는 Info-Guard 프로젝트의 AI 모델들을 학습하기 위한 스크립트들이 포함되어 있습니다.

## 파일 구성

- `train_models.py`: 메인 학습 스크립트
- `create_test_data.py`: 테스트 데이터 생성 스크립트
- `README.md`: 이 파일

## 주요 기능

### 1. 감정 분석 모델 (Sentiment Analysis)
- **모델**: KLUE BERT-base
- **라벨**: positive, neutral, negative
- **용도**: 텍스트의 감정 상태 분석

### 2. 편향 감지 모델 (Bias Detection)
- **모델**: Microsoft DialoGPT-medium
- **라벨**: neutral, biased
- **용도**: 텍스트의 편향성 감지

### 3. 신뢰도 분석 모델 (Credibility Analysis)
- **모델**: KLUE RoBERTa-large
- **라벨**: reliable, partially_reliable, unreliable
- **용도**: 정보의 신뢰도 평가

### 4. 콘텐츠 분류 모델 (Content Classification)
- **모델**: KLUE BERT-base
- **라벨**: news, entertainment, education, technology, politics, sports, health, business
- **용도**: 콘텐츠 카테고리 자동 분류

## 사용법

### 1. 테스트 데이터 생성

```bash
cd src/python-server/scripts
python create_test_data.py
```

이 명령어는 각 모델별로 테스트 데이터를 생성합니다:
- `test_sentiment_data.json/csv`
- `test_bias_data.json/csv`
- `test_credibility_data.json/csv`
- `test_content_classification_data.json/csv`

### 2. 모델 학습

#### 모든 모델 학습
```bash
python train_models.py --data-path test_sentiment_data.json --model all
```

#### 특정 모델만 학습
```bash
# 감정 분석 모델만
python train_models.py --data-path test_sentiment_data.json --model sentiment

# 편향 감지 모델만
python train_models.py --data-path test_bias_data.json --model bias

# 신뢰도 분석 모델만
python train_models.py --data-path test_credibility_data.json --model credibility

# 콘텐츠 분류 모델만
python train_models.py --data-path test_content_classification_data.json --model content
```

#### 데이터 검증만 수행
```bash
python train_models.py --data-path test_sentiment_data.json --validate-only
```

### 3. 명령행 옵션

- `--model`: 학습할 모델 타입 선택 (sentiment, bias, credibility, content, all)
- `--data-path`: 학습 데이터 파일 경로 (필수)
- `--output-dir`: 학습 결과 저장 디렉토리 (기본값: ./training_outputs)
- `--validate-only`: 데이터 검증만 수행

## 데이터 형식

### 감정 분석 데이터
```json
[
  {
    "text": "이 영상은 정말 유익하고 재미있어요!",
    "label": "positive"
  }
]
```

### 편향 감지 데이터
```json
[
  {
    "text": "이 영상은 객관적인 사실을 바탕으로 제작되었습니다.",
    "bias_label": "neutral"
  }
]
```

### 신뢰도 분석 데이터
```json
[
  {
    "text": "공식 통계에 따르면 2023년 경제 성장률은 2.6%입니다.",
    "credibility_label": "reliable"
  }
]
```

### 콘텐츠 분류 데이터
```json
[
  {
    "text": "오늘 주요 뉴스는 다음과 같습니다.",
    "category_label": "news"
  }
]
```

## 학습 설정

### RTX 4060Ti 최적화 설정
- **Mixed Precision**: FP16 활성화
- **Gradient Checkpointing**: 메모리 효율성 향상
- **Batch Size**: GPU 메모리에 맞게 자동 조정
- **Learning Rate**: 각 모델에 최적화된 값 사용

### 하이퍼파라미터
- **Epochs**: 3-5 (모델별로 다름)
- **Learning Rate**: 1e-5 ~ 3e-5
- **Warmup Steps**: 300-500
- **Weight Decay**: 0.01
- **Early Stopping**: 3 에포크 동안 개선 없으면 중단

## 출력 결과

### 학습된 모델
- `{output_dir}/{model_name}/`: 학습된 모델 파일들
- `{output_dir}/{model_name}/logs/`: TensorBoard 로그

### 학습 요약
- `{output_dir}/training_summary_{timestamp}.json`: 학습 세션 요약
- 학습 시간, 모델별 성능, 시스템 정보 등 포함

## 주의사항

1. **GPU 메모리**: RTX 4060Ti 16GB에 최적화되어 있습니다
2. **데이터 품질**: 충분한 양의 고품질 데이터가 필요합니다
3. **의존성**: requirements.txt의 모든 패키지가 설치되어야 합니다
4. **CUDA**: CUDA 12.1+ 버전이 필요합니다

## 문제 해결

### 일반적인 오류

1. **CUDA 메모리 부족**
   - 배치 크기 줄이기
   - gradient_accumulation_steps 증가
   - gradient_checkpointing 활성화

2. **데이터 형식 오류**
   - JSON/CSV 파일 형식 확인
   - 필수 컬럼 존재 여부 확인
   - 인코딩 확인 (UTF-8 권장)

3. **모델 로딩 실패**
   - 인터넷 연결 확인
   - Hugging Face 토큰 설정
   - 로컬 모델 경로 확인

## 추가 정보

더 자세한 정보는 다음 문서들을 참조하세요:
- [AI 서비스 구현 가이드](../docs/03-ai-service-implementation-guide.md)
- [AI 모델 학습 전략](../docs/15-ai-model-learning-strategy.md)
- [콘텐츠 분류 모델 구현](../docs/16-content-classification-model-implementation.md)
