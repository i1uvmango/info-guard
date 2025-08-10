# Info-Guard 데이터베이스 구현 가이드

## 1. 요구사항 분석

### 1.1 기능 목적
- YouTube 영상 분석 결과 저장 및 관리
- 사용자 피드백 수집 및 AI 모델 성능 개선
- 채널별 신뢰도 통계 제공
- 캐싱을 통한 빠른 응답 속도

### 1.2 성능 요구사항
- 분석 결과 조회: 100ms 이내
- 동시 사용자: 1000명 이상 지원
- 데이터 저장: 분석당 1MB 이하

### 1.3 기술 스택
- **주 데이터베이스**: PostgreSQL 15+
- **캐시**: Redis 7+
- **ORM**: Prisma (Node.js)
- **백업**: pg_dump, Redis RDB/AOF

## 2. 데이터베이스 스키마 설계

### 2.1 핵심 테이블

#### analysis_results (분석 결과)
```sql
CREATE TABLE analysis_results (
    id BIGSERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL,
    video_url TEXT NOT NULL,
    channel_id VARCHAR(50),
    channel_name VARCHAR(200),
    video_title VARCHAR(500),
    credibility_score DECIMAL(5,2) CHECK (credibility_score >= 0 AND credibility_score <= 100),
    credibility_grade VARCHAR(10) CHECK (credibility_grade IN ('A', 'B', 'C', 'D', 'F')),
    bias_score DECIMAL(5,2),
    fact_check_score DECIMAL(5,2),
    source_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    analysis_breakdown JSONB,
    explanation TEXT,
    confidence_score DECIMAL(5,2),
    processing_time_ms INTEGER,
    model_version VARCHAR(20),
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, analysis_timestamp)
);
```

#### user_feedback (사용자 피드백)
```sql
CREATE TABLE user_feedback (
    id BIGSERIAL PRIMARY KEY,
    analysis_result_id BIGINT REFERENCES analysis_results(id) ON DELETE CASCADE,
    user_id VARCHAR(50),
    session_id VARCHAR(100),
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('accurate', 'inaccurate', 'helpful', 'not_helpful')),
    feedback_text TEXT,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_result_id, user_id, feedback_type)
);
```

#### channels (채널 정보)
```sql
CREATE TABLE channels (
    id BIGSERIAL PRIMARY KEY,
    channel_id VARCHAR(50) UNIQUE NOT NULL,
    channel_name VARCHAR(200) NOT NULL,
    channel_url TEXT,
    subscriber_count INTEGER,
    video_count INTEGER,
    view_count BIGINT,
    average_credibility_score DECIMAL(5,2),
    total_analyses INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 인덱스 생성
```sql
-- 분석 결과 인덱스
CREATE INDEX idx_analysis_results_video_id ON analysis_results(video_id);
CREATE INDEX idx_analysis_results_timestamp ON analysis_results(analysis_timestamp);
CREATE INDEX idx_analysis_results_credibility_score ON analysis_results(credibility_score);
CREATE INDEX idx_analysis_results_channel_id ON analysis_results(channel_id);

-- 피드백 인덱스
CREATE INDEX idx_user_feedback_analysis_id ON user_feedback(analysis_result_id);
CREATE INDEX idx_user_feedback_type ON user_feedback(feedback_type);

-- 채널 인덱스
CREATE INDEX idx_channels_channel_id ON channels(channel_id);
CREATE INDEX idx_channels_avg_credibility ON channels(average_credibility_score);
```

## 3. Prisma 스키마 설정

### 3.1 schema.prisma
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model AnalysisResult {
  id                BigInt    @id @default(autoincrement())
  videoId           String    @map("video_id") @db.VarChar(20)
  videoUrl          String    @map("video_url")
  channelId         String?   @map("channel_id") @db.VarChar(50)
  channelName       String?   @map("channel_name") @db.VarChar(200)
  videoTitle        String?   @map("video_title") @db.VarChar(500)
  credibilityScore  Decimal   @map("credibility_score") @db.Decimal(5,2)
  credibilityGrade  String    @map("credibility_grade") @db.VarChar(10)
  biasScore         Decimal   @map("bias_score") @db.Decimal(5,2)
  factCheckScore    Decimal   @map("fact_check_score") @db.Decimal(5,2)
  sourceScore       Decimal   @map("source_score") @db.Decimal(5,2)
  sentimentScore    Decimal   @map("sentiment_score") @db.Decimal(5,2)
  analysisBreakdown Json?     @map("analysis_breakdown")
  explanation       String?
  confidenceScore   Decimal   @map("confidence_score") @db.Decimal(5,2)
  processingTimeMs  Int?      @map("processing_time_ms")
  modelVersion      String?   @map("model_version") @db.VarChar(20)
  analysisTimestamp DateTime  @map("analysis_timestamp") @default(now())
  createdAt         DateTime  @map("created_at") @default(now())
  updatedAt         DateTime  @map("updated_at") @default(now())
  
  userFeedbacks     UserFeedback[]
  
  @@map("analysis_results")
  @@unique([videoId, analysisTimestamp])
  @@index([videoId])
  @@index([analysisTimestamp])
  @@index([credibilityScore])
  @@index([channelId])
}

model UserFeedback {
  id                BigInt    @id @default(autoincrement())
  analysisResultId  BigInt    @map("analysis_result_id")
  userId            String?   @map("user_id") @db.VarChar(50)
  sessionId         String?   @map("session_id") @db.VarChar(100)
  feedbackType      String    @map("feedback_type") @db.VarChar(20)
  feedbackText      String?
  feedbackScore     Int?      @map("feedback_score")
  createdAt         DateTime  @map("created_at") @default(now())
  
  analysisResult    AnalysisResult @relation(fields: [analysisResultId], references: [id], onDelete: Cascade)
  
  @@map("user_feedback")
  @@unique([analysisResultId, userId, feedbackType])
  @@index([analysisResultId])
  @@index([feedbackType])
}

model Channel {
  id                      BigInt    @id @default(autoincrement())
  channelId               String    @unique @map("channel_id") @db.VarChar(50)
  channelName             String    @map("channel_name") @db.VarChar(200)
  channelUrl              String?   @map("channel_url")
  subscriberCount         Int?      @map("subscriber_count")
  videoCount              Int?      @map("video_count")
  viewCount               BigInt?   @map("view_count")
  averageCredibilityScore Decimal?  @map("average_credibility_score") @db.Decimal(5,2)
  totalAnalyses           Int       @map("total_analyses") @default(0)
  createdAt               DateTime  @map("created_at") @default(now())
  updatedAt               DateTime  @map("updated_at") @default(now())
  
  @@map("channels")
  @@index([channelId])
  @@index([averageCredibilityScore])
}
```

## 4. 데이터 액세스 레이어

### 4.1 데이터베이스 연결
```javascript
// database/connection.js
const { PrismaClient } = require('@prisma/client');
const Redis = require('ioredis');

class DatabaseManager {
    constructor() {
        this.prisma = new PrismaClient({
            log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
        });
        
        this.redis = new Redis({
            host: process.env.REDIS_HOST || 'localhost',
            port: process.env.REDIS_PORT || 6379,
            password: process.env.REDIS_PASSWORD,
        });
    }
    
    async connect() {
        await this.prisma.$connect();
        await this.redis.ping();
        console.log('Database connections established');
    }
    
    async disconnect() {
        await this.prisma.$disconnect();
        await this.redis.quit();
    }
}

module.exports = new DatabaseManager();
```

### 4.2 분석 결과 저장소
```javascript
// database/repositories/analysisRepository.js
const db = require('../connection');

class AnalysisRepository {
    async createAnalysisResult(analysisData) {
        const result = await db.prisma.analysisResult.create({
            data: analysisData
        });
        
        // Redis 캐시 업데이트
        await db.redis.setex(`analysis:${result.videoId}:latest`, 3600, JSON.stringify(result));
        
        return result;
    }
    
    async getLatestAnalysisByVideoId(videoId) {
        // Redis에서 먼저 확인
        const cached = await db.redis.get(`analysis:${videoId}:latest`);
        if (cached) return JSON.parse(cached);
        
        // 데이터베이스에서 조회
        const result = await db.prisma.analysisResult.findFirst({
            where: { videoId },
            orderBy: { analysisTimestamp: 'desc' },
            include: { userFeedbacks: true }
        });
        
        if (result) {
            await db.redis.setex(`analysis:${videoId}:latest`, 3600, JSON.stringify(result));
        }
        
        return result;
    }
    
    async getCredibilityStats() {
        return await db.prisma.analysisResult.aggregate({
            _count: { id: true },
            _avg: { 
                credibilityScore: true,
                biasScore: true,
                factCheckScore: true,
                sourceScore: true,
                sentimentScore: true
            }
        });
    }
}

module.exports = new AnalysisRepository();
```

## 5. 마이그레이션 및 시드

### 5.1 마이그레이션 실행
```bash
# Prisma 마이그레이션 생성
npx prisma migrate dev --name init

# 데이터베이스 시드 실행
node database/seeds/seedData.js
```

### 5.2 시드 데이터
```javascript
// database/seeds/seedData.js
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function seedData() {
    // 샘플 분석 결과
    await prisma.analysisResult.create({
        data: {
            videoId: 'dQw4w9WgXcQ',
            videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            channelId: 'UC_x5XG1OV2P6uZZ5FSM9Ttw',
            channelName: 'Google Developers',
            videoTitle: 'Sample High Credibility Video',
            credibilityScore: 85.5,
            credibilityGrade: 'A',
            biasScore: 15.2,
            factCheckScore: 92.1,
            sourceScore: 88.7,
            sentimentScore: 45.3,
            analysisBreakdown: {
                sentiment: { score: 45.3, details: 'Neutral tone' },
                bias: { score: 15.2, details: 'Low bias detected' },
                factCheck: { score: 92.1, details: 'Most claims verified' },
                source: { score: 88.7, details: 'Reliable sources cited' }
            },
            explanation: 'This video demonstrates high credibility with verified sources.',
            confidenceScore: 87.2,
            processingTimeMs: 2500,
            modelVersion: '1.0.0'
        }
    });
    
    console.log('Seed data inserted successfully');
}

seedData().catch(console.error).finally(() => prisma.$disconnect());
```

## 6. 백업 및 모니터링

### 6.1 백업 스크립트
```bash
#!/bin/bash
# database/backup/backup.sh

BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="info_guard"

mkdir -p $BACKUP_DIR

# PostgreSQL 백업
pg_dump -h localhost -U postgres -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### 6.2 모니터링
```javascript
// database/monitoring/dbMonitor.js
const db = require('../connection');

class DatabaseMonitor {
    async getDatabaseStats() {
        return await db.prisma.$queryRaw`
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct
            FROM pg_stats 
            WHERE schemaname = 'public'
            ORDER BY tablename, attname;
        `;
    }
    
    async getTableSizes() {
        return await db.prisma.$queryRaw`
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
        `;
    }
}

module.exports = new DatabaseMonitor();
```

## 7. 구현 단계

### 7.1 1단계: 기본 스키마 설정
1. PostgreSQL 및 Redis 설치
2. Prisma 설정 및 스키마 생성
3. 기본 테이블 생성

### 7.2 2단계: 데이터 액세스 레이어
1. Repository 클래스 구현
2. 캐싱 로직 구현
3. 기본 CRUD 작업 구현

### 7.3 3단계: 마이그레이션 및 시드
1. 마이그레이션 파일 생성
2. 시드 데이터 작성
3. 테스트 데이터 삽입

### 7.4 4단계: 최적화 및 모니터링
1. 인덱스 최적화
2. 백업 스크립트 설정
3. 모니터링 도구 구현

이 가이드라인을 따라 Info-Guard 프로젝트의 데이터베이스를 체계적으로 구현할 수 있습니다. 