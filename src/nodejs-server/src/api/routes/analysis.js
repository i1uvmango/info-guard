const express = require('express');
const { body, validationResult } = require('express-validator');
const { logger } = require('../../utils/logger');
const { getPrismaClient } = require('../../services/database');
const { getRedisClient } = require('../../services/redis');

const router = express.Router();

// 분석 요청
router.post('/analyze', [
  body('videoUrl').isURL().withMessage('유효한 YouTube URL이 필요합니다'),
  body('userId').optional().isUUID()
], async (req, res) => {
  try {
    // 입력 검증
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: '입력 데이터가 유효하지 않습니다',
        details: errors.array()
      });
    }

    const { videoUrl, userId } = req.body;
    const prisma = getPrismaClient();
    const redis = getRedisClient();

    // 캐시에서 기존 분석 결과 확인
    const cacheKey = `analysis:${videoUrl}`;
    const cachedResult = await redis.get(cacheKey);
    
    if (cachedResult) {
      const parsedResult = JSON.parse(cachedResult);
      logger.info(`캐시된 분석 결과 사용: ${videoUrl}`);
      
      return res.json({
        analysisId: parsedResult.analysisId,
        status: 'completed',
        result: parsedResult.result,
        cached: true,
        timestamp: new Date().toISOString()
      });
    }

    // 새로운 분석 생성
    const analysis = await prisma.analysis.create({
      data: {
        videoUrl,
        userId: userId || null,
        status: 'pending',
        progress: 0
      }
    });

    logger.info(`새 분석 요청 생성: ${analysis.id} - ${videoUrl}`);

    // 백그라운드에서 분석 실행 (실제로는 작업 큐 사용)
    setTimeout(async () => {
      try {
        // 분석 진행상황 업데이트
        await prisma.analysis.update({
          where: { id: analysis.id },
          data: { progress: 50, status: 'processing' }
        });

        // 가상의 분석 결과 생성
        const result = {
          credibility: Math.random() * 100,
          bias: Math.random() * 100,
          factuality: Math.random() * 100,
          overall: Math.random() * 100
        };

        // 분석 완료
        await prisma.analysis.update({
          where: { id: analysis.id },
          data: {
            progress: 100,
            status: 'completed',
            result: result
          }
        });

        // 결과 캐싱 (1시간)
        await redis.setEx(cacheKey, 3600, JSON.stringify({
          analysisId: analysis.id,
          result: result
        }));

        logger.info(`분석 완료: ${analysis.id}`);
      } catch (error) {
        logger.error(`분석 실패: ${analysis.id}`, error);
        await prisma.analysis.update({
          where: { id: analysis.id },
          data: {
            status: 'failed',
            error: error.message
          }
        });
      }
    }, 1000);

    res.status(202).json({
      analysisId: analysis.id,
      status: 'pending',
      message: '분석이 시작되었습니다',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('분석 요청 실패:', error);
    res.status(500).json({
      error: '분석 요청 중 오류가 발생했습니다'
    });
  }
});

// 분석 상태 조회
router.get('/status/:analysisId', async (req, res) => {
  try {
    const { analysisId } = req.params;
    const prisma = getPrismaClient();

    const analysis = await prisma.analysis.findUnique({
      where: { id: analysisId }
    });

    if (!analysis) {
      return res.status(404).json({
        error: '분석 ID를 찾을 수 없습니다'
      });
    }

    res.json({
      analysisId: analysis.id,
      status: analysis.status,
      progress: analysis.progress,
      result: analysis.result,
      error: analysis.error,
      createdAt: analysis.createdAt,
      updatedAt: analysis.updatedAt
    });
  } catch (error) {
    logger.error('분석 상태 조회 실패:', error);
    res.status(500).json({
      error: '분석 상태 조회 중 오류가 발생했습니다'
    });
  }
});

// 분석 결과 목록 조회
router.get('/list', async (req, res) => {
  try {
    const { page = 1, limit = 10, status } = req.query;
    const prisma = getPrismaClient();

    const where = {};
    if (status) {
      where.status = status;
    }

    const analyses = await prisma.analysis.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      skip: (page - 1) * limit,
      take: parseInt(limit),
      select: {
        id: true,
        videoUrl: true,
        status: true,
        progress: true,
        createdAt: true,
        updatedAt: true
      }
    });

    const total = await prisma.analysis.count({ where });

    res.json({
      analyses,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    logger.error('분석 목록 조회 실패:', error);
    res.status(500).json({
      error: '분석 목록 조회 중 오류가 발생했습니다'
    });
  }
});

module.exports = router;
