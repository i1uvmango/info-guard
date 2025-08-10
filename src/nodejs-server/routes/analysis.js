/**
 * Info-Guard 분석 API 라우터
 * YouTube 영상 신뢰도 분석 엔드포인트
 */

const express = require('express');
const Joi = require('joi');
const router = express.Router();

// 서비스들
const AnalysisService = require('../services/analysisService');
const YouTubeService = require('../services/youtubeService');
const CacheService = require('../services/cacheService');

// 미들웨어
const auth = require('../middleware/auth');
const { validateRequest, validateAnalysisRequest } = require('../middleware/validateRequest');

/**
 * POST /api/v1/analysis/analyze-video
 * YouTube 영상 신뢰도 분석
 */
router.post('/analyze-video', 
    auth.optionalAuth, 
    validateAnalysisRequest,
    async (req, res, next) => {
        try {
            const { videoUrl, videoId, transcript, metadata } = req.body;
            
            // 캐시 서비스 사용
            const cacheService = CacheService;
            
            // 캐시 키 생성
            const cacheKey = `analysis:${videoId || videoUrl}`;
            
            // 캐시에서 결과 확인
            const cachedResult = await cacheService.get(cacheKey);
            if (cachedResult) {
                return res.json({
                    success: true,
                    data: cachedResult,
                    cached: true,
                    timestamp: new Date().toISOString()
                });
            }
            
            // YouTube 서비스로 비디오 데이터 수집
            const youtubeService = new YouTubeService();
            let videoData;
            
            if (videoUrl || videoId) {
                videoData = await youtubeService.getVideoData(videoUrl || videoId);
            } else {
                // 직접 제공된 데이터 사용
                videoData = {
                    videoId: videoId || 'unknown',
                    transcript: transcript || '',
                    metadata: metadata || {}
                };
            }
            
            // 분석 서비스로 신뢰도 분석
            const analysisService = new AnalysisService();
            const analysisResult = await analysisService.analyzeVideo(videoData);
            
            // 결과 캐싱 (1시간)
            await cacheService.set(cacheKey, analysisResult, 3600);
            
            res.json({
                success: true,
                data: analysisResult,
                cached: false,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            next(error);
        }
    }
);

/**
 * GET /api/v1/analysis/status/:videoId
 * 분석 상태 확인
 */
router.get('/status/:videoId', async (req, res, next) => {
    try {
        const { videoId } = req.params;
        
        const cacheService = CacheService;
        const analysisResult = await cacheService.get(`analysis:${videoId}`);
        
        if (analysisResult) {
            res.json({
                success: true,
                data: {
                    videoId,
                    status: 'completed',
                    result: analysisResult
                }
            });
        } else {
            res.json({
                success: true,
                data: {
                    videoId,
                    status: 'not_found'
                }
            });
        }
        
    } catch (error) {
        next(error);
    }
});

/**
 * POST /api/v1/analysis/batch
 * 배치 분석 (여러 영상 동시 분석)
 */
router.post('/batch', 
    auth.authMiddleware,
    async (req, res, next) => {
        try {
            const { videos } = req.body;
            
            if (!Array.isArray(videos) || videos.length === 0) {
                return res.status(400).json({
                    error: 'Invalid request',
                    message: 'videos array is required'
                });
            }
            
            if (videos.length > 10) {
                return res.status(400).json({
                    error: 'Too many videos',
                    message: 'Maximum 10 videos allowed per batch'
                });
            }
            
            const analysisService = new AnalysisService();
            const youtubeService = new YouTubeService();
            const cacheService = CacheService;
            
            const results = [];
            
            for (const video of videos) {
                try {
                    const { videoUrl, videoId } = video;
                    
                    // 캐시 확인
                    const cacheKey = `analysis:${videoId || videoUrl}`;
                    const cachedResult = await cacheService.get(cacheKey);
                    
                    if (cachedResult) {
                        results.push({
                            videoId: videoId || videoUrl,
                            status: 'completed',
                            result: cachedResult,
                            cached: true
                        });
                        continue;
                    }
                    
                    // YouTube 데이터 수집
                    const videoData = await youtubeService.getVideoData(videoUrl || videoId);
                    
                    // 분석 수행
                    const analysisResult = await analysisService.analyzeVideo(videoData);
                    
                    // 결과 캐싱
                    await cacheService.set(cacheKey, analysisResult, 3600);
                    
                    results.push({
                        videoId: videoId || videoUrl,
                        status: 'completed',
                        result: analysisResult,
                        cached: false
                    });
                    
                } catch (error) {
                    results.push({
                        videoId: video.videoId || video.videoUrl,
                        status: 'failed',
                        error: error.message
                    });
                }
            }
            
            res.json({
                success: true,
                data: results,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            next(error);
        }
    }
);

/**
 * POST /api/v1/analysis/feedback
 * 분석 결과 피드백
 */
router.post('/feedback', async (req, res, next) => {
    try {
        const { videoId, analysisId, feedbackType, feedbackText } = req.body;
        
        // 피드백 저장 (실제 구현에서는 데이터베이스에 저장)
        console.log('Feedback received:', {
            videoId,
            analysisId,
            feedbackType,
            feedbackText,
            timestamp: new Date().toISOString()
        });
        
        res.json({
            success: true,
            message: 'Feedback saved successfully'
        });
        
    } catch (error) {
        next(error);
    }
});

/**
 * GET /api/v1/analysis/history
 * 분석 히스토리 조회
 */
router.get('/history', 
    auth.authMiddleware,
    async (req, res, next) => {
        try {
            const { page = 1, limit = 20 } = req.query;
            
            // 실제 구현에서는 데이터베이스에서 조회
            const history = [
                {
                    id: '1',
                    videoId: 'example123',
                    videoTitle: 'Example Video',
                    credibilityScore: 75,
                    credibilityGrade: '높음',
                    analyzedAt: new Date().toISOString()
                }
            ];
            
            res.json({
                success: true,
                data: {
                    history,
                    pagination: {
                        page: parseInt(page),
                        limit: parseInt(limit),
                        total: history.length
                    }
                }
            });
            
        } catch (error) {
            next(error);
        }
    }
);

module.exports = router; 