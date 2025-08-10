/**
 * Info-Guard 공통 타입 정의
 */

// 기본 응답 타입
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

// YouTube 영상 정보
export interface YouTubeVideo {
  video_id: string;
  title: string;
  description: string;
  channel_id: string;
  channel_name: string;
  published_at: string;
  duration: string;
  view_count: number;
  like_count: number;
  transcript?: string;
  tags?: string[];
}

// 신뢰도 분석 결과
export interface CredibilityAnalysis {
  video_id: string;
  credibility_score: number;      // 0-100
  credibility_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  bias_score: number;             // 0-100
  fact_check_score: number;       // 0-100
  source_score: number;           // 0-100
  sentiment_score: number;        // 0-100
  content_category: ContentCategory;
  analysis_breakdown: {
    sentiment: number;
    bias: number;
    fact_check: number;
    source: number;
  };
  explanation: string;
  confidence_score: number;       // 0-100
  processing_time_ms: number;
  model_version: string;
  created_at: string;
}

// 콘텐츠 카테고리
export type ContentCategory = 
  | 'politics'      // 정치
  | 'economy'       // 경제
  | 'social'        // 사회
  | 'investment'    // 투자
  | 'news'          // 시사
  | 'entertainment' // 오락
  | 'daily'         // 일상
  | 'other';        // 기타

// 사용자 피드백
export interface UserFeedback {
  id: string;
  analysis_id: string;
  user_id?: string;
  session_id: string;
  feedback_type: 'accurate' | 'inaccurate' | 'helpful' | 'not_helpful';
  feedback_text?: string;
  feedback_score: number;         // 1-5
  created_at: string;
}

// 채널 정보
export interface Channel {
  channel_id: string;
  channel_name: string;
  channel_url: string;
  subscriber_count: number;
  video_count: number;
  view_count: number;
  average_credibility_score: number;
  total_analyses: number;
  created_at: string;
  updated_at: string;
}

// 분석 요청
export interface AnalysisRequest {
  video_url: string;
  video_id?: string;
  force_refresh?: boolean;
  include_transcript?: boolean;
}

// WebSocket 메시지
export interface WebSocketMessage {
  type: 'analysis_progress' | 'analysis_complete' | 'error' | 'status';
  data: any;
  timestamp: string;
}

// 분석 진행 상태
export interface AnalysisProgress {
  video_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;               // 0-100
  current_step: string;
  estimated_time_remaining?: number;
}

// 시스템 상태
export interface SystemStatus {
  python_ai_server: 'healthy' | 'unhealthy' | 'unknown';
  nodejs_server: 'healthy' | 'unhealthy' | 'unknown';
  database: 'healthy' | 'unhealthy' | 'unknown';
  redis: 'healthy' | 'unhealthy' | 'unknown';
  last_check: string;
}

// 설정 옵션
export interface UserSettings {
  language: 'ko' | 'en';
  theme: 'light' | 'dark' | 'auto';
  notifications: boolean;
  auto_analysis: boolean;
  privacy_mode: boolean;
  data_collection: boolean;
}
