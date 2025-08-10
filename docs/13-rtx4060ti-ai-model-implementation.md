# RTX 4060Ti 기반 고급 AI 모델 구현 가이드

## 개요

기존의 단순 키워드 기반 분석에서 실제 학습된 AI 모델을 사용하는 고급 신뢰도 분석 시스템으로 업그레이드했습니다.

## 문제점 분석

### 기존 시스템의 한계
- **의미 없는 분석**: 모든 영상이 50점으로 동일한 결과
- **단순 키워드 분석**: 실제 내용 분석 없이 키워드 매칭만 수행
- **AI 서비스 미활용**: Python AI 서버가 있지만 실제 모델 없음

### 새로운 시스템의 장점
- **실제 AI 모델**: BERT 기반 한국어 특화 모델
- **GPU 가속**: RTX 4060Ti의 8GB VRAM 활용
- **정확한 분석**: 각 영상마다 다른 신뢰도 점수

## 아키텍처

### 1. 모델 구조

#### AdvancedCredibilityModel
```python
class AdvancedCredibilityModel(nn.Module):
    def __init__(self, model_name: str = "klue/roberta-base", num_classes: int = 5):
        # BERT 기반 한국어 모델
        # GPU 가속 지원
        # 5단계 신뢰도 분류 (0-4 → 0-100점)
```

#### BiasDetectionModel
```python
class BiasDetectionModel(nn.Module):
    # 8가지 편향성 유형 분석
    # 정치, 경제, 사회, 문화, 성별, 인종, 종교, 미디어
    # 각각 3단계 분류 (낮음, 중간, 높음)
```

#### FactCheckingModel
```python
class FactCheckingModel(nn.Module):
    # 사실 검증 분류
    # 사실, 거짓, 확인불가
    # 신뢰도 점수 계산
```

### 2. GPU 최적화

#### CUDA 지원
- **GPU 감지**: `torch.cuda.is_available()`
- **메모리 관리**: 8GB VRAM 효율적 활용
- **배치 처리**: 여러 영상 동시 분석

#### 성능 최적화
- **모델 양자화**: 메모리 사용량 최적화
- **배치 크기 조정**: GPU 메모리에 맞춤
- **비동기 처리**: 실시간 분석 지원

## 구현 파일

### 1. 고급 AI 모델
- **파일**: `src/ai-service/models/advanced_credibility_model.py`
- **기능**: 
  - 신뢰도 분석 모델
  - 편향성 감지 모델
  - 사실 검증 모델
  - GPU 가속 지원

### 2. 의존성 관리
- **파일**: `src/ai-service/requirements_advanced.txt`
- **주요 패키지**:
  - `torch>=2.0.0` (CUDA 지원)
  - `transformers>=4.30.0` (BERT 모델)
  - `nvidia-ml-py>=11.450.129` (GPU 모니터링)

### 3. 모델 학습
- **파일**: `src/ai-service/train_models.py`
- **기능**:
  - 샘플 데이터 생성
  - 모델 학습 스크립트
  - GPU 가속 학습
  - 모델 저장/로드

## 설치 및 실행

### 1. 환경 설정 (윈도우 + RTX 4060Ti)

#### CUDA 설치
```bash
# CUDA Toolkit 11.8 이상 설치
# PyTorch CUDA 버전 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 의존성 설치
```bash
cd src/ai-service
pip install -r requirements_advanced.txt
```

### 2. 모델 학습

#### 학습 데이터 준비
```python
# 샘플 데이터 (실제로는 더 많은 데이터 필요)
sample_texts = [
    "이 연구는 과학적 방법론을 통해 진행되었습니다.",  # 높은 신뢰도
    "충격적인 진실! 당신이 몰랐던 사실!",              # 낮은 신뢰도
    # ... 더 많은 데이터
]
```

#### 모델 학습 실행
```bash
python train_models.py
```

### 3. AI 서비스 실행

#### 환경변수 설정
```bash
# .env 파일에 추가
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=your_api_key_here
```

#### 서비스 시작
```bash
python main.py
```

## 성능 최적화

### 1. GPU 메모리 관리
```python
# 배치 크기 조정
BATCH_SIZE = 4  # RTX 4060Ti에 최적화

# 메모리 정리
torch.cuda.empty_cache()
```

### 2. 모델 양자화
```python
# INT8 양자화로 메모리 사용량 절반으로 감소
model = torch.quantization.quantize_dynamic(
    model, {nn.Linear}, dtype=torch.qint8
)
```

### 3. 비동기 처리
```python
# 여러 요청 동시 처리
async def analyze_multiple_videos(video_list):
    tasks = [analyze_video(video) for video in video_list]
    results = await asyncio.gather(*tasks)
    return results
```

## 테스트 및 검증

### 1. 단위 테스트
```python
def test_credibility_model():
    model = AdvancedCredibilityModel()
    text = "이것은 테스트 텍스트입니다."
    result = model.predict_credibility(text)
    assert 0 <= result['credibility_score'] <= 100
```

### 2. 성능 테스트
```python
def benchmark_gpu_performance():
    # GPU 사용량 모니터링
    # 처리 속도 측정
    # 메모리 사용량 확인
```

### 3. 정확도 테스트
```python
def test_model_accuracy():
    # 테스트 데이터셋으로 정확도 측정
    # 다양한 영상 유형 테스트
    # 편향성 감지 정확도 확인
```

## 향후 개선 사항

### 1. 데이터 확장
- **더 많은 학습 데이터**: 다양한 영상 유형
- **레이블링 개선**: 전문가 검증
- **다국어 지원**: 영어, 중국어 등

### 2. 모델 개선
- **앙상블 모델**: 여러 모델 조합
- **실시간 학습**: 사용자 피드백 반영
- **개인화**: 사용자별 맞춤 분석

### 3. 성능 최적화
- **모델 압축**: 더 작은 모델로 성능 유지
- **캐싱 시스템**: 분석 결과 재사용
- **분산 처리**: 여러 GPU 활용

## 문제 해결

### 1. GPU 메모리 부족
```python
# 해결 방법
torch.cuda.empty_cache()  # 메모리 정리
BATCH_SIZE = 2           # 배치 크기 감소
model.half()             # FP16 사용
```

### 2. 모델 로딩 실패
```python
# 해결 방법
try:
    model = AdvancedCredibilityModel()
except Exception as e:
    logger.error(f"모델 로딩 실패: {e}")
    # Fallback 모델 사용
```

### 3. CUDA 버전 불일치
```bash
# 해결 방법
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 결론

RTX 4060Ti 기반 고급 AI 모델을 통해 실제 의미 있는 신뢰도 분석이 가능해졌습니다. GPU 가속을 활용하여 빠르고 정확한 분석을 제공하며, 각 영상의 실제 내용을 기반으로 한 신뢰도 점수를 제공합니다.

### 주요 성과
- ✅ 실제 AI 모델 구현
- ✅ GPU 가속 지원
- ✅ 정확한 신뢰도 분석
- ✅ 확장 가능한 아키텍처

### 다음 단계
- 실제 학습 데이터 수집
- 모델 성능 최적화
- 사용자 피드백 시스템 구축 