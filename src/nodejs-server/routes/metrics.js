/**
 * Info-Guard 메트릭 라우터
 */

const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// 기본 메트릭
router.get('/', (req, res) => {
    try {
        const metrics = {
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            cpu: process.cpuUsage(),
            version: '1.0.0'
        };
        
        logger.info('Metrics requested', { ip: req.ip });
        res.status(200).json(metrics);
        
    } catch (error) {
        logger.error('Metrics request failed', { error: error.message });
        res.status(500).json({
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// 성능 메트릭
router.get('/performance', (req, res) => {
    try {
        const performanceMetrics = {
            timestamp: new Date().toISOString(),
            memory: {
                rss: process.memoryUsage().rss,
                heapTotal: process.memoryUsage().heapTotal,
                heapUsed: process.memoryUsage().heapUsed,
                external: process.memoryUsage().external
            },
            cpu: process.cpuUsage(),
            uptime: process.uptime()
        };
        
        logger.info('Performance metrics requested', { ip: req.ip });
        res.status(200).json(performanceMetrics);
        
    } catch (error) {
        logger.error('Performance metrics request failed', { error: error.message });
        res.status(500).json({
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

module.exports = router; 