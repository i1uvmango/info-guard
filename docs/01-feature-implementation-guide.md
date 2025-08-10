# Info-Guard 기능 구현 가이드

## 1. 기능 구현 전 준비사항

### 1.1 요구사항 분석
- **기능 목적**: 해당 기능이 Info-Guard의 어떤 목표를 달성하는지 명확히 파악
- **사용자 시나리오**: 실제 사용자가 어떻게 사용할지 구체적으로 정의
- **성능 요구사항**: 응답시간, 처리량, 정확도 등 정량적 목표 설정
- **보안 요구사항**: 데이터 보호, 개인정보 처리, API 보안 등

### 1.2 기술 스택 선택
- **AI/ML 기능**: Python (TensorFlow/PyTorch), OpenAI API
- **백엔드**: Node.js (Express), Python (FastAPI)
- **프론트엔드**: React (Chrome Extension)
- **데이터베이스**: PostgreSQL, Redis (캐싱)
- **외부 API**: YouTube Data API, 팩트체크 API

### 1.3 아키텍처 고려사항
- **마이크로서비스**: AI 분석, API 서비스, Chrome Extension 분리
- **실시간 처리**: WebSocket 또는 Server-Sent Events 활용
- **확장성**: 로드 밸런싱, 캐싱 전략 수립
- **장애 복구**: Circuit Breaker, Retry 메커니즘 구현

## 2. AI/ML 기능 구현

### 2.1 신뢰도 분석 모델
```python
# 신뢰도 분석 파이프라인
class CredibilityAnalyzer:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.bias_detector = BiasDetector()
        self.fact_checker = FactChecker()
        self.source_validator = SourceValidator()
    
    def analyze_video(self, video_data):
        # 1. 자막 텍스트 추출
        transcript = self.extract_transcript(video_data)
        
        # 2. 감정 분석
        sentiment_score = self.sentiment_analyzer.analyze(transcript)
        
        # 3. 편향 감지
        bias_score = self.bias_detector.detect(transcript)
        
        # 4. 팩트 체크
        fact_score = self.fact_checker.verify(transcript)
        
        # 5. 출처 검증
        source_score = self.source_validator.validate(video_data)
        
        # 6. 종합 신뢰도 계산
        credibility_score = self.calculate_credibility(
            sentiment_score, bias_score, fact_score, source_score
        )
        
        return CredibilityResult(
            score=credibility_score,
            breakdown={
                'sentiment': sentiment_score,
                'bias': bias_score,
                'fact_check': fact_score,
                'source': source_score
            },
            explanation=self.generate_explanation(credibility_score)
        )
```

### 2.2 편향 감지 알고리즘
```python
class BiasDetector:
    def __init__(self):
        self.bias_keywords = self.load_bias_keywords()
        self.emotional_indicators = self.load_emotional_indicators()
        self.political_indicators = self.load_political_indicators()
    
    def detect(self, text):
        # 1. 감정적 표현 감지
        emotional_bias = self.detect_emotional_bias(text)
        
        # 2. 정치적 편향 감지
        political_bias = self.detect_political_bias(text)
        
        # 3. 경제적 편향 감지
        economic_bias = self.detect_economic_bias(text)
        
        # 4. 문화적 편향 감지
        cultural_bias = self.detect_cultural_bias(text)
        
        return BiasResult(
            total_bias_score=self.calculate_total_bias(
                emotional_bias, political_bias, economic_bias, cultural_bias
            ),
            bias_types={
                'emotional': emotional_bias,
                'political': political_bias,
                'economic': economic_bias,
                'cultural': cultural_bias
            }
        )
```

### 2.3 팩트 체크 시스템
```python
class FactChecker:
    def __init__(self):
        self.external_apis = self.initialize_external_apis()
        self.fact_database = self.load_fact_database()
    
    def verify(self, text):
        # 1. 수치 데이터 추출
        numerical_claims = self.extract_numerical_claims(text)
        
        # 2. 외부 API로 검증
        verified_claims = []
        for claim in numerical_claims:
            verification_result = self.verify_with_external_api(claim)
            verified_claims.append(verification_result)
        
        # 3. 팩트 데이터베이스 검증
        fact_check_results = self.check_against_fact_database(text)
        
        # 4. 신뢰도 점수 계산
        fact_score = self.calculate_fact_score(verified_claims, fact_check_results)
        
        return FactCheckResult(
            score=fact_score,
            verified_claims=verified_claims,
            fact_check_results=fact_check_results
        )
```

## 3. Chrome Extension 구현

### 3.1 Extension 구조
```javascript
// manifest.json
{
  "manifest_version": 3,
  "name": "Info-Guard",
  "version": "1.0.0",
  "description": "YouTube 영상 신뢰도 분석 도구",
  "permissions": [
    "activeTab",
    "storage",
    "https://www.youtube.com/*"
  ],
  "content_scripts": [
    {
      "matches": ["https://www.youtube.com/*"],
      "js": ["content.js"],
      "css": ["styles.css"]
    }
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html"
  }
}
```

### 3.2 실시간 분석 기능
```javascript
// content.js
class InfoGuardAnalyzer {
    constructor() {
        this.apiEndpoint = 'https://api.info-guard.com/v1/analyze';
        this.currentVideoId = null;
        this.analysisResult = null;
    }
    
    async initialize() {
        // YouTube 페이지 감지
        if (this.isYouTubeVideoPage()) {
            this.currentVideoId = this.extractVideoId();
            await this.startAnalysis();
        }
    }
    
    async startAnalysis() {
        try {
            // 1. 비디오 정보 수집
            const videoInfo = await this.collectVideoInfo();
            
            // 2. API 호출
            const analysisResult = await this.callAnalysisAPI(videoInfo);
            
            // 3. UI 업데이트
            this.updateUI(analysisResult);
            
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError(error);
        }
    }
    
    async callAnalysisAPI(videoInfo) {
        const response = await fetch(this.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify(videoInfo)
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    updateUI(analysisResult) {
        // 신뢰도 등급 표시
        this.displayCredibilityGrade(analysisResult.credibility_grade);
        
        // 상세 정보 표시
        this.displayDetailedInfo(analysisResult);
        
        // 시각적 경고 표시
        if (analysisResult.credibility_score < 50) {
            this.showWarning(analysisResult);
        }
    }
}
```

### 3.3 UI 컴포넌트
```javascript
// UI 컴포넌트들
class CredibilityDisplay {
    constructor() {
        this.container = this.createContainer();
        this.injectIntoYouTube();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'info-guard-container';
        container.className = 'info-guard-credibility-display';
        return container;
    }
    
    displayCredibilityGrade(grade) {
        const gradeElement = document.createElement('div');
        gradeElement.className = `credibility-grade grade-${grade.toLowerCase()}`;
        gradeElement.innerHTML = `
            <div class="grade-icon">${this.getGradeIcon(grade)}</div>
            <div class="grade-text">신뢰도: ${grade}</div>
        `;
        
        this.container.appendChild(gradeElement);
    }
    
    displayDetailedInfo(analysisResult) {
        const detailsElement = document.createElement('div');
        detailsElement.className = 'credibility-details';
        detailsElement.innerHTML = `
            <div class="score-breakdown">
                <div class="score-item">
                    <span>편향 감지:</span>
                    <span class="score ${this.getScoreClass(analysisResult.bias_score)}">
                        ${analysisResult.bias_score}%
                    </span>
                </div>
                <div class="score-item">
                    <span>팩트 체크:</span>
                    <span class="score ${this.getScoreClass(analysisResult.fact_score)}">
                        ${analysisResult.fact_score}%
                    </span>
                </div>
                <div class="score-item">
                    <span>출처 검증:</span>
                    <span class="score ${this.getScoreClass(analysisResult.source_score)}">
                        ${analysisResult.source_score}%
                    </span>
                </div>
            </div>
        `;
        
        this.container.appendChild(detailsElement);
    }
}
```

## 4. API 서비스 구현

### 4.1 분석 API 엔드포인트
```javascript
// Express.js 서버
const express = require('express');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const cors = require('cors');

const app = express();

// 보안 미들웨어
app.use(helmet());
app.use(cors());
app.use(express.json());

// 속도 제한 설정
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15분
    max: 100, // 최대 100회 요청
    message: 'Too many requests from this IP'
});
app.use('/api/', limiter);

// 분석 API 엔드포인트
app.post('/api/v1/analyze-video', async (req, res) => {
    try {
        const { videoUrl, videoId, transcript } = req.body;
        
        // 1. 입력 검증
        if (!videoUrl && !videoId) {
            return res.status(400).json({
                error: 'videoUrl or videoId is required'
            });
        }
        
        // 2. 비디오 정보 수집
        const videoInfo = await collectVideoInfo(videoUrl || videoId);
        
        // 3. AI 분석 실행
        const analysisResult = await performAIAnalysis(videoInfo);
        
        // 4. 결과 캐싱
        await cacheAnalysisResult(videoId, analysisResult);
        
        // 5. 응답 반환
        res.json({
            success: true,
            data: analysisResult,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// 분석 함수
async function performAIAnalysis(videoInfo) {
    const analyzer = new CredibilityAnalyzer();
    
    // 1. 자막 분석
    const transcriptAnalysis = await analyzer.analyzeTranscript(videoInfo.transcript);
    
    // 2. 메타데이터 분석
    const metadataAnalysis = await analyzer.analyzeMetadata(videoInfo.metadata);
    
    // 3. 채널 정보 분석
    const channelAnalysis = await analyzer.analyzeChannel(videoInfo.channel);
    
    // 4. 종합 신뢰도 계산
    const credibilityScore = calculateCredibilityScore(
        transcriptAnalysis,
        metadataAnalysis,
        channelAnalysis
    );
    
    return {
        credibility_score: credibilityScore,
        credibility_grade: getCredibilityGrade(credibilityScore),
        analysis_breakdown: {
            transcript: transcriptAnalysis,
            metadata: metadataAnalysis,
            channel: channelAnalysis
        },
        explanation: generateExplanation(credibilityScore),
        confidence: calculateConfidence(transcriptAnalysis, metadataAnalysis, channelAnalysis)
    };
}
```

### 4.2 실시간 업데이트 API
```javascript
// WebSocket 서버
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    console.log('Client connected');
    
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            
            if (data.type === 'start_analysis') {
                // 실시간 분석 시작
                await startRealTimeAnalysis(ws, data.videoId);
            }
            
        } catch (error) {
            console.error('WebSocket error:', error);
            ws.send(JSON.stringify({
                type: 'error',
                message: error.message
            }));
        }
    });
    
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

async function startRealTimeAnalysis(ws, videoId) {
    try {
        // 1. 초기 분석
        const initialAnalysis = await performInitialAnalysis(videoId);
        ws.send(JSON.stringify({
            type: 'analysis_started',
            data: initialAnalysis
        }));
        
        // 2. 실시간 업데이트
        const updateInterval = setInterval(async () => {
            const updatedAnalysis = await performIncrementalAnalysis(videoId);
            ws.send(JSON.stringify({
                type: 'analysis_updated',
                data: updatedAnalysis
            }));
        }, 5000); // 5초마다 업데이트
        
        // 3. 분석 완료 시 정리
        setTimeout(() => {
            clearInterval(updateInterval);
            ws.send(JSON.stringify({
                type: 'analysis_completed',
                data: await getFinalAnalysis(videoId)
            }));
        }, 30000); // 30초 후 완료
        
    } catch (error) {
        ws.send(JSON.stringify({
            type: 'error',
            message: error.message
        }));
    }
}
```

## 5. 데이터베이스 설계

### 5.1 분석 결과 저장
```sql
-- 분석 결과 테이블
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) NOT NULL,
    video_url TEXT NOT NULL,
    channel_id VARCHAR(50),
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    credibility_score DECIMAL(5,2),
    credibility_grade VARCHAR(10),
    bias_score DECIMAL(5,2),
    fact_check_score DECIMAL(5,2),
    source_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    analysis_breakdown JSONB,
    explanation TEXT,
    confidence_score DECIMAL(5,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_analysis_results_video_id ON analysis_results(video_id);
CREATE INDEX idx_analysis_results_timestamp ON analysis_results(analysis_timestamp);
CREATE INDEX idx_analysis_results_credibility_score ON analysis_results(credibility_score);

-- 사용자 피드백 테이블
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    analysis_result_id INTEGER REFERENCES analysis_results(id),
    user_id VARCHAR(50),
    feedback_type VARCHAR(20), -- 'accurate', 'inaccurate', 'helpful', 'not_helpful'
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI 모델 성능 추적 테이블
CREATE TABLE model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50),
    model_version VARCHAR(20),
    accuracy_score DECIMAL(5,2),
    precision_score DECIMAL(5,2),
    recall_score DECIMAL(5,2),
    f1_score DECIMAL(5,2),
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_data_size INTEGER,
    performance_metrics JSONB
);
```

## 6. 테스트 구현

### 6.1 단위 테스트
```javascript
// AI 분석 테스트
describe('CredibilityAnalyzer', () => {
    let analyzer;
    
    beforeEach(() => {
        analyzer = new CredibilityAnalyzer();
    });
    
    test('should analyze video with high credibility correctly', async () => {
        const mockVideoData = {
            transcript: 'This is a factual news report with verified sources.',
            metadata: {
                title: 'Factual News Report',
                description: 'Based on verified sources and official data.'
            }
        };
        
        const result = await analyzer.analyze_video(mockVideoData);
        
        expect(result.score).toBeGreaterThan(70);
        expect(result.breakdown.sentiment).toBeLessThan(30); // 낮은 감정적 표현
        expect(result.breakdown.bias).toBeLessThan(20); // 낮은 편향
    });
    
    test('should detect biased content correctly', async () => {
        const mockVideoData = {
            transcript: 'This is clearly biased content with emotional language.',
            metadata: {
                title: 'Biased Opinion Piece',
                description: 'My personal opinion with strong emotional language.'
            }
        };
        
        const result = await analyzer.analyze_video(mockVideoData);
        
        expect(result.score).toBeLessThan(50);
        expect(result.breakdown.bias).toBeGreaterThan(60);
    });
});
```

### 6.2 통합 테스트
```javascript
// API 통합 테스트
describe('Analysis API', () => {
    test('should analyze YouTube video successfully', async () => {
        const response = await request(app)
            .post('/api/v1/analyze-video')
            .send({
                videoUrl: 'https://www.youtube.com/watch?v=test123'
            })
            .expect(200);
        
        expect(response.body.success).toBe(true);
        expect(response.body.data).toHaveProperty('credibility_score');
        expect(response.body.data).toHaveProperty('credibility_grade');
        expect(response.body.data).toHaveProperty('analysis_breakdown');
    });
    
    test('should handle invalid video URL', async () => {
        const response = await request(app)
            .post('/api/v1/analyze-video')
            .send({
                videoUrl: 'invalid-url'
            })
            .expect(400);
        
        expect(response.body.error).toBeDefined();
    });
});
```

### 6.3 성능 테스트
```javascript
// 성능 테스트
describe('Performance Tests', () => {
    test('should complete analysis within 5 seconds', async () => {
        const startTime = Date.now();
        
        const result = await analyzer.analyze_video(mockVideoData);
        
        const endTime = Date.now();
        const processingTime = endTime - startTime;
        
        expect(processingTime).toBeLessThan(5000); // 5초 이내
        expect(result).toBeDefined();
    });
    
    test('should handle concurrent requests', async () => {
        const concurrentRequests = 10;
        const promises = [];
        
        for (let i = 0; i < concurrentRequests; i++) {
            promises.push(analyzer.analyze_video(mockVideoData));
        }
        
        const results = await Promise.all(promises);
        
        expect(results).toHaveLength(concurrentRequests);
        results.forEach(result => {
            expect(result).toBeDefined();
            expect(result.score).toBeGreaterThanOrEqual(0);
            expect(result.score).toBeLessThanOrEqual(100);
        });
    });
});
```

## 7. 배포 및 모니터링

### 7.1 Docker 컨테이너화
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci --only=production

# 애플리케이션 코드 복사
COPY . .

# 보안 설정
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

CMD ["npm", "start"]
```

### 7.2 모니터링 설정
```javascript
// 모니터링 미들웨어
const monitoring = require('./monitoring');

app.use(monitoring.requestLogger);
app.use(monitoring.errorHandler);
app.use(monitoring.performanceTracker);

// 헬스체크 엔드포인트
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        version: process.env.npm_package_version
    });
});

// 메트릭 엔드포인트
app.get('/metrics', (req, res) => {
    res.json({
        requests_per_minute: monitoring.getRequestRate(),
        average_response_time: monitoring.getAverageResponseTime(),
        error_rate: monitoring.getErrorRate(),
        active_connections: monitoring.getActiveConnections()
    });
});
```

이 가이드라인을 따라 Info-Guard 프로젝트의 기능을 체계적이고 안전하게 구현할 수 있습니다. 각 단계에서 테스트를 포함하고, 보안과 성능을 고려하여 개발하는 것이 중요합니다. 