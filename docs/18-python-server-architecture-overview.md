# Python 서버 아키텍처 개요

## 1. 서버 개요

### 1.1 서버 목적
- **Info-Guard AI 서버**: YouTube 영상 신뢰도 분석을 위한 AI 기반 백엔드 서비스
- **기술 스택**: FastAPI, Python 3.8+, Uvicorn, Pydantic
- **아키텍처**: 비동기 기반 마이크로서비스 아키텍처

### 1.2 핵심 기능
- YouTube 영상 분석 (감정, 편향, 신뢰도, 콘텐츠 분류)
- 실시간 WebSocket 통신
- AI 모델 관리 및 추론
- RESTful API 제공
- 배치 분석 처리

## 2. 서버 구조

### 2.1 디렉토리 구조
```
src/python-server/
├── main.py                 # 메인 서버 진입점
├── api/                    # API 레이어
│   ├── routers/           # 라우터 정의
│   │   ├── __init__.py    # 라우터 패키지
│   │   ├── health.py      # 헬스체크 API
│   │   ├── analysis.py    # 분석 API
│   │   └── websocket.py   # WebSocket API
│   └── dependencies.py    # 의존성 주입
├── ai_models/             # AI 모델 레이어
│   ├── model_manager.py   # 모델 관리자
│   ├── sentiment_analyzer.py
│   ├── bias_detector.py
│   ├── credibility_analyzer.py
│   └── content_classifier.py
├── ai-service/            # 고급 AI 서비스
│   └── services/         # 비즈니스 로직 서비스
├── utils/                 # 유틸리티
│   ├── config.py         # 설정 관리
│   ├── logger.py         # 로깅
│   └── security.py       # 보안
├── data_processing/       # 데이터 처리
├── database/              # 데이터베이스
└── tests/                 # 테스트
```

### 2.2 레이어 아키텍처
```
┌─────────────────────────────────────┐
│           API Layer                 │
│  (REST API + WebSocket)            │
├─────────────────────────────────────┤
│         Service Layer               │
│    (Business Logic)                 │
├─────────────────────────────────────┤
│         AI Model Layer              │
│    (ML Models + Inference)         │
├─────────────────────────────────────┤
│      Data Processing Layer          │
│    (YouTube API + Preprocessing)    │
├─────────────────────────────────────┤
│        Infrastructure Layer         │
│    (Config + Logging + Security)    │
└─────────────────────────────────────┘
```

## 3. 핵심 컴포넌트

### 3.1 FastAPI 애플리케이션
- **생명주기 관리**: `lifespan` 컨텍스트 매니저
- **미들웨어**: CORS, TrustedHost
- **라우터**: 모듈화된 API 엔드포인트

### 3.2 AI 모델 관리자
- **비동기 초기화**: 모든 AI 모델 병렬 로딩
- **상태 관리**: 모델 준비 상태 모니터링
- **메모리 최적화**: RTX 4060Ti 16GB 최적화

### 3.3 의존성 주입 시스템
- **서비스 인스턴스**: 싱글톤 패턴
- **의존성 함수**: FastAPI Depends 활용
- **모듈 경로 관리**: 동적 Python 경로 설정

## 4. 설정 및 환경

### 4.1 환경 변수
- **YouTube API**: API 키 관리
- **데이터베이스**: PostgreSQL, Redis 연결
- **AI 모델**: HuggingFace 토큰, 모델 캐시
- **CUDA 설정**: GPU 메모리 최적화

### 4.2 개발/프로덕션 설정
- **DEBUG 모드**: 개발 환경 설정
- **CORS**: 허용된 오리진 관리
- **TrustedHost**: 프로덕션 보안

## 5. 성능 최적화

### 5.1 메모리 관리
- **최대 메모리**: 14GB (16GB - 2GB 여유)
- **그라디언트 체크포인팅**: 메모리 절약
- **혼합 정밀도**: FP16 활용

### 5.2 병렬 처리
- **비동기 모델 로딩**: asyncio.gather
- **배치 처리**: 동시 분석 최대 3개
- **WebSocket**: 실시간 통신

## 6. 보안 및 모니터링

### 6.1 보안 기능
- **API 키 마스킹**: 로그에서 민감 정보 보호
- **호스트 검증**: TrustedHost 미들웨어
- **CORS 정책**: 허용된 도메인만 접근

### 6.2 모니터링
- **헬스체크**: 서버, AI 모델, DB 상태
- **메트릭 수집**: 시스템 리소스 모니터링
- **로깅**: 구조화된 로그 시스템

## 7. 확장성 및 유지보수

### 7.1 모듈화
- **라우터 분리**: 기능별 API 그룹
- **서비스 계층**: 비즈니스 로직 분리
- **의존성 주입**: 느슨한 결합

### 7.2 테스트 전략
- **단위 테스트**: 각 컴포넌트별 테스트
- **통합 테스트**: API 엔드포인트 테스트
- **성능 테스트**: AI 모델 추론 성능

## 8. 향후 개선 계획

### 8.1 단기 목표
- [ ] 모듈 경로 문제 해결
- [ ] 서비스 레이어 구현 완성
- [ ] 에러 처리 강화

### 8.2 장기 목표
- [ ] 마이크로서비스 분리
- [ ] 컨테이너화 (Docker)
- [ ] 쿠버네티스 배포
- [ ] 자동 스케일링
