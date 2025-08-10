const db = require('../connection');

class ChannelRepository {
    async createOrUpdateChannel(channelData) {
        try {
            const result = await db.prisma.channel.upsert({
                where: { channelId: channelData.channelId },
                update: {
                    channelName: channelData.channelName,
                    channelUrl: channelData.channelUrl,
                    subscriberCount: channelData.subscriberCount,
                    videoCount: channelData.videoCount,
                    viewCount: channelData.viewCount,
                    updatedAt: new Date()
                },
                create: {
                    channelId: channelData.channelId,
                    channelName: channelData.channelName,
                    channelUrl: channelData.channelUrl,
                    subscriberCount: channelData.subscriberCount,
                    videoCount: channelData.videoCount,
                    viewCount: channelData.viewCount,
                    averageCredibilityScore: null,
                    totalAnalyses: 0
                }
            });
            
            return result;
        } catch (error) {
            console.error('Error creating/updating channel:', error);
            throw error;
        }
    }
    
    async getChannelById(channelId) {
        try {
            return await db.prisma.channel.findUnique({
                where: { channelId }
            });
        } catch (error) {
            console.error('Error getting channel:', error);
            throw error;
        }
    }
    
    async getTopChannelsByCredibility(limit = 10) {
        try {
            return await db.prisma.channel.findMany({
                where: {
                    averageCredibilityScore: { not: null },
                    totalAnalyses: { gte: 5 } // 최소 5개 분석이 있는 채널만
                },
                orderBy: { averageCredibilityScore: 'desc' },
                take: limit
            });
        } catch (error) {
            console.error('Error getting top channels:', error);
            throw error;
        }
    }
    
    async getChannelStats(channelId) {
        try {
            const channel = await db.prisma.channel.findUnique({
                where: { channelId }
            });
            
            if (!channel) {
                return null;
            }
            
            const analyses = await db.prisma.analysisResult.findMany({
                where: { channelId },
                orderBy: { analysisTimestamp: 'desc' },
                take: 100
            });
            
            const gradeDistribution = analyses.reduce((acc, analysis) => {
                const grade = analysis.credibilityGrade;
                acc[grade] = (acc[grade] || 0) + 1;
                return acc;
            }, {});
            
            return {
                channel,
                totalAnalyses: analyses.length,
                gradeDistribution,
                recentAnalyses: analyses.slice(0, 10)
            };
        } catch (error) {
            console.error('Error getting channel stats:', error);
            throw error;
        }
    }
    
    async updateChannelCredibility(channelId) {
        try {
            const analyses = await db.prisma.analysisResult.findMany({
                where: { channelId },
                select: { credibilityScore: true }
            });
            
            if (analyses.length > 0) {
                const avgCredibility = analyses.reduce((sum, analysis) => 
                    sum + parseFloat(analysis.credibilityScore), 0) / analyses.length;
                
                await db.prisma.channel.update({
                    where: { channelId },
                    data: {
                        averageCredibilityScore: avgCredibility,
                        totalAnalyses: analyses.length
                    }
                });
            }
        } catch (error) {
            console.error('Error updating channel credibility:', error);
            throw error;
        }
    }
}

module.exports = new ChannelRepository(); 