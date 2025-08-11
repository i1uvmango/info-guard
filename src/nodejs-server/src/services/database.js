const { PrismaClient } = require('@prisma/client');
const { logger } = require('../utils/logger');

let prisma;

// 데이터베이스 연결 설정
const setupDatabase = async () => {
  try {
    prisma = new PrismaClient({
      log: process.env.NODE_ENV === 'development' ? ['query', 'info', 'warn', 'error'] : ['error']
    });

    // 데이터베이스 연결 테스트
    await prisma.$connect();
    logger.info('Prisma 데이터베이스 연결 성공');
    
    return prisma;
  } catch (error) {
    logger.error('데이터베이스 연결 실패:', error);
    throw error;
  }
};

// 데이터베이스 연결 해제
const disconnectDatabase = async () => {
  if (prisma) {
    await prisma.$disconnect();
    logger.info('데이터베이스 연결 해제됨');
  }
};

// Prisma 클라이언트 반환
const getPrismaClient = () => {
  if (!prisma) {
    throw new Error('데이터베이스가 초기화되지 않았습니다. setupDatabase()를 먼저 호출하세요.');
  }
  return prisma;
};

module.exports = {
  setupDatabase,
  disconnectDatabase,
  getPrismaClient
};
