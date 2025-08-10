const db = require('../connection');

class FeedbackRepository {
    async createFeedback(feedbackData) {
        try {
            const result = await db.prisma.userFeedback.create({
                data: {
                    analysisResultId: feedbackData.analysisResultId,
                    userId: feedbackData.userId,
                    sessionId: feedbackData.sessionId,
                    feedbackType: feedbackData.feedbackType,
                    feedbackText: feedbackData.feedbackText,
                    feedbackScore: feedbackData.feedbackScore,
                }
            });
            
            return result;
        } catch (error) {
            console.error('Error creating feedback:', error);
            throw error;
        }
    }
    
    async getFeedbackByAnalysisId(analysisResultId) {
        try {
            return await db.prisma.userFeedback.findMany({
                where: { analysisResultId },
                orderBy: { createdAt: 'desc' }
            });
        } catch (error) {
            console.error('Error getting feedback:', error);
            throw error;
        }
    }
    
    async getFeedbackStats() {
        try {
            const stats = await db.prisma.userFeedback.groupBy({
                by: ['feedbackType'],
                _count: { id: true },
                _avg: { feedbackScore: true }
            });
            
            return stats.reduce((acc, stat) => {
                acc[stat.feedbackType] = {
                    count: stat._count.id,
                    averageScore: stat._avg.feedbackScore
                };
                return acc;
            }, {});
        } catch (error) {
            console.error('Error getting feedback stats:', error);
            throw error;
        }
    }
    
    async updateChannelStats(channelId) {
        try {
            const channelAnalyses = await db.prisma.analysisResult.findMany({
                where: { channelId },
                select: { credibilityScore: true }
            });
            
            if (channelAnalyses.length > 0) {
                const avgCredibility = channelAnalyses.reduce((sum, analysis) => 
                    sum + parseFloat(analysis.credibilityScore), 0) / channelAnalyses.length;
                
                await db.prisma.channel.update({
                    where: { channelId },
                    data: {
                        averageCredibilityScore: avgCredibility,
                        totalAnalyses: channelAnalyses.length
                    }
                });
            }
        } catch (error) {
            console.error('Error updating channel stats:', error);
            throw error;
        }
    }
}

module.exports = new FeedbackRepository(); 