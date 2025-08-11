# Python 서버 리팩토링 계획

## 1. 현재 문제점 분석

### 1.1 모듈 경로 문제
- **문제**: `ModuleNotFoundError: No module named 'utils.config'`
- **원인**: Python 모듈 경로 설정 부족
- **영향**: 서버 시작 불가, import 에러

### 1.2 구조적 문제
- **의존성 순환**: `main.py` → `api.routers` → `utils.config`
- **경로 설정**: 하드코딩된 sys.path 설정
- **서비스 레이어**: 불완전한 구현

### 1.3 코드 품질 문제
- **에러 처리**: 부족한 예외 처리
- **로깅**: 일관성 없는 로깅
- **설정**: 분산된 설정 관리

## 2. 리팩토링 목표

### 2.1 단기 목표 (1-2일)
- [ ] 모듈 경로 문제 완전 해결
- [ ] 서버 정상 시작 및 실행
- [ ] 기본 API 엔드포인트 동작 확인

### 2.2 중기 목표 (3-5일)
- [ ] 서비스 레이어 완성
- [ ] 의존성 주입 시스템 정리
- [ ] 에러 처리 및 로깅 개선

### 2.3 장기 목표 (1주일)
- [ ] 코드 품질 향상
- [ ] 테스트 코드 작성
- [ ] 성능 최적화

## 3. 리팩토링 단계별 계획

### 3.1 1단계: 모듈 경로 문제 해결
**목표**: 서버가 정상적으로 시작되도록 함

#### 3.1.1 현재 상태 분석
```python
# main.py 현재 문제
sys.path.insert(0, current_dir)                    # src/python-server/
sys.path.insert(0, os.path.join(current_dir, 'utils'))  # src/python-server/utils/
sys.path.insert(0, os.path.join(current_dir, 'ai-service'))  # src/python-server/ai-service/
sys.path.insert(0, os.path.join(current_dir, 'ai-service', 'services'))  # src/python-server/ai-service/services/
```

#### 3.1.2 해결 방안
1. **절대 경로 사용**: 상대 경로 대신 절대 경로 활용
2. **패키지 구조 정리**: `__init__.py` 파일들 정리
3. **import 문 수정**: 명확한 import 경로 사용

#### 3.1.3 구현 계획
```python
# 개선된 main.py
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
PYTHON_SERVER_ROOT = Path(__file__).parent

# Python 경로에 추가
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PYTHON_SERVER_ROOT))
```

### 3.2 2단계: 서비스 레이어 구현
**목표**: 비즈니스 로직을 서비스 레이어로 분리

#### 3.2.1 서비스 구조 설계
```
services/
├── __init__.py
├── analysis_service.py      # 분석 서비스
├── youtube_service.py       # YouTube API 서비스
├── cache_service.py         # 캐시 서비스
├── model_service.py         # AI 모델 서비스
└── monitoring_service.py    # 모니터링 서비스
```

#### 3.2.2 의존성 주입 개선
```python
# dependencies.py 개선
from typing import Annotated
from fastapi import Depends

# 서비스 팩토리 패턴
class ServiceFactory:
    _instances = {}
    
    @classmethod
    def get_analysis_service(cls) -> AnalysisService:
        if 'analysis' not in cls._instances:
            cls._instances['analysis'] = AnalysisService()
        return cls._instances['analysis']

# 의존성 함수
def get_analysis_service() -> AnalysisService:
    return ServiceFactory.get_analysis_service()

# 라우터에서 사용
@router.post("/analyze")
async def analyze_video(
    request: AnalysisRequest,
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)]
):
    return await analysis_service.analyze(request)
```

### 3.3 3단계: 에러 처리 및 로깅 개선
**목표**: 일관된 에러 처리와 로깅 시스템 구축

#### 3.3.1 에러 처리 전략
```python
# exceptions.py
class InfoGuardException(Exception):
    """기본 예외 클래스"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AnalysisError(InfoGuardException):
    """분석 관련 에러"""
    pass

class ModelError(InfoGuardException):
    """AI 모델 관련 에러"""
    pass

class YouTubeAPIError(InfoGuardException):
    """YouTube API 관련 에러"""
    pass
```

#### 3.3.2 로깅 시스템 개선
```python
# logger.py 개선
import structlog
from typing import Any, Dict

def setup_logging():
    """구조화된 로깅 설정"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """구조화된 로거 반환"""
    return structlog.get_logger(name)
```

### 3.4 4단계: 설정 관리 개선
**목표**: 중앙화된 설정 관리 시스템 구축

#### 3.4.1 설정 파일 구조
```
config/
├── __init__.py
├── base.py          # 기본 설정
├── development.py   # 개발 환경 설정
├── production.py    # 프로덕션 환경 설정
└── test.py         # 테스트 환경 설정
```

#### 3.4.2 환경별 설정 분리
```python
# config/base.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class BaseConfig(BaseSettings):
    """기본 설정 클래스"""
    # 공통 설정
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# config/development.py
class DevelopmentConfig(BaseConfig):
    """개발 환경 설정"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "postgresql://localhost:5432/info_guard_dev"
```

## 4. 구현 우선순위

### 4.1 높은 우선순위 (즉시 해결)
1. **모듈 경로 문제**: 서버 시작 불가 해결
2. **기본 import 에러**: 필수 모듈 import 문제 해결
3. **서버 실행**: 최소한의 기능으로 서버 동작

### 4.2 중간 우선순위 (1-2일 내)
1. **서비스 레이어**: 비즈니스 로직 분리
2. **의존성 주입**: 깔끔한 의존성 관리
3. **에러 처리**: 기본적인 예외 처리

### 4.3 낮은 우선순위 (3-5일 내)
1. **로깅 시스템**: 구조화된 로깅
2. **설정 관리**: 환경별 설정 분리
3. **테스트 코드**: 기본 테스트 작성

## 5. 테스트 전략

### 5.1 단위 테스트
```python
# tests/test_analysis_service.py
import pytest
from unittest.mock import Mock, patch
from services.analysis_service import AnalysisService

class TestAnalysisService:
    @pytest.fixture
    def service(self):
        return AnalysisService()
    
    @pytest.mark.asyncio
    async def test_analyze_video_success(self, service):
        # 테스트 구현
        pass
```

### 5.2 통합 테스트
```python
# tests/test_api_integration.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 6. 성능 최적화 계획

### 6.1 메모리 최적화
- **모델 캐싱**: 자주 사용되는 모델 메모리에 유지
- **배치 처리**: 여러 요청을 묶어서 처리
- **메모리 모니터링**: 실시간 메모리 사용량 추적

### 6.2 응답 시간 최적화
- **비동기 처리**: I/O 작업 비동기화
- **캐싱 전략**: Redis를 활용한 결과 캐싱
- **연결 풀링**: 데이터베이스 연결 재사용

## 7. 배포 및 운영

### 7.1 개발 환경
- **로컬 실행**: `python main.py`
- **환경 변수**: `.env` 파일 사용
- **핫 리로드**: `uvicorn --reload`

### 7.2 프로덕션 환경
- **Docker 컨테이너**: 멀티 스테이지 빌드
- **환경 변수**: Kubernetes ConfigMap
- **로깅**: ELK 스택 연동

## 8. 모니터링 및 알림

### 8.1 헬스체크
- **서버 상태**: `/health/` 엔드포인트
- **AI 모델 상태**: `/health/status` 엔드포인트
- **데이터베이스 상태**: 연결 상태 확인

### 8.2 메트릭 수집
- **시스템 리소스**: CPU, 메모리, 디스크 사용량
- **API 성능**: 응답 시간, 처리량
- **AI 모델 성능**: 추론 시간, 정확도

## 9. 다음 단계

### 9.1 즉시 실행할 작업
1. 모듈 경로 문제 해결
2. 서버 정상 시작 확인
3. 기본 API 테스트

### 9.2 다음 세션 작업
1. 서비스 레이어 구현
2. 에러 처리 개선
3. 로깅 시스템 구축

이 계획에 따라 단계별로 리팩토링을 진행하겠습니다.
