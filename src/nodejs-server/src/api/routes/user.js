const express = require('express');
const { body, validationResult } = require('express-validator');
const { logger } = require('../../utils/logger');
const { getPrismaClient } = require('../../services/database');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const router = express.Router();

// 사용자 등록
router.post('/register', [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 6 }),
  body('username').isLength({ min: 2, max: 30 })
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

    const { email, password, username } = req.body;
    const prisma = getPrismaClient();

    // 이메일 중복 확인
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      return res.status(409).json({
        error: '이미 등록된 이메일입니다'
      });
    }

    // 비밀번호 해시화
    const hashedPassword = await bcrypt.hash(password, 12);

    // 사용자 생성
    const user = await prisma.user.create({
      data: {
        email,
        username,
        password: hashedPassword
      },
      select: {
        id: true,
        email: true,
        username: true,
        createdAt: true
      }
    });

    logger.info(`새 사용자 등록: ${email}`);
    res.status(201).json({
      message: '사용자 등록이 완료되었습니다',
      user
    });
  } catch (error) {
    logger.error('사용자 등록 실패:', error);
    res.status(500).json({
      error: '사용자 등록 중 오류가 발생했습니다'
    });
  }
});

// 사용자 로그인
router.post('/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').notEmpty()
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

    const { email, password } = req.body;
    const prisma = getPrismaClient();

    // 사용자 찾기
    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      return res.status(401).json({
        error: '이메일 또는 비밀번호가 올바르지 않습니다'
      });
    }

    // 비밀번호 확인
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      return res.status(401).json({
        error: '이메일 또는 비밀번호가 올바르지 않습니다'
      });
    }

    // JWT 토큰 생성
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    logger.info(`사용자 로그인: ${email}`);
    res.json({
      message: '로그인이 완료되었습니다',
      token,
      user: {
        id: user.id,
        email: user.email,
        username: user.username
      }
    });
  } catch (error) {
    logger.error('사용자 로그인 실패:', error);
    res.status(500).json({
      error: '로그인 중 오류가 발생했습니다'
    });
  }
});

// 사용자 프로필 조회
router.get('/profile', async (req, res) => {
  try {
    // JWT 토큰 검증 (실제로는 미들웨어로 처리)
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) {
      return res.status(401).json({
        error: '인증 토큰이 필요합니다'
      });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    const prisma = getPrismaClient();

    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        email: true,
        username: true,
        createdAt: true,
        updatedAt: true
      }
    });

    if (!user) {
      return res.status(404).json({
        error: '사용자를 찾을 수 없습니다'
      });
    }

    res.json({ user });
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        error: '유효하지 않은 토큰입니다'
      });
    }
    
    logger.error('사용자 프로필 조회 실패:', error);
    res.status(500).json({
      error: '프로필 조회 중 오류가 발생했습니다'
    });
  }
});

module.exports = router;
