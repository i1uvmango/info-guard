/**
 * Info-Guard 백엔드 서버
 * YouTube 영상 신뢰도 분석을 위한 API 서비스
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { logger } = require('./utils/logger');
const { errorHandler } = require('./middleware/errorHandler');
const { notFoundHandler } = require('./middleware/notFoundHandler');
const { setupDatabase } = require('./services/database');
const { setupRedis } = require('./services/redis');
const { setupSocketIO } = require('./services/socket');

// 라우터 임포트
const healthRoutes = require('./api/routes/health');
const analysisRoutes = require('./api/routes/analysis');
const userRoutes = require('./api/routes/user');
const feedbackRoutes = require('./api/routes/feedback');

const app = express();
const PORT = process.env.PORT || 3000;

// 기본 미들웨어
app.use(helmet());
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// CORS 설정
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:8000'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15분
  max: 100, // IP당 최대 요청 수
  message: '너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.'
});
app.use('/api/', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 정적 파일 제공
app.use('/public', express.static('public'));

// API 라우트
app.use('/health', healthRoutes);
app.use('/api/v1/analysis', analysisRoutes);
app.use('/api/v1/users', userRoutes);
app.use('/api/v1/feedback', feedbackRoutes);

// 기본 라우트
app.get('/', (req, res) => {
  res.json({
    message: 'Info-Guard 백엔드 서버에 오신 것을 환영합니다!',
    version: '1.0.0',
    status: 'running'
  });
});

// 에러 핸들링
app.use(notFoundHandler);
app.use(errorHandler);

// 서버 시작
async function startServer() {
  try {
    // 데이터베이스 연결
    await setupDatabase();
    logger.info('데이터베이스 연결 성공');
    
    // Redis 연결
    await setupRedis();
    logger.info('Redis 연결 성공');
    
    // HTTP 서버 시작
    const server = app.listen(PORT, () => {
      logger.info(`Info-Guard 백엔드 서버가 포트 ${PORT}에서 실행 중입니다`);
    });
    
    // Socket.IO 설정
    setupSocketIO(server);
    
    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM 신호를 받았습니다. 서버를 종료합니다...');
      server.close(() => {
        logger.info('서버가 정상적으로 종료되었습니다');
        process.exit(0);
      });
    });
    
  } catch (error) {
    logger.error('서버 시작 실패:', error);
    process.exit(1);
  }
}

// 예상치 못한 에러 처리
process.on('uncaughtException', (error) => {
  logger.error('예상치 못한 에러:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('처리되지 않은 Promise 거부:', reason);
  process.exit(1);
});

startServer();
