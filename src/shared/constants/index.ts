/**
 * Info-Guard 공통 상수 정의
 */

// API 엔드포인트
export const API_ENDPOINTS = {
  // Python AI 서버
  PYTHON_AI: {
    BASE: process.env.PYTHON_AI_URL || 'http://localhost:8000',
    HEALTH: '/health',
    ANALYSIS: '/api/v1/analysis',
    WEBSOCKET: '/ws'
  },
  
  // Node.js 백엔드 서버
  NODEJS: {
    BASE: process.env.NODEJS_URL || 'http://localhost:3000',
    HEALTH: '/health',
    ANALYSIS: '/api/v1/analysis',
    USERS: '/api/v1/users',
    FEEDBACK: '/api/v1/feedback',
    WEBSOCKET: '/socket.io'
  }
} as const;

// 신뢰도 등급 기준
export const CREDIBILITY_GRADES = {
  A: { min: 80, max: 100, label: '높음', color: '#22c55e' },
  B: { min: 60, max: 79, label: '보통', color: '#3b82f6' },
  C: { min: 40, max: 59, label: '낮음', color: '#f59e0b' },
  D: { min: 20, max: 39, label: '매우 낮음', color: '#ef4444' },
  F: { min: 0, max: 19, label: '신뢰할 수 없음', color: '#dc2626' }
} as const;

// 콘텐츠 카테고리
export const CONTENT_CATEGORIES = {
  POLITICS: {
    key: 'politics',
    label: '정치',
    keywords: ['정치', '선거', '정부', '국회', '정책', '여당', '야당']
  },
  ECONOMY: {
    key: 'economy',
    label: '경제',
    keywords: ['경제', '주식', '부동산', '투자', '금융', '은행', '증권']
  },
  SOCIAL: {
    key: 'social',
    label: '사회',
    keywords: ['사회', '교육', '의료', '환경', '교통', '복지', '범죄']
  },
  INVESTMENT: {
    key: 'investment',
    label: '투자',
    keywords: ['투자', '주식', '부동산', '암호화폐', '펀드', '보험', '연금']
  },
  NEWS: {
    key: 'news',
    label: '시사',
    keywords: ['뉴스', '시사', '사건', '사고', '재난', '기후', '국제']
  },
  ENTERTAINMENT: {
    key: 'entertainment',
    label: '오락',
    keywords: ['게임', '음악', '영화', '드라마', '예능', '유튜버', '스트리머']
  },
  DAILY: {
    key: 'daily',
    label: '일상',
    keywords: ['일상', '브이로그', '요리', '여행', '운동', '패션', '뷰티']
  }
} as const;

// 편향 감지 키워드
export const BIAS_KEYWORDS = {
  EMOTIONAL: [
    '충격', '충격적', '놀라운', '믿을 수 없는', '믿을 수 없어',
    '어마어마한', '엄청난', '대박', '최고', '최악',
    '절대', '완벽', '완벽한', '완벽하게', '완벽하다'
  ],
  POLITICAL: [
    '좌파', '우파', '진보', '보수', '개혁', '혁명',
    '체제', '정권', '독재', '민주주의', '자유주의'
  ],
  ECONOMIC: [
    '폭락', '폭등', '대박', '망했다', '성공', '실패',
    '부자', '빈자', '부의 재분배', '자본주의', '사회주의'
  ]
} as const;

// YouTube API 설정
export const YOUTUBE_API = {
  BASE_URL: 'https://www.googleapis.com/youtube/v3',
  MAX_RESULTS: 50,
  DEFAULT_REGION: 'KR',
  DEFAULT_LANGUAGE: 'ko'
} as const;

// 분석 설정
export const ANALYSIS_CONFIG = {
  MAX_TRANSCRIPT_LENGTH: 10000,  // 최대 자막 길이
  MIN_CONFIDENCE_THRESHOLD: 0.7, // 최소 신뢰도 임계값
  MAX_PROCESSING_TIME: 30000,    // 최대 처리 시간 (ms)
  CACHE_DURATION: 24 * 60 * 60   // 캐시 유효 기간 (초)
} as const;

// 에러 메시지
export const ERROR_MESSAGES = {
  VIDEO_NOT_FOUND: '영상을 찾을 수 없습니다.',
  ANALYSIS_FAILED: '분석에 실패했습니다.',
  INVALID_VIDEO_URL: '올바르지 않은 YouTube URL입니다.',
  API_RATE_LIMIT: 'API 요청 한도를 초과했습니다.',
  NETWORK_ERROR: '네트워크 오류가 발생했습니다.',
  SERVER_ERROR: '서버 오류가 발생했습니다.',
  UNAUTHORIZED: '인증이 필요합니다.',
  FORBIDDEN: '접근이 거부되었습니다.'
} as const;

// 성공 메시지
export const SUCCESS_MESSAGES = {
  ANALYSIS_COMPLETED: '분석이 완료되었습니다.',
  FEEDBACK_SUBMITTED: '피드백이 제출되었습니다.',
  SETTINGS_SAVED: '설정이 저장되었습니다.',
  CACHE_CLEARED: '캐시가 정리되었습니다.'
} as const;

// UI 설정
export const UI_CONFIG = {
  POPUP_WIDTH: 400,
  POPUP_HEIGHT: 600,
  TOOLTIP_DELAY: 500,
  ANIMATION_DURATION: 300,
  REFRESH_INTERVAL: 5000
} as const;

// 로깅 설정
export const LOG_LEVELS = {
  ERROR: 'ERROR',
  WARN: 'WARN',
  INFO: 'INFO',
  DEBUG: 'DEBUG'
} as const;

// 환경 설정
export const ENV = {
  DEVELOPMENT: 'development',
  PRODUCTION: 'production',
  TEST: 'test'
} as const;
