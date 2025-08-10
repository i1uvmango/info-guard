# Info-Guard Backend

YouTube 영상 신뢰도 분석 백엔드 API 서버

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
npm install
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Database Configuration
DATABASE_URL="postgresql://postgres:password@localhost:5432/info_guard"

# Redis Configuration (선택사항)
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
PORT=3000
NODE_ENV=development

# API Keys
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_API_KEY=your_ai_service_api_key_here

# JWT Configuration
JWT_SECRET=info-guard-jwt-secret-key-2024
JWT_EXPIRES_IN=24h

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info
LOG_FILE=logs/app.log

# API Configuration
API_KEY=info-guard-api-key-2024
```

### 3. 서버 시작
```bash
npm start
```

## 📁 프로젝트 구조

```
src/
├── routes/           # API 라우터
│   ├── analysis.js   # 분석 API
│   ├── health.js     # 헬스체크
│   └── metrics.js    # 메트릭
├── services/         # 비즈니스 로직
│   ├── analysisService.js
│   ├── youtubeService.js
│   └── cacheService.js
├── middleware/       # 미들웨어
│   ├── auth.js
│   ├── errorHandler.js
│   ├── requestLogger.js
│   └── validateRequest.js
├── utils/           # 유틸리티
│   └── logger.js
└── server.js        # 메인 서버
```

## 🔧 주요 기능

### ✅ 구현 완료
- [x] Express.js 기반 REST API
- [x] WebSocket 실시간 통신
- [x] YouTube API 연동
- [x] Redis 캐싱 (메모리 fallback)
- [x] JWT 인증
- [x] 요청 검증 (Joi)
- [x] 로깅 시스템 (Winston)
- [x] 에러 핸들링
- [x] Rate Limiting
- [x] CORS 설정
- [x] 보안 헤더 (Helmet)

### ⚠️ 주의사항
- Redis 서버가 없어도 메모리 캐시로 작동합니다
- YouTube API 키가 없으면 일부 기능이 제한됩니다
- AI 서비스가 없으면 분석 기능이 제한됩니다

## 🛠️ 개발

### 개발 모드
```bash
npm run dev
```

### 테스트
```bash
npm test
```

### 린트
```bash
npm run lint
```

## 📊 API 엔드포인트

### 분석 API
- `POST /api/v1/analysis/analyze-video` - 비디오 분석
- `GET /api/v1/analysis/status/:videoId` - 분석 상태 확인
- `POST /api/v1/analysis/batch` - 배치 분석
- `POST /api/v1/analysis/feedback` - 피드백
- `GET /api/v1/analysis/history` - 분석 히스토리

### 시스템 API
- `GET /health` - 헬스체크
- `GET /metrics` - 메트릭

## 🔒 보안

- JWT 토큰 기반 인증
- API 키 인증
- Rate Limiting
- 입력 검증
- CORS 설정
- 보안 헤더

## 📝 로그

로그는 `logs/` 디렉토리에 저장됩니다:
- `error.log` - 에러 로그
- `combined.log` - 전체 로그

## 🐛 문제 해결

### Redis 연결 오류
Redis 서버가 실행되지 않아도 메모리 캐시로 작동합니다.

### YouTube API 오류
YouTube API 키를 설정하지 않으면 관련 기능이 제한됩니다.

### 포트 충돌
다른 포트를 사용하려면 `.env` 파일에서 `PORT`를 변경하세요. 