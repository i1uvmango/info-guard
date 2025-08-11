const { Server } = require('socket.io');
const { logger } = require('../utils/logger');

let io;

// Socket.IO 설정
const setupSocketIO = (server) => {
  try {
    io = new Server(server, {
      cors: {
        origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:8000'],
        methods: ['GET', 'POST'],
        credentials: true
      },
      transports: ['websocket', 'polling']
    });

    // 연결 이벤트
    io.on('connection', (socket) => {
      logger.info(`클라이언트 연결됨: ${socket.id}`);

      // 분석 진행상황 구독
      socket.on('subscribe_analysis', (analysisId) => {
        socket.join(`analysis_${analysisId}`);
        logger.info(`클라이언트 ${socket.id}가 분석 ${analysisId} 구독`);
      });

      // 분석 진행상황 구독 해제
      socket.on('unsubscribe_analysis', (analysisId) => {
        socket.leave(`analysis_${analysisId}`);
        logger.info(`클라이언트 ${socket.id}가 분석 ${analysisId} 구독 해제`);
      });

      // 연결 해제
      socket.on('disconnect', () => {
        logger.info(`클라이언트 연결 해제됨: ${socket.id}`);
      });
    });

    logger.info('Socket.IO 설정 완료');
    return io;
  } catch (error) {
    logger.error('Socket.IO 설정 실패:', error);
    throw error;
  }
};

// 분석 진행상황 업데이트 전송
const emitAnalysisProgress = (analysisId, progress, status, message) => {
  if (io) {
    io.to(`analysis_${analysisId}`).emit('analysis_progress', {
      analysisId,
      progress,
      status,
      message,
      timestamp: new Date().toISOString()
    });
    logger.debug(`분석 ${analysisId} 진행상황 전송: ${progress}%`);
  }
};

// 분석 완료 알림 전송
const emitAnalysisComplete = (analysisId, result) => {
  if (io) {
    io.to(`analysis_${analysisId}`).emit('analysis_complete', {
      analysisId,
      result,
      timestamp: new Date().toISOString()
    });
    logger.info(`분석 ${analysisId} 완료 알림 전송`);
  }
};

// Socket.IO 인스턴스 반환
const getSocketIO = () => {
  if (!io) {
    throw new Error('Socket.IO가 초기화되지 않았습니다. setupSocketIO()를 먼저 호출하세요.');
  }
  return io;
};

module.exports = {
  setupSocketIO,
  emitAnalysisProgress,
  emitAnalysisComplete,
  getSocketIO
};
