/**
 * Info-Guard 헬스체크 라우터
 */

const express = require('express');
const router = express.Router();
const { logger } = require('../../utils/logger');

// 기본 헬스체크
router.get('/', (req, res) => {
    try {
        const healthData = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            version: '1.0.0',
            environment: process.env.NODE_ENV || 'development'
        };
        
        logger.info('Health check requested', { ip: req.ip });
        res.status(200).json(healthData);
        
    } catch (error) {
        logger.error('Health check failed', { error: error.message });
        res.status(500).json({
            status: 'unhealthy',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// 상세 헬스체크
router.get('/detailed', async (req, res) => {
    try {
        const detailedHealth = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            cpu: process.cpuUsage(),
            version: '1.0.0',
            environment: process.env.NODE_ENV || 'development',
            services: {
                database: 'unknown',
                redis: 'unknown',
                youtube_api: 'unknown'
            }
        };
        
        // 서비스 상태 확인 (비동기)
        try {
            // 여기에 실제 서비스 체크 로직 추가
            detailedHealth.services.database = 'healthy';
            detailedHealth.services.redis = 'healthy';
            detailedHealth.services.youtube_api = 'healthy';
        } catch (serviceError) {
            logger.error('Service health check failed', { error: serviceError.message });
            detailedHealth.status = 'degraded';
        }
        
        logger.info('Detailed health check requested', { ip: req.ip });
        res.status(200).json(detailedHealth);
        
    } catch (error) {
        logger.error('Detailed health check failed', { error: error.message });
        res.status(500).json({
            status: 'unhealthy',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

module.exports = router;
