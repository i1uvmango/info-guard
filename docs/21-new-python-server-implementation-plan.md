# 새로운 Python 서버 구현 계획

## 🎯 **프로젝트 개요**
Info-Guard Python 서버를 처음부터 새롭게 구현하여 YouTube 영상 신뢰도 분석을 위한 AI 기반 백엔드 서비스를 구축합니다.

## 🏗️ **새로운 아키텍처 설계**

### 1.1 핵심 원칙
- **단순하고 명확한 구조**: 복잡한 의존성 제거
- **모듈화된 설계**: 각 기능을 독립적인 모듈로 분리
- **점진적 구현**: 핵심 기능부터 단계별 구현
- **테스트 주도 개발**: 각 단계마다 테스트 코드 작성

### 1.2 새로운 디렉토리 구조
```
src/python-server/
├── main.py                    # 메인 서버 진입점
├── app/                       # 애플리케이션 핵심
│   ├── __init__.py
│   ├── core/                  # 핵심 설정 및 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py          # 설정 관리
│   │   ├── logging.py         # 로깅 시스템
│   │   └── exceptions.py      # 커스텀 예외 클래스
│   ├── api/                   # API 레이어
│   │   ├── __init__.py
│   │   ├── deps.py            # 의존성 주입
│   │   ├── middleware.py      # 미들웨어
│   │   └── v1/                # API 버전 1
│   │       ├── __init__.py
│   │       ├── health.py      # 헬스체크
│   │       ├── analysis.py    # 분석 API
│   │       └── websocket.py   # WebSocket
│   ├── models/                # 데이터 모델
│   │   ├── __init__.py
│   │   ├── analysis.py        # 분석 관련 모델
│   │   ├── youtube.py         # YouTube 관련 모델
│   │   └── common.py          # 공통 모델
│   ├── services/              # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── analysis.py        # 분석 서비스
│   │   ├── youtube.py         # YouTube 서비스
│   │   ├── ai_models.py       # AI 모델 서비스
│   │   └── cache.py           # 캐시 서비스
│   ├── ai/                    # AI 모델
│   │   ├── __init__.py
│   │   ├── base.py            # 기본 모델 클래스
│   │   ├── sentiment.py       # 감정 분석
│   │   ├── bias.py            # 편향 감지
│   │   ├── credibility.py     # 신뢰도 분석
│   │   └── classifier.py      # 콘텐츠 분류
│   └── utils/                 # 유틸리티
│       ├── __init__.py
│       ├── text.py            # 텍스트 처리
│       └── validators.py      # 검증 유틸리티
├── tests/                     # 테스트 코드
│   ├── __init__.py
│   ├── test_api/              # API 테스트
│   ├── test_services/         # 서비스 테스트
│   └── test_ai/               # AI 모델 테스트
├── requirements.txt            # 의존성 패키지
├── requirements-dev.txt        # 개발용 의존성
├── .env.example               # 환경 변수 예제
├── docker-compose.yml          # 개발용 Docker 설정
└── README.md                  # 프로젝트 문서
```

## 🚀 **구현 단계별 계획**

### **1단계: 기본 구조 및 설정 (1-2일)**
- [x] 프로젝트 디렉토리 구조 생성
- [x] 기본 설정 파일 작성 (config.py, logging.py)
- [x] 의존성 패키지 정의 (requirements.txt)
- [x] 메인 서버 파일 작성 (main.py)
- [x] 기본 예외 클래스 정의

### **2단계: 핵심 API 구현 (2-3일)**
- [x] FastAPI 애플리케이션 설정
- [x] 헬스체크 API 구현 (/health)
- [x] 기본 미들웨어 설정 (CORS, 로깅)
- [x] API 라우터 구조 설정
- [x] 기본 에러 핸들링

### **3단계: 데이터 모델 및 서비스 (2-3일)**
- [x] Pydantic 모델 정의
- [x] 분석 서비스 기본 구조
- [x] YouTube 서비스 기본 구조
- [x] AI 모델 서비스 기본 구조
- [x] 의존성 주입 시스템

### **4단계: AI 모델 통합 (3-4일)**
- [x] 기본 AI 모델 클래스 구현
- [x] 감정 분석 모델 통합
- [x] 편향 감지 모델 통합
- [x] 신뢰도 분석 모델 통합
- [x] 콘텐츠 분류 모델 통합

### **5단계: YouTube API 연동 (2-3일)**
- [x] YouTube API 클라이언트 구현
- [x] 영상 메타데이터 수집

## 🤖 **AI 모델 서비스 완성 가이드**

### 📊 **현재 구현 현황 (2024년 12월 기준)**

#### ✅ **완성된 AI 모델들**
1. **감정 분석 모델 (Sentiment Analysis)**
   - 파일: `app/ai/sentiment.py`
   - 상태: ✅ 완성 및 테스트 통과
   - 기능: 긍정/부정/중립 감정 분석, 감정 점수 계산
   - 테스트: `tests/test_ai/test_sentiment.py` ✅ 통과

2. **편향성 분석 모델 (Bias Detection)**
   - 파일: `app/ai/bias.py`
   - 상태: ✅ 완성 및 테스트 준비 완료
   - 기능: 정치적, 성별, 인종, 종교적 편향 감지
   - 테스트: `tests/test_ai/test_bias.py` (테스트 실행 시 오류 발생)

3. **신뢰도 분석 모델 (Credibility Analysis)**
   - 파일: `app/ai/credibility.py`
   - 상태: ✅ 완성 (테스트 미작성)
   - 기능: 텍스트 신뢰도 점수 계산, 신뢰도 지표 분석

4. **팩트 체커 모델 (Fact Checker)**
   - 파일: `app/ai/fact_checker.py`
   - 상태: ✅ 완성 (테스트 미작성)
   - 기능: 사실 확인, 주장 검증, 출처 분석

5. **콘텐츠 분류 모델 (Content Classifier)**
   - 파일: `app/ai/classifier.py`
   - 상태: ✅ 완성 (테스트 미작성)
   - 기능: 뉴스, 교육, 엔터테인먼트 등 콘텐츠 유형 분류

#### ✅ **완성된 서비스들**
1. **AI 모델 서비스 (`app/services/ai_models.py`)**
   - 상태: ✅ 완성
   - 기능: 모든 AI 모델 통합 관리, 분석 요청 처리

2. **분석 서비스 (`app/services/analysis.py`)**
   - 상태: ✅ 완성
   - 기능: 전체 분석 워크플로우 관리

3. **YouTube 서비스 (`app/services/youtube.py`)**
   - 상태: ✅ 완성
   - 기능: YouTube API 연동, 영상 데이터 수집

4. **배치 처리 서비스 (`app/services/batch_processor.py`)**
   - 상태: ✅ 완성
   - 기능: 대량 분석 작업 처리

5. **캐시 서비스 (`app/services/cache.py`)**
   - 상태: ✅ 완성
   - 기능: 분석 결과 캐싱

#### ✅ **완성된 API들**
1. **헬스체크 API (`/health`)**
   - 상태: ✅ 완성 및 테스트 통과
   - 파일: `app/api/v1/health.py`

2. **분석 API (`/analysis`)**
   - 상태: ✅ 완성 및 테스트 통과
   - 파일: `app/api/v1/analysis.py`

3. **WebSocket API**
   - 상태: ✅ 완성 (테스트 미작성)
   - 파일: `app/api/v1/websocket.py`

### ❌ **현재 발생하는 오류들**

#### 1. **편향성 분석 테스트 오류**
- **파일**: `tests/test_ai/test_bias.py`
- **오류**: `AttributeError: 'async_generator' object has no attribute 'name'`
- **원인**: pytest-asyncio fixture 사용 방식 문제
- **상태**: 수정 시도 중 (fixture 구조 변경 완료)

#### 2. **테스트 파일 누락**
- `tests/test_ai/test_credibility.py` - 빈 파일 (0바이트)
- `tests/test_ai/test_classifier.py` - 빈 파일 (0바이트)
- `tests/test_ai/test_fact_checker.py` - 파일 없음

### 🔧 **즉시 해결해야 할 작업들**

#### **우선순위 1: 편향성 분석 테스트 수정**
```bash
# 현재 디렉토리: src/python-server
python -m pytest tests/test_ai/test_bias.py -v
```
- **문제**: fixture에서 detector 객체가 제대로 yield되지 않음
- **해결방법**: pytest-asyncio 사용법 수정 또는 fixture 구조 변경

#### **우선순위 2: 누락된 테스트 파일 작성**
1. **신뢰도 분석 테스트** (`test_credibility.py`)
2. **팩트 체커 테스트** (`test_fact_checker.py`)
3. **콘텐츠 분류 테스트** (`test_classifier.py`)

### 📋 **남은 구현 작업들**

#### **Phase 1: 테스트 완성 (1-2일)**
- [ ] 편향성 분석 테스트 오류 수정
- [ ] 신뢰도 분석 테스트 작성
- [ ] 팩트 체커 테스트 작성
- [ ] 콘텐츠 분류 테스트 작성
- [ ] 전체 AI 모델 테스트 통과 확인

#### **Phase 2: 통합 테스트 (1-2일)**
- [ ] API 통합 테스트
- [ ] WebSocket 통신 테스트
- [ ] 전체 분석 워크플로우 테스트
- [ ] 성능 테스트

#### **Phase 3: 최적화 및 배포 (2-3일)**
- [ ] 메모리 사용량 최적화
- [ ] RTX 4060Ti GPU 최적화
- [ ] Docker 컨테이너화
- [ ] 환경별 설정 분리

### 🎯 **현재까지 달성한 성과**

1. **✅ 기본 아키텍처 완성**: 모든 핵심 모듈과 서비스 구현 완료
2. **✅ AI 모델 구현 완성**: 5개 AI 모델 모두 구현 완료
3. **✅ API 서비스 완성**: REST API 및 WebSocket 구현 완료
4. **✅ 서비스 레이어 완성**: 모든 비즈니스 로직 구현 완료
5. **✅ 기본 테스트 완성**: 감정 분석 모델 테스트 통과

### 📊 **전체 진행률**

- **구현 완성도**: 95% (19/20 모듈)
- **테스트 완성도**: 40% (2/5 AI 모델 테스트)
- **통합 테스트**: 0% (미시작)
- **배포 준비**: 0% (미시작)

### 🚨 **주의사항**

1. **테스트 오류 해결 필요**: 편향성 분석 테스트가 현재 실행되지 않음
2. **메모리 최적화 필요**: RTX 4060Ti 16GB 환경에서 안정적 동작 확인 필요
3. **성능 테스트 필요**: 실제 AI 모델 추론 성능 측정 필요

---

**현재 상황**: AI 모델 서비스는 거의 완성되었으나, 테스트 단계에서 일부 오류가 발생하고 있습니다. 다음 단계로 넘어가기 전에 테스트 오류를 해결하고 모든 AI 모델 테스트를 완성해야 합니다.**
