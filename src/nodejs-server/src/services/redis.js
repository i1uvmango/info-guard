const redis = require('redis');
const { logger } = require('../utils/logger');

let redisClient;

// Redis 연결 설정
const setupRedis = async () => {
  try {
    redisClient = redis.createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      socket: {
        reconnectStrategy: (retries) => {
          if (retries > 10) {
            logger.error('Redis 재연결 시도 횟수 초과');
            return new Error('Redis 재연결 실패');
          }
          return Math.min(retries * 100, 3000);
        }
      }
    });

    // Redis 이벤트 리스너
    redisClient.on('connect', () => {
      logger.info('Redis 연결 성공');
    });

    redisClient.on('error', (err) => {
      logger.error('Redis 에러:', err);
    });

    redisClient.on('reconnecting', () => {
      logger.warn('Redis 재연결 시도 중...');
    });

    redisClient.on('end', () => {
      logger.warn('Redis 연결 종료됨');
    });

    // Redis 연결
    await redisClient.connect();
    
    return redisClient;
  } catch (error) {
    logger.error('Redis 연결 실패:', error);
    throw error;
  }
};

// Redis 연결 해제
const disconnectRedis = async () => {
  if (redisClient) {
    await redisClient.quit();
    logger.info('Redis 연결 해제됨');
  }
};

// Redis 클라이언트 반환
const getRedisClient = () => {
  if (!redisClient) {
    throw new Error('Redis가 초기화되지 않았습니다. setupRedis()를 먼저 호출하세요.');
  }
  return redisClient;
};

module.exports = {
  setupRedis,
  disconnectRedis,
  getRedisClient
};
