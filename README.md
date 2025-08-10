# Info-Guard 소스 코드

Info-Guard는 YouTube 영상의 신뢰도를 AI 기반으로 분석하는 플랫폼입니다.

## 프로젝트 구조

```
src/
├── python-server/          # AI 분석 서버 (Python/FastAPI)
│   ├── ai_models/         # AI 모델 및 분석 로직
│   ├── data_processing/   # 데이터 처리 및 YouTube API 연동
│   ├── api/               # FastAPI 라우터 및 엔드포인트
│   ├── utils/             # 유틸리티 함수
│   └── tests/             # 테스트 코드
│
├── nodejs-server/          # 백엔드 API 서버 (Node.js/Express)
│   ├── api/               # API 라우터
│   ├── services/          # 비즈니스 로직
│   ├── models/            # 데이터 모델
│   ├── middleware/        # 미들웨어
│   ├── utils/             # 유틸리티 함수
│   └── tests/             # 테스트 코드
│
├── chrome-extension/       # Chrome 확장 프로그램
│   ├── popup/             # 팝업 UI
│   ├── content/            # YouTube 페이지 통합
│   ├── background/         # 백그라운드 스크립트
│   ├── options/            # 설정 페이지
│   ├── assets/             # 아이콘 및 이미지
│   └── utils/              # 유틸리티 함수
│
├── docker/                 # Docker 설정
│   ├── python/            # Python 서버 Dockerfile
│   ├── nodejs/            # Node.js 서버 Dockerfile
│   └── nginx/             # Nginx 설정
│
└── shared/                 # 공통 코드
    ├── types/              # TypeScript 타입 정의
    ├── constants/          # 상수 정의
    └── utils/              # 공통 유틸리티
```

## 주요 기능

### 1. AI 기반 신뢰도 분석
- **감정 분석**: 영상 내용의 감정적 편향성 감지
- **편향 감지**: 정치적, 경제적, 문화적 편향성 분석
- **팩트체크**: 주장의 사실 여부 검증
- **출처 검증**: 정보 출처의 신뢰성 평가

### 2. 콘텐츠 분류
- 정치, 경제, 사회, 투자, 시사 등 카테고리별 자동 분류
- 오락, 일상 콘텐츠는 분석 대상에서 제외

### 3. 실시간 분석
- YouTube 페이지에서 즉시 신뢰도 점수 표시
- WebSocket을 통한 실시간 분석 진행 상황 업데이트

### 4. 사용자 피드백
- 분석 결과에 대한 사용자 피드백 수집
- AI 모델 성능 개선을 위한 데이터 축적

## 기술 스택

### Python AI 서버
- **프레임워크**: FastAPI
- **AI/ML**: PyTorch, Transformers, scikit-learn
- **자연어처리**: NLTK, spaCy, VADER
- **데이터베이스**: PostgreSQL, Redis

### Node.js 백엔드
- **프레임워크**: Express.js
- **데이터베이스**: Prisma ORM, PostgreSQL
- **캐싱**: Redis
- **실시간 통신**: Socket.IO

### Chrome Extension
- **Manifest**: V3
- **프론트엔드**: HTML5, CSS3, JavaScript (ES6+)
- **스타일링**: Tailwind CSS
- **상태 관리**: Chrome Storage API

### 인프라
- **컨테이너화**: Docker, Docker Compose
- **웹 서버**: Nginx (리버스 프록시)
- **데이터베이스**: PostgreSQL 15, Redis 7

## 시작하기

### 1. 환경 설정
```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 설정값 입력
```

### 2. Docker로 실행
```bash
cd src/docker
docker-compose up -d
```

### 3. 개별 서비스 실행

#### Python AI 서버
```bash
cd src/python-server
pip install -r requirements.txt
python main.py
```

#### Node.js 백엔드
```bash
cd src/nodejs-server
npm install
npm run dev
```

#### Chrome Extension
1. Chrome에서 `chrome://extensions/` 접속
2. "개발자 모드" 활성화
3. "압축해제된 확장 프로그램을 로드합니다" 클릭
4. `src/chrome-extension` 폴더 선택

## API 문서

### Python AI 서버
- **URL**: http://localhost:8000
- **문서**: http://localhost:8000/docs (Swagger UI)

### Node.js 백엔드
- **URL**: http://localhost:3000
- **문서**: http://localhost:3000/api-docs

## 개발 가이드

### 코드 스타일
- Python: PEP 8 준수
- JavaScript: ESLint + Prettier
- TypeScript: strict 모드 사용

### 테스트
```bash
# Python 테스트
cd src/python-server
pytest

# Node.js 테스트
cd src/nodejs-server
npm test
```

### 배포
```bash
# 프로덕션 빌드
cd src/docker
docker-compose -f docker-compose.prod.yml up -d
```

## 라이선스

MIT License

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.
