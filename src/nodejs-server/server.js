/**
 * Info-Guard Backend Server
 * YouTube 영상 신뢰도 분석 API 서버
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const compression = require('compression');
const morgan = require('morgan');
const { WebSocket, WebSocketServer } = require('ws');
const http = require('http');

// 환경 변수 로드
require('dotenv').config();

// 라우터들
const analysisRoutes = require('./routes/analysis');
const healthRoutes = require('./routes/health');
const metricsRoutes = require('./routes/metrics');

// 미들웨어들
const errorHandler = require('./middleware/errorHandler');
const requestLogger = require('./middleware/requestLogger');
const authMiddleware = require('./middleware/auth');

// 서비스들
const YouTubeService = require('./services/youtubeService');
const AnalysisService = require('./services/analysisService');
const CacheService = require('./services/cacheService');

const app = express();
const server = http.createServer(app);

// WebSocket 서버 설정
const wss = new WebSocketServer({ server });

// 기본 미들웨어
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 로깅 미들웨어
app.use(morgan('combined'));
app.use(requestLogger);

// 속도 제한 설정
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15분
    max: 100, // 최대 100회 요청
    message: {
        error: 'Too many requests from this IP',
        message: 'Please try again later'
    },
    standardHeaders: true,
    legacyHeaders: false
});
app.use('/api/', limiter);

// 라우터 설정
app.use('/api/v1/analysis', analysisRoutes);
app.use('/health', healthRoutes);
app.use('/metrics', metricsRoutes);

// 기본 라우트
app.get('/', (req, res) => {
    res.json({
        name: 'Info-Guard API',
        version: '1.0.0',
        description: 'YouTube Content Credibility Analysis API',
        endpoints: {
            analysis: '/api/v1/analysis',
            health: '/health',
            metrics: '/metrics'
        }
    });
});

// 404 핸들러
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.originalUrl} not found`
    });
});

// 에러 핸들러
app.use(errorHandler);

// WebSocket 연결 처리
wss.on('connection', (ws) => {
    console.log('Client connected to WebSocket');
    
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            
            if (data.type === 'start_analysis') {
                await handleAnalysisRequest(ws, data);
            } else if (data.type === 'ping') {
                ws.send(JSON.stringify({ type: 'pong' }));
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
        console.log('Client disconnected from WebSocket');
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
});

// 분석 요청 처리
async function handleAnalysisRequest(ws, data) {
    try {
        const { videoUrl, videoId } = data;
        
        if (!videoUrl && !videoId) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'videoUrl or videoId is required'
            }));
            return;
        }
        
        // 분석 시작 알림
        ws.send(JSON.stringify({
            type: 'analysis_started',
            data: { videoUrl, videoId }
        }));
        
        // YouTube 데이터 수집
        const youtubeService = new YouTubeService();
        const videoData = await youtubeService.getVideoData(videoUrl || videoId);
        
        // 분석 서비스 초기화
        const analysisService = new AnalysisService();
        
        // 실시간 분석 진행
        const analysisResult = await analysisService.analyzeVideo(videoData);
        
        // 결과 전송
        ws.send(JSON.stringify({
            type: 'analysis_completed',
            data: analysisResult
        }));
        
    } catch (error) {
        console.error('Analysis request failed:', error);
        ws.send(JSON.stringify({
            type: 'error',
            message: error.message
        }));
    }
}

// 서버 시작
const PORT = process.env.PORT || 3000;

server.listen(PORT, () => {
    console.log(`Info-Guard API Server running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`WebSocket server ready for connections`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

module.exports = app; 