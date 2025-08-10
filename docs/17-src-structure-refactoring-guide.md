# SRC 구조 리팩토링 가이드

## 개요

Info-Guard 프로젝트의 src 폴더 구조를 리팩토링하여 각 서비스를 독립적으로 운영할 수 있도록 정리합니다. 이는 마이크로서비스 아키텍처의 원칙에 따라 각 서비스의 독립성과 확장성을 보장합니다.

## 현재 구조 분석

### 현재 src 폴더 구조
```
src/
├── ai-service/           # Python AI 서비스
├── chrome-extension/     # Chrome 확장 프로그램
├── nodejs-server/        # Node.js 백엔드 서버 (현재 혼재)
├── database/             # 데이터베이스 관련
├── prisma/               # Prisma 스키마
├── ai-models/            # AI 모델 파일들
├── venv/                 # Python 가상환경
├── node_modules/         # Node.js 의존성
├── server.js             # 메인 서버 파일
├── package.json          # Node.js 패키지 설정
├── requirements.txt      # Python 의존성
├── docker-compose.yml    # Docker 설정
└── Dockerfile            # Docker 이미지
```

### 문제점
1. **서비스 혼재**: Python, Node.js, Chrome Extension이 같은 레벨에 혼재
2. **의존성 충돌**: Python과 Node.js 의존성이 섞여 있음
3. **배포 복잡성**: 단일 폴더에서 여러 서비스를 관리하기 어려움
4. **개발 환경**: 각 서비스별 독립적인 개발 환경 구성 어려움

## 리팩토링 목표

### 1. 서비스 분리
- **python-server/**: AI 서비스 및 Python 백엔드
- **nodejs-server/**: Node.js 백엔드 API 서버
- **chrome-extension/**: Chrome 확장 프로그램
- **shared/**: 공통 유틸리티 및 설정

### 2. 독립적 운영
- 각 서비스별 독립적인 의존성 관리
- 개별 Docker 컨테이너화
- 독립적인 개발 환경 및 테스트
- 마이크로서비스 아키텍처 지원

### 3. 개발 효율성
- 명확한 서비스 경계
- 독립적인 CI/CD 파이프라인
- 서비스별 독립적인 배포

## 새로운 구조 설계

### 리팩토링 후 구조
```
src/
├── python-server/           # Python AI 서비스
│   ├── ai-service/         # AI 분석 서비스
│   ├── ml-models/          # ML 모델들
│   ├── data-processors/    # 데이터 전처리
│   ├── requirements.txt    # Python 의존성
│   ├── Dockerfile          # Python 서비스 Docker
│   └── README.md           # Python 서비스 문서
│
├── nodejs-server/           # Node.js 백엔드 서버
│   ├── api/                # API 엔드포인트
│   ├── services/           # 비즈니스 로직
│   ├── middleware/         # 미들웨어
│   ├── database/           # 데이터베이스 연결
│   ├── prisma/             # Prisma 스키마
│   ├── package.json        # Node.js 의존성
│   ├── Dockerfile          # Node.js 서비스 Docker
│   └── README.md           # Node.js 서비스 문서
│
├── chrome-extension/        # Chrome 확장 프로그램
│   ├── manifest.json       # 확장 프로그램 매니페스트
│   ├── background/         # 백그라운드 스크립트
│   ├── content/            # 콘텐츠 스크립트
│   ├── popup/              # 팝업 UI
│   ├── options/            # 옵션 페이지
│   ├── assets/             # 이미지 및 아이콘
│   └── README.md           # 확장 프로그램 문서
│
├── shared/                  # 공통 리소스
│   ├── config/             # 공통 설정
│   ├── utils/              # 공통 유틸리티
│   ├── types/              # 공통 타입 정의
│   └── constants/          # 상수 정의
│
├── docker/                  # Docker 관련 파일들
│   ├── docker-compose.yml  # 전체 서비스 오케스트레이션
│   ├── python-server/      # Python 서비스 Docker 설정
│   ├── nodejs-server/      # Node.js 서비스 Docker 설정
│   └── nginx/              # Nginx 설정
│
├── docs/                    # 프로젝트 문서
├── scripts/                 # 빌드 및 배포 스크립트
└── README.md                # 전체 프로젝트 개요
```

## 리팩토링 단계별 계획

### Phase 1: 서비스 분리 및 이동
1. **Python 서비스 분리**
   - `ai-service/` → `python-server/ai-service/`
   - `ai-models/` → `python-server/ml-models/`
   - Python 관련 파일들 이동

2. **Node.js 서버 분리**
   - `server.js`, `package.json` 등 → `nodejs-server/`
   - `routes/`, `services/`, `middleware/` → `nodejs-server/`
   - `database/`, `prisma/` → `nodejs-server/`

3. **Chrome Extension 정리**
   - `chrome-extension/` 폴더 정리 및 문서화

### Phase 2: 의존성 관리 정리
1. **Python 서비스**
   - 독립적인 `requirements.txt`
   - 독립적인 가상환경 설정
   - 독립적인 Docker 이미지

2. **Node.js 서비스**
   - 독립적인 `package.json`
   - 독립적인 `node_modules`
   - 독립적인 Docker 이미지

### Phase 3: Docker 컨테이너화
1. **개별 서비스 Dockerfile**
2. **docker-compose.yml 업데이트**
3. **서비스 간 통신 설정**

### Phase 4: 개발 환경 설정
1. **각 서비스별 독립적인 개발 환경**
2. **서비스별 테스트 환경**
3. **CI/CD 파이프라인 분리**

## 개발 원칙 (Prompts 참고)

### 1. TDD 접근법
- 테스트 우선 개발
- 각 서비스별 독립적인 테스트 스위트
- 통합 테스트 및 E2E 테스트

### 2. 문서 우선 개발
- 각 서비스별 README 작성
- API 문서화
- 아키텍처 문서 업데이트

### 3. 점진적 개발
- 작은 단위로 구현
- 각 단계별 검증
- 지속적인 리팩토링

### 4. 품질 우선
- 코드 품질 및 가독성
- 보안 및 성능 고려
- 에러 처리 및 로깅

## 마이그레이션 체크리스트

### Python 서비스
- [ ] AI 서비스 코드 이동
- [ ] ML 모델 파일 이동
- [ ] Python 의존성 정리
- [ ] 가상환경 설정
- [ ] Docker 이미지 생성
- [ ] 테스트 환경 구성

### Node.js 서버
- [ ] 서버 코드 이동
- [ ] API 엔드포인트 정리
- [ ] 데이터베이스 연결 설정
- [ ] 미들웨어 정리
- [ ] Docker 이미지 생성
- [ ] 테스트 환경 구성

### Chrome Extension
- [ ] 확장 프로그램 코드 정리
- [ ] 매니페스트 파일 업데이트
- [ ] 빌드 스크립트 작성
- [ ] 테스트 환경 구성

### 공통 인프라
- [ ] Docker Compose 설정 업데이트
- [ ] Nginx 설정 정리
- [ ] 환경 변수 관리
- [ ] 로깅 및 모니터링 설정

## 예상 효과

### 1. 개발 효율성 향상
- 명확한 서비스 경계
- 독립적인 개발 환경
- 빠른 빌드 및 테스트

### 2. 운영 안정성 향상
- 서비스별 독립적인 배포
- 장애 격리
- 확장성 향상

### 3. 유지보수성 향상
- 코드 구조 명확화
- 의존성 관리 단순화
- 문서화 개선

## 다음 단계

1. **현재 코드 백업**
2. **Phase 1 실행**: 서비스 분리 및 이동
3. **Phase 2 실행**: 의존성 관리 정리
4. **Phase 3 실행**: Docker 컨테이너화
5. **Phase 4 실행**: 개발 환경 설정
6. **테스트 및 검증**
7. **문서 업데이트**

이 리팩토링을 통해 Info-Guard 프로젝트는 더욱 견고하고 확장 가능한 마이크로서비스 아키텍처를 갖게 됩니다.
