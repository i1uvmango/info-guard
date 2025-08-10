# Info-Guard Database

Info-Guard 프로젝트의 데이터베이스 설정 및 관리 가이드입니다.

## 📋 목차

- [설치 및 설정](#설치-및-설정)
- [데이터베이스 구조](#데이터베이스-구조)
- [사용법](#사용법)
- [모니터링](#모니터링)
- [백업](#백업)

## 🚀 설치 및 설정

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

`env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요:

```bash
cp env.example .env
```

### 3. 데이터베이스 설정

#### PostgreSQL 설치 (macOS)
```bash
brew install postgresql
brew services start postgresql
```

#### Redis 설치 (macOS)
```bash
brew install redis
brew services start redis
```

### 4. 데이터베이스 생성

```bash
createdb info_guard
```

### 5. Prisma 설정

```bash
# Prisma 클라이언트 생성
npm run db:generate

# 데이터베이스 스키마 동기화
npm run db:push

# 마이그레이션 실행 (선택사항)
npm run db:migrate
```

### 6. 시드 데이터 삽입

```bash
npm run db:seed
```

## 🗄️ 데이터베이스 구조

### 주요 테이블

#### 1. analysis_results
YouTube 영상 분석 결과를 저장하는 테이블입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL | 기본 키 |
| video_id | VARCHAR(20) | YouTube 비디오 ID |
| video_url | TEXT | 비디오 URL |
| channel_id | VARCHAR(50) | 채널 ID |
| credibility_score | DECIMAL(5,2) | 신뢰도 점수 (0-100) |
| credibility_grade | VARCHAR(10) | 신뢰도 등급 (A-F) |
| bias_score | DECIMAL(5,2) | 편향 점수 |
| fact_check_score | DECIMAL(5,2) | 팩트 체크 점수 |
| source_score | DECIMAL(5,2) | 출처 신뢰도 점수 |
| sentiment_score | DECIMAL(5,2) | 감정 분석 점수 |

#### 2. user_feedback
사용자 피드백을 저장하는 테이블입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL | 기본 키 |
| analysis_result_id | BIGINT | 분석 결과 ID (외래 키) |
| user_id | VARCHAR(50) | 사용자 ID |
| feedback_type | VARCHAR(20) | 피드백 타입 |
| feedback_score | INTEGER | 피드백 점수 (1-5) |

#### 3. channels
채널 정보를 저장하는 테이블입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL | 기본 키 |
| channel_id | VARCHAR(50) | 채널 ID |
| channel_name | VARCHAR(200) | 채널명 |
| subscriber_count | INTEGER | 구독자 수 |
| average_credibility_score | DECIMAL(5,2) | 평균 신뢰도 점수 |

## 💻 사용법

### Repository 클래스 사용

```javascript
const AnalysisRepository = require('./database/repositories/analysisRepository');
const FeedbackRepository = require('./database/repositories/feedbackRepository');
const ChannelRepository = require('./database/repositories/channelRepository');

// 분석 결과 저장
const analysisData = {
    videoId: 'dQw4w9WgXcQ',
    videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    credibilityScore: 85.5,
    credibilityGrade: 'A',
    // ... 기타 필드들
};

const result = await AnalysisRepository.createAnalysisResult(analysisData);

// 최신 분석 결과 조회
const latestAnalysis = await AnalysisRepository.getLatestAnalysisByVideoId('dQw4w9WgXcQ');

// 사용자 피드백 저장
const feedbackData = {
    analysisResultId: 1,
    userId: 'user123',
    feedbackType: 'accurate',
    feedbackScore: 5
};

await FeedbackRepository.createFeedback(feedbackData);
```

### 데이터베이스 연결

```javascript
const db = require('./database/connection');

// 연결
await db.connect();

// 헬스 체크
const health = await db.healthCheck();
console.log(health); // { status: 'healthy', timestamp: ... }

// 연결 해제
await db.disconnect();
```

## 📊 모니터링

### 데이터베이스 모니터링

```javascript
const dbMonitor = require('./database/monitoring/dbMonitor');

// 시스템 헬스 체크
const health = await dbMonitor.getSystemHealth();

// 테이블 크기 확인
const tableSizes = await dbMonitor.getTableSizes();

// 연결 통계
const connectionStats = await dbMonitor.getConnectionStats();

// Redis 통계
const redisStats = await dbMonitor.getRedisStats();
```

### Prisma Studio

데이터베이스를 시각적으로 탐색하려면 Prisma Studio를 사용하세요:

```bash
npm run db:studio
```

## 💾 백업

### 자동 백업

백업 스크립트를 실행하여 데이터베이스를 백업할 수 있습니다:

```bash
npm run db:backup
```

### 수동 백업

```bash
# PostgreSQL 백업
pg_dump -h localhost -U postgres -d info_guard > backup.sql

# Redis 백업
redis-cli BGSAVE
```

## 🔧 유용한 명령어

```bash
# Prisma 클라이언트 재생성
npm run db:generate

# 데이터베이스 스키마 동기화
npm run db:push

# 마이그레이션 실행
npm run db:migrate

# 시드 데이터 삽입
npm run db:seed

# Prisma Studio 실행
npm run db:studio

# 백업 실행
npm run db:backup
```

## 🐛 문제 해결

### 일반적인 문제들

1. **연결 오류**
   - PostgreSQL과 Redis가 실행 중인지 확인
   - 환경 변수가 올바르게 설정되었는지 확인

2. **Prisma 오류**
   - `npm run db:generate` 실행
   - 데이터베이스 스키마 동기화 확인

3. **권한 오류**
   - PostgreSQL 사용자 권한 확인
   - 데이터베이스 생성 권한 확인

### 로그 확인

```bash
# PostgreSQL 로그
tail -f /usr/local/var/log/postgres.log

# Redis 로그
tail -f /usr/local/var/log/redis.log
```

## 📚 추가 자료

- [Prisma 공식 문서](https://www.prisma.io/docs/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation) 