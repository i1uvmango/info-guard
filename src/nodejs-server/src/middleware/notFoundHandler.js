const { logger } = require('../utils/logger');

// 404 에러 핸들링 미들웨어
const notFoundHandler = (req, res, next) => {
  // 404 에러 로깅
  logger.warn('404 에러:', {
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // API 요청인 경우 JSON 응답
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({
      error: '요청한 리소스를 찾을 수 없습니다',
      status: 404,
      timestamp: new Date().toISOString(),
      path: req.path
    });
  }

  // 일반 요청인 경우 404 페이지 렌더링
  res.status(404).render('404', {
    title: '페이지를 찾을 수 없습니다',
    message: '요청하신 페이지가 존재하지 않습니다.',
    path: req.path
  });
};

module.exports = { notFoundHandler };
