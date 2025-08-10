# Node.js Backend Server

Info-Guard 프로젝트의 Node.js 백엔드 서버입니다. YouTube API 통합, 사용자 인증, 데이터베이스 관리 등의 기능을 제공합니다.

## 구조

```
nodejs-server/
├── api/                  # API 엔드포인트
├── services/             # 비즈니스 로직
├── middleware/           # 미들웨어
├── database/             # 데이터베이스 연결
├── prisma/               # Prisma 스키마
├── controllers/          # 컨트롤러
├── models/               # 데이터 모델
├── utils/                # 유틸리티 함수
├── package.json          # Node.js 의존성
└── README.md            # 이 파일
```

## 주요 기능

- **YouTube API 통합**: YouTube 콘텐츠 정보 수집
- **사용자 인증**: JWT 기반 인증 시스템
- **데이터베이스 관리**: Prisma ORM을 통한 데이터 관리
- **API 게이트웨이**: 프론트엔드와 AI 서비스 간 중계
- **실시간 처리**: WebSocket을 통한 실시간 통신

## 설치 및 실행

### 1. 의존성 설치
```bash
cd src/nodejs-server
npm install
```

### 2. 환경 변수 설정
```bash
cp ../../env.example .env
# .env 파일을 편집하여 필요한 값들을 설정
```

### 3. 데이터베이스 마이그레이션
```bash
npx prisma migrate dev
npx prisma generate
```

### 4. 서버 실행
```bash
npm start
# 또는 개발 모드
npm run dev
```

## API 엔드포인트

### 인증
- `POST /auth/login`: 사용자 로그인
- `POST /auth/register`: 사용자 등록
- `POST /auth/refresh`: 토큰 갱신

### YouTube 분석
- `GET /youtube/video/:id`: 비디오 정보 조회
- `POST /youtube/analyze`: 콘텐츠 분석 요청
- `GET /youtube/history`: 분석 히스토리 조회

### 사용자 관리
- `GET /user/profile`: 사용자 프로필 조회
- `PUT /user/profile`: 사용자 프로필 수정
- `GET /user/analyses`: 사용자 분석 기록 조회

## 데이터베이스

- **ORM**: Prisma
- **데이터베이스**: PostgreSQL (개발), MySQL (운영)
- **마이그레이션**: `npx prisma migrate dev`

## 개발 환경

- **Node.js**: 16+
- **주요 라이브러리**:
  - Express.js
  - Prisma
  - JWT
  - WebSocket
  - YouTube API

## 테스트

```bash
npm test
# 또는 특정 테스트
npm test -- --grep "auth"
```

## Docker 실행

```bash
cd ../../docker
docker-compose up nodejs-server
```

## 모니터링

- 로그: `logs/server.log`
- 메트릭: `/metrics` 엔드포인트
- 헬스체크: `/health` 엔드포인트
