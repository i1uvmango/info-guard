const { logger } = require('../utils/logger');

// 에러 핸들링 미들웨어
const errorHandler = (err, req, res, next) => {
  // 에러 로깅
  logger.error('에러 발생:', {
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // 개발 환경에서는 스택 트레이스 포함
  const errorResponse = {
    error: err.message,
    status: err.status || 500,
    timestamp: new Date().toISOString()
  };

  if (process.env.NODE_ENV === 'development') {
    errorResponse.stack = err.stack;
  }

  // 상태 코드 설정
  res.status(err.status || 500);

  // API 요청인 경우 JSON 응답
  if (req.path.startsWith('/api/')) {
    return res.json(errorResponse);
  }

  // 일반 요청인 경우 에러 페이지 렌더링
  res.render('error', errorResponse);
};

module.exports = { errorHandler };
