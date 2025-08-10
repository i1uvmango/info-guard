# Info-Guard Python AI Server

RTX 4060Ti 16GB에 최적화된 AI 기반 YouTube 영상 신뢰성 분석 서버입니다.

## 🚀 주요 기능

- **AI 기반 신뢰성 분석**: 감정 분석, 편향 감지, 사실 확인, 출처 검증
- **YouTube API 연동**: 영상 정보 및 자막 자동 수집
- **실시간 분석**: WebSocket을 통한 실시간 분석 결과 전송
- **CUDA 최적화**: RTX 4060Ti 16GB에 최적화된 GPU 가속
- **모델 학습**: 커스텀 데이터셋을 통한 모델 파인튜닝

## 🛠️ 시스템 요구사항

### 하드웨어
- **GPU**: NVIDIA RTX 4060Ti 16GB 이상
- **RAM**: 32GB 이상 권장
- **저장공간**: 50GB 이상 (모델 캐시 포함)

### 소프트웨어
- **OS**: Ubuntu 20.04+ / Windows 11 / macOS 13+
- **Python**: 3.9+ (3.11 권장)
- **CUDA**: 12.1+ (PyTorch 호환 버전)
- **cuDNN**: 8.9+ (CUDA 12.1 호환)

## 📦 설치 방법

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv info-guard-env
source info-guard-env/bin/activate  # Linux/macOS
# 또는
info-guard-env\Scripts\activate     # Windows

# Python 버전 확인 (3.9+ 필요)
python --version
```

### 2. CUDA 설치 확인

```bash
# CUDA 버전 확인
nvidia-smi
nvcc --version

# PyTorch CUDA 지원 확인
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

### 3. 의존성 설치

```bash
# 기본 의존성 설치
pip install -r requirements.txt

# 또는 단계별 설치 (권장)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets accelerate
pip install fastapi uvicorn
pip install google-api-python-client youtube-transcript-api
pip install scikit-learn numpy pandas
pip install sentence-transformers
```

### 4. 환경 변수 설정

```bash
# .env 파일 복사
cp env.example .env

# YouTube API 키 설정
echo "YOUTUBE_API_KEY=AIzaSyC8_h83XbrUYo-jJJGdgHzJbZLoVaKJcd4" >> .env

# CUDA 설정 (RTX 4060Ti 최적화)
echo "CUDA_VISIBLE_DEVICES=0" >> .env
echo "MAX_MEMORY_MB=14000" >> .env
echo "MIXED_PRECISION=true" >> .env
echo "GRADIENT_CHECKPOINTING=true" >> .env
```

## 🔧 설정 최적화

### CUDA 메모리 최적화

```python
# utils/config.py에서 설정 조정
MAX_MEMORY_MB = 14000        # 16GB - 2GB 여유
TRAINING_BATCH_SIZE = 4      # RTX 4060Ti에 최적화
INFERENCE_BATCH_SIZE = 8     # 추론 시 더 큰 배치
GRADIENT_ACCUMULATION_STEPS = 4  # 메모리 절약
```

### 모델 로딩 전략

```python
# 자동 디바이스 매핑 (권장)
DEVICE_MAP = "auto"
LOW_CPU_MEM_USAGE = True

# 또는 수동 설정
DEVICE_MAP = None  # 수동으로 GPU에 로드
```

## 🚀 실행 방법

### 1. 개발 모드 실행

```bash
# 서버 실행
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 프로덕션 모드 실행

```bash
# Gunicorn 사용 (Linux/macOS)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Windows
waitress-serve main:app --host=0.0.0.0 --port=8000
```

### 3. Docker 실행

```bash
# Docker Compose 사용
cd ../docker
docker-compose up python-server

# 또는 개별 실행
docker build -t info-guard-python .
docker run -p 8000:8000 --gpus all info-guard-python
```

## 🧠 AI 모델 학습

### 1. 데이터 준비

```bash
# 학습 데이터 형식
{
    "text": "분석할 텍스트",
    "label": "positive|neutral|negative"  # 감정 분석
    "bias_label": "biased|neutral"        # 편향 감지
}
```

### 2. 모델 학습 실행

```bash
# 감정 분석 모델 학습
python scripts/train_models.py --model sentiment --data-path ./data/sentiment_data.json

# 편향 감지 모델 학습
python scripts/train_models.py --model bias --data-path ./data/bias_data.json

# 모든 모델 학습
python scripts/train_models.py --model all --data-path ./data/
```

### 3. 학습 모니터링

```bash
# TensorBoard 실행
tensorboard --logdir ./training_outputs

# 메모리 사용량 확인
python -c "from ai_models.model_loader import model_loader; print(model_loader.get_memory_usage())"
```

## 📊 API 엔드포인트

### 기본 엔드포인트

- `GET /health`: 서버 상태 확인
- `POST /analysis`: 영상 신뢰성 분석
- `GET /analysis/{video_id}`: 분석 결과 조회
- `WebSocket /ws`: 실시간 분석 진행 상황

### 분석 요청 예시

```python
import requests

# 분석 요청
response = requests.post("http://localhost:8000/analysis", json={
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "analysis_type": "full",  # full, quick, custom
    "include_transcript": True,
    "include_comments": False
})

print(response.json())
```

## 🔍 문제 해결

### CUDA 메모리 부족

```bash
# 배치 크기 줄이기
echo "TRAINING_BATCH_SIZE=2" >> .env
echo "INFERENCE_BATCH_SIZE=4" >> .env

# 그래디언트 체크포인팅 활성화
echo "GRADIENT_CHECKPOINTING=true" >> .env

# 메모리 정리
python -c "import torch; torch.cuda.empty_cache()"
```

### 모델 로딩 실패

```bash
# 캐시 정리
rm -rf ./ai_models/cache/*

# 모델 재다운로드
python -c "from ai_models.model_loader import model_loader; model_loader.cleanup()"
```

### YouTube API 제한

```bash
# API 제한 설정 조정
echo "MAX_REQUESTS_PER_MINUTE=50" >> .env
echo "MAX_CONCURRENT_REQUESTS=5" >> .env
```

## 📈 성능 최적화

### RTX 4060Ti 특화 설정

```python
# utils/config.py
TORCH_CUDA_ARCH_LIST = "8.9"  # RTX 4060Ti 아키텍처
MAX_MEMORY_MB = 14000         # 16GB 최적화
MIXED_PRECISION = True         # FP16 사용
GRADIENT_CHECKPOINTING = True  # 메모리 절약
```

### 배치 처리 최적화

```python
# 학습 시
TRAINING_BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4

# 추론 시
INFERENCE_BATCH_SIZE = 8
```

## 🧪 테스트

### 단위 테스트

```bash
# 모든 테스트 실행
pytest

# 특정 모듈 테스트
pytest tests/test_credibility_analyzer.py

# 커버리지 포함
pytest --cov=src/python_server
```

### 통합 테스트

```bash
# API 테스트
python -m pytest tests/test_api.py

# 모델 테스트
python -m pytest tests/test_models.py
```

## 📚 추가 리소스

- [PyTorch CUDA 가이드](https://pytorch.org/docs/stable/notes/cuda.html)
- [Transformers 최적화](https://huggingface.co/docs/transformers/performance)
- [RTX 4060Ti 성능 가이드](https://www.nvidia.com/en-us/geforce/graphics-cards/rtx-4060-ti/)

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.
