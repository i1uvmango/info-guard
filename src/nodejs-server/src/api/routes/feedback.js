const express = require('express');
const { body, validationResult } = require('express-validator');
const { logger } = require('../../utils/logger');
const { getPrismaClient } = require('../../services/database');

const router = express.Router();

// 피드백 제출
router.post('/', [
  body('analysisId').isUUID(),
  body('rating').isInt({ min: 1, max: 5 }),
  body('comment').optional().isLength({ max: 1000 }),
  body('category').optional().isIn(['accuracy', 'usefulness', 'interface', 'other'])
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

    const { analysisId, rating, comment, category } = req.body;
    const prisma = getPrismaClient();

    // 분석 결과 존재 확인
    const analysis = await prisma.analysis.findUnique({
      where: { id: analysisId }
    });

    if (!analysis) {
      return res.status(404).json({
        error: '분석 결과를 찾을 수 없습니다'
      });
    }

    // 피드백 생성
    const feedback = await prisma.feedback.create({
      data: {
        analysisId,
        rating,
        comment,
        category: category || 'other',
        ipAddress: req.ip,
        userAgent: req.get('User-Agent')
      }
    });

    logger.info(`새 피드백 제출: 분석 ${analysisId}, 평점 ${rating}`);
    res.status(201).json({
      message: '피드백이 성공적으로 제출되었습니다',
      feedback: {
        id: feedback.id,
        rating: feedback.rating,
        category: feedback.category,
        createdAt: feedback.createdAt
      }
    });
  } catch (error) {
    logger.error('피드백 제출 실패:', error);
    res.status(500).json({
      error: '피드백 제출 중 오류가 발생했습니다'
    });
  }
});

// 분석별 피드백 조회
router.get('/analysis/:analysisId', async (req, res) => {
  try {
    const { analysisId } = req.params;
    const prisma = getPrismaClient();

    // 분석 결과 존재 확인
    const analysis = await prisma.analysis.findUnique({
      where: { id: analysisId }
    });

    if (!analysis) {
      return res.status(404).json({
        error: '분석 결과를 찾을 수 없습니다'
      });
    }

    // 피드백 조회
    const feedbacks = await prisma.feedback.findMany({
      where: { analysisId },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        rating: true,
        comment: true,
        category: true,
        createdAt: true
      }
    });

    // 통계 계산
    const totalFeedbacks = feedbacks.length;
    const averageRating = totalFeedbacks > 0 
      ? feedbacks.reduce((sum, f) => sum + f.rating, 0) / totalFeedbacks 
      : 0;

    const ratingDistribution = feedbacks.reduce((acc, f) => {
      acc[f.rating] = (acc[f.rating] || 0) + 1;
      return acc;
    }, {});

    res.json({
      analysisId,
      totalFeedbacks,
      averageRating: Math.round(averageRating * 100) / 100,
      ratingDistribution,
      feedbacks
    });
  } catch (error) {
    logger.error('피드백 조회 실패:', error);
    res.status(500).json({
      error: '피드백 조회 중 오류가 발생했습니다'
    });
  }
});

// 전체 피드백 통계
router.get('/stats', async (req, res) => {
  try {
    const prisma = getPrismaClient();

    // 전체 통계 조회
    const totalFeedbacks = await prisma.feedback.count();
    const averageRating = await prisma.feedback.aggregate({
      _avg: { rating: true }
    });

    const categoryStats = await prisma.feedback.groupBy({
      by: ['category'],
      _count: { id: true },
      _avg: { rating: true }
    });

    const recentFeedbacks = await prisma.feedback.findMany({
      take: 10,
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        rating: true,
        category: true,
        createdAt: true,
        analysis: {
          select: {
            id: true,
            videoUrl: true
          }
        }
      }
    });

    res.json({
      totalFeedbacks,
      averageRating: Math.round((averageRating._avg.rating || 0) * 100) / 100,
      categoryStats,
      recentFeedbacks
    });
  } catch (error) {
    logger.error('피드백 통계 조회 실패:', error);
    res.status(500).json({
      error: '피드백 통계 조회 중 오류가 발생했습니다'
    });
  }
});

module.exports = router;
