# Info-Guard Python Server

YouTube 영상 신뢰도 분석을 위한 AI 기반 백엔드 서비스입니다.

## 🚀 주요 기능

- **YouTube 영상 분석**: 감정 분석, 편향 감지, 신뢰도 분석, 콘텐츠 분류
- **실시간 진행상황**: WebSocket을 통한 분석 진행상황 실시간 모니터링
- **AI 모델 통합**: RTX 4060Ti GPU 최적화된 AI 모델 실행
- **RESTful API**: FastAPI 기반의 현대적이고 빠른 API
- **비동기 처리**: 백그라운드에서 분석 작업 처리

## 🏗️ 아키텍처

```
src/python-server/
├── main.py                    # 메인 서버 진입점
├── app/                       # 애플리케이션 핵심
│   ├── core/                  # 핵심 설정 및 유틸리티
│   ├── api/                   # API 레이어
│   ├── models/                # 데이터 모델
│   ├── services/              # 비즈니스 로직
│   ├── ai/                    # AI 모델
│   └── utils/                 # 유틸리티
├── tests/                     # 테스트 코드
├── test_services.py           # 서비스 테스트 스크립트
└── requirements.txt           # 의존성 패키지
```

## 🛠️ 기술 스택

- **Backend**: FastAPI, Uvicorn
- **AI/ML**: scikit-learn, transformers, PyTorch
- **데이터베이스**: PostgreSQL, Redis
- **비동기 처리**: asyncio, BackgroundTasks
- **실시간 통신**: WebSocket

## 📋 요구사항

- Python 3.11+
- RTX 4060Ti 16GB (GPU 가속)
- Docker & Docker Compose
- 8GB+ RAM
- 20GB+ 저장공간

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone <repository-url>
cd info-guard/src/python-server
```

### 2. 환경 변수 설정
```bash
cp env.example .env
# .env 파일을 편집하여 필요한 설정값 입력
```

### 3. Docker로 실행
```bash
docker-compose up -d
```

### 4. 로컬 개발 환경
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements-dev.txt

# 서버 실행
python main.py
```

## 🧪 서비스 테스트

서비스들이 제대로 작동하는지 확인하려면:

```bash
# 전체 서비스 테스트
python test_services.py

# 개별 테스트
python -m pytest tests/
```

테스트는 다음을 확인합니다:
- ✅ 캐시 서비스 (Redis 연결 및 기본 작업)
- ✅ AI 모델 서비스 (모델 상태 및 분석 기능)
- ✅ YouTube 서비스 (API 연결 및 기본 기능)

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔌 주요 API 엔드포인트

### 분석 API
- `POST /api/v1/analysis/analyze` - 영상 분석 요청
- `GET /api/v1/analysis/status/{id}` - 분석 상태 조회
- `GET /api/v1/analysis/result/{id}` - 분석 결과 조회
- `DELETE /api/v1/analysis/{id}` - 분석 취소

### WebSocket
- `WS /ws/analysis/{user_id}` - 실시간 분석 구독

### 헬스체크
- `GET /api/v1/health` - 기본 헬스체크
- `GET /api/v1/health/detailed` - 상세 헬스체크
- `GET /api/v1/health/ready` - 서비스 준비 상태

## 🧪 테스트

```bash
# 단위 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=app

# 특정 테스트 파일 실행
pytest tests/test_api/test_analysis.py
```

## 🔧 개발 도구

```bash
# 코드 포맷팅
black app/ tests/

# 코드 정렬
isort app/ tests/

# 린팅
flake8 app/ tests/

# 타입 체크
mypy app/
```

## 📊 모니터링

- **로그**: 구조화된 로깅 시스템
- **헬스체크**: 서비스 상태 모니터링
- **메트릭**: 성능 및 사용량 지표

## 🚀 배포

### Docker 이미지 빌드
```bash
docker build -t info-guard-python-server .
```

### 프로덕션 실행
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  info-guard-python-server
```

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🆘 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**Info-Guard Team** - AI 기반 콘텐츠 신뢰도 분석 서비스
