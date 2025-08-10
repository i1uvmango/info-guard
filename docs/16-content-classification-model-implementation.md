# 1단계: 콘텐츠 분류 모델 구현

## 개요
Info-Guard 프로젝트의 첫 번째 단계로, 정치/경제/시사 vs 엔터테인먼트 콘텐츠를 분류하는 모델을 구축합니다.

## 요구사항 분석

### 기능 요구사항
- [ ] 유튜브 영상 제목, 설명, 태그를 입력받아 콘텐츠 카테고리 분류
- [ ] 4개 카테고리: 정치(25%), 경제(25%), 시사(25%), 기타(25%)
- [ ] 실시간 분류 (응답 시간 < 1초)
- [ ] 분류 정확도 85% 이상 달성

### 비기능 요구사항
- [ ] 한국어 특화 처리
- [ ] 확장 가능한 아키텍처
- [ ] 모델 성능 모니터링
- [ ] A/B 테스트 지원

## 기술 아키텍처

### 모델 선택: KoBERT
```python
# 모델 아키텍처
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class ContentClassifier:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("skt/koBERT-base-v1")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "skt/koBERT-base-v1", 
            num_labels=4
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
```

### 데이터 전처리 파이프라인
```python
class ContentPreprocessor:
    def __init__(self):
        self.stop_words = self._load_korean_stopwords()
        self.category_mapping = {
            0: "정치", 1: "경제", 2: "시사", 3: "기타"
        }
    
    def preprocess_text(self, title, description, tags):
        # 텍스트 정규화
        # 한국어 특수 표현 처리
        # 불용어 제거
        # 토큰화
        pass
```

## 데이터 수집 및 라벨링

### 데이터 소스
1. **유튜브 API를 통한 데이터 수집**
   - 제목, 설명, 태그, 카테고리
   - 최소 10,000개 샘플 목표
   - 균형잡힌 카테고리 분포

2. **전문가 라벨링**
   - 3명 이상의 전문가 교차 검증
   - 라벨링 가이드라인 문서화
   - 일관성 검증 프로세스

### 데이터 구조
```json
{
  "video_id": "string",
  "title": "string",
  "description": "string",
  "tags": ["string"],
  "category": "int (0-3)",
  "confidence": "float",
  "labeled_by": "string",
  "labeling_date": "datetime"
}
```

## 모델 학습 파이프라인

### 학습 데이터 분할
```python
# 데이터 분할 (70:15:15)
train_data, temp_data = train_test_split(data, test_size=0.3, random_state=42)
val_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)
```

### 학습 설정
```python
training_args = TrainingArguments(
    output_dir="./content_classifier",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    evaluation_strategy="steps",
    eval_steps=100,
    save_steps=500,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy"
)
```

### 성능 평가 지표
- **정확도 (Accuracy)**: 전체 분류 정확도
- **정밀도 (Precision)**: 각 카테고리별 정밀도
- **재현율 (Recall)**: 각 카테고리별 재현율
- **F1-Score**: 정밀도와 재현율의 조화평균

## 구현 단계

### Phase 1.1: 기본 인프라 구축 (1-2일)
- [ ] 프로젝트 구조 설정
- [ ] 의존성 설치 및 환경 구성
- [ ] 기본 클래스 구조 구현

### Phase 1.2: 데이터 수집 (3-5일)
- [ ] 유튜브 API 연동
- [ ] 데이터 수집 스크립트 구현
- [ ] 초기 데이터셋 구축 (1,000개)

### Phase 1.3: 모델 구현 (3-5일)
- [ ] KoBERT 모델 설정
- [ ] 데이터 전처리 파이프라인 구현
- [ ] 기본 학습 루프 구현

### Phase 1.4: 학습 및 최적화 (2-3일)
- [ ] 모델 학습 실행
- [ ] 성능 평가 및 분석
- [ ] 하이퍼파라미터 튜닝

### Phase 1.5: 테스트 및 배포 (2-3일)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 실행
- [ ] 모델 배포 및 모니터링

## 파일 구조

```
ai-service/
├── models/
│   ├── content_classifier/
│   │   ├── __init__.py
│   │   ├── classifier.py
│   │   ├── preprocessor.py
│   │   └── trainer.py
│   └── trained_models/
│       └── content_classifier_v1.pth
├── data/
│   ├── raw/
│   ├── processed/
│   └── labeled/
├── scripts/
│   ├── data_collection.py
│   ├── train_classifier.py
│   └── evaluate_model.py
└── tests/
    ├── test_classifier.py
    ├── test_preprocessor.py
    └── test_trainer.py
```

## 테스트 전략

### 단위 테스트
```python
def test_content_preprocessor():
    preprocessor = ContentPreprocessor()
    result = preprocessor.preprocess_text(
        title="테스트 제목",
        description="테스트 설명",
        tags=["테스트", "태그"]
    )
    assert isinstance(result, dict)
    assert "processed_text" in result
```

### 통합 테스트
```python
def test_end_to_end_classification():
    classifier = ContentClassifier()
    result = classifier.classify(
        title="정치 뉴스 제목",
        description="정치 관련 설명",
        tags=["정치", "뉴스"]
    )
    assert result["category"] == 0  # 정치
    assert result["confidence"] > 0.8
```

## 성능 모니터링

### 모델 성능 추적
- 정확도, 정밀도, 재현율 실시간 모니터링
- 예측 시간 측정
- 에러율 추적

### A/B 테스트 지원
- 여러 모델 버전 동시 운영
- 사용자 그룹별 성능 비교
- 점진적 롤아웃

## 다음 단계 준비

### 2단계 연계
- 감정 편향 분석을 위한 데이터 준비
- 콘텐츠 분류 결과를 감정 분석 입력으로 활용

### 확장성 고려
- 새로운 카테고리 추가 용이성
- 다국어 지원 확장 가능성
- 실시간 학습 지원

## 리스크 및 대응 방안

### 기술적 리스크
- **KoBERT 모델 크기**: 모델 압축 및 최적화
- **한국어 특수 표현**: 사전 구축 및 규칙 기반 보완
- **데이터 품질**: 다단계 검증 프로세스

### 운영 리스크
- **API 제한**: 요청 분산 및 캐싱
- **모델 성능 저하**: 지속적 모니터링 및 재학습
- **확장성 한계**: 마이크로서비스 아키텍처 고려
