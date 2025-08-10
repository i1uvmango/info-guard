const db = require('../connection');

class AnalysisRepository {
    async createAnalysisResult(analysisData) {
        try {
            const result = await db.prisma.analysisResult.create({
                data: analysisData
            });
            
            // Redis 캐시 업데이트
            await this.cacheAnalysisResult(result.videoId, result);
            
            return result;
        } catch (error) {
            console.error('Error creating analysis result:', error);
            throw error;
        }
    }
    
    async getLatestAnalysisByVideoId(videoId) {
        try {
            // Redis에서 먼저 확인
            const cached = await db.redis.get(`analysis:${videoId}:latest`);
            if (cached) {
                return JSON.parse(cached);
            }
            
            // 데이터베이스에서 조회
            const result = await db.prisma.analysisResult.findFirst({
                where: { videoId },
                orderBy: { analysisTimestamp: 'desc' },
                include: {
                    userFeedbacks: {
                        select: {
                            feedbackType: true,
                            feedbackScore: true,
                            createdAt: true
                        }
                    }
                }
            });
            
            if (result) {
                // Redis에 캐시
                await this.cacheAnalysisResult(videoId, result);
            }
            
            return result;
        } catch (error) {
            console.error('Error getting latest analysis:', error);
            throw error;
        }
    }
    
    async getAnalysisHistory(videoId, limit = 10) {
        try {
            return await db.prisma.analysisResult.findMany({
                where: { videoId },
                orderBy: { analysisTimestamp: 'desc' },
                take: limit
            });
        } catch (error) {
            console.error('Error getting analysis history:', error);
            throw error;
        }
    }
    
    async getChannelAnalyses(channelId, limit = 50) {
        try {
            return await db.prisma.analysisResult.findMany({
                where: { channelId },
                orderBy: { analysisTimestamp: 'desc' },
                take: limit
            });
        } catch (error) {
            console.error('Error getting channel analyses:', error);
            throw error;
        }
    }
    
    async getCredibilityStats() {
        try {
            const stats = await db.prisma.analysisResult.aggregate({
                _count: { id: true },
                _avg: { 
                    credibilityScore: true,
                    biasScore: true,
                    factCheckScore: true,
                    sourceScore: true,
                    sentimentScore: true
                },
                _min: { credibilityScore: true },
                _max: { credibilityScore: true }
            });
            
            return {
                totalAnalyses: stats._count.id,
                averageCredibility: stats._avg.credibilityScore,
                averageBias: stats._avg.biasScore,
                averageFactCheck: stats._avg.factCheckScore,
                averageSource: stats._avg.sourceScore,
                averageSentiment: stats._avg.sentimentScore,
                minCredibility: stats._min.credibilityScore,
                maxCredibility: stats._max.credibilityScore
            };
        } catch (error) {
            console.error('Error getting credibility stats:', error);
            throw error;
        }
    }
    
    async cacheAnalysisResult(videoId, result) {
        try {
            await db.redis.setex(`analysis:${videoId}:latest`, 3600, JSON.stringify(result));
        } catch (error) {
            console.error('Error caching analysis result:', error);
        }
    }
    
    async invalidateCache(videoId) {
        try {
            await db.redis.del(`analysis:${videoId}:latest`);
        } catch (error) {
            console.error('Error invalidating cache:', error);
        }
    }
}

module.exports = new AnalysisRepository(); 