const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();

async function seedData() {
    try {
        console.log('Starting seed data insertion...');
        
        // 샘플 채널 데이터
        const sampleChannels = [
            {
                channelId: 'UC_x5XG1OV2P6uZZ5FSM9Ttw',
                channelName: 'Google Developers',
                channelUrl: 'https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw',
                subscriberCount: 5000000,
                videoCount: 1500,
                viewCount: 1000000000,
                averageCredibilityScore: 82.5,
                totalAnalyses: 2
            },
            {
                channelId: 'UCBR8-60-B28hp2BmDPdntcQ',
                channelName: 'YouTube',
                channelUrl: 'https://www.youtube.com/channel/UCBR8-60-B28hp2BmDPdntcQ',
                subscriberCount: 100000000,
                videoCount: 5000,
                viewCount: 50000000000,
                averageCredibilityScore: 75.2,
                totalAnalyses: 1
            },
            {
                channelId: 'sample_channel_id',
                channelName: 'Sample Channel',
                channelUrl: 'https://www.youtube.com/channel/sample_channel_id',
                subscriberCount: 10000,
                videoCount: 50,
                viewCount: 500000,
                averageCredibilityScore: 35.2,
                totalAnalyses: 1
            }
        ];
        
        // 채널 데이터 삽입
        for (const channel of sampleChannels) {
            await prisma.channel.upsert({
                where: { channelId: channel.channelId },
                update: channel,
                create: channel
            });
        }
        
        // 샘플 분석 결과 데이터
        const sampleAnalyses = [
            {
                videoId: 'dQw4w9WgXcQ',
                videoUrl: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                channelId: 'UC_x5XG1OV2P6uZZ5FSM9Ttw',
                channelName: 'Google Developers',
                videoTitle: 'Sample High Credibility Video',
                credibilityScore: 85.5,
                credibilityGrade: 'A',
                biasScore: 15.2,
                factCheckScore: 92.1,
                sourceScore: 88.7,
                sentimentScore: 45.3,
                analysisBreakdown: {
                    sentiment: { score: 45.3, details: 'Neutral tone' },
                    bias: { score: 15.2, details: 'Low bias detected' },
                    factCheck: { score: 92.1, details: 'Most claims verified' },
                    source: { score: 88.7, details: 'Reliable sources cited' }
                },
                explanation: 'This video demonstrates high credibility with verified sources and factual content.',
                confidenceScore: 87.2,
                processingTimeMs: 2500,
                modelVersion: '1.0.0'
            },
            {
                videoId: 'sample_low_credibility',
                videoUrl: 'https://www.youtube.com/watch?v=sample_low_credibility',
                channelId: 'sample_channel_id',
                channelName: 'Sample Channel',
                videoTitle: 'Sample Low Credibility Video',
                credibilityScore: 35.2,
                credibilityGrade: 'D',
                biasScore: 78.5,
                factCheckScore: 25.1,
                sourceScore: 30.8,
                sentimentScore: 85.2,
                analysisBreakdown: {
                    sentiment: { score: 85.2, details: 'Highly emotional' },
                    bias: { score: 78.5, details: 'Strong bias detected' },
                    factCheck: { score: 25.1, details: 'Many unverified claims' },
                    source: { score: 30.8, details: 'Unreliable sources' }
                },
                explanation: 'This video shows signs of bias and contains unverified claims.',
                confidenceScore: 72.1,
                processingTimeMs: 2800,
                modelVersion: '1.0.0'
            },
            {
                videoId: 'UCBR8-60-B28hp2BmDPdntcQ_sample',
                videoUrl: 'https://www.youtube.com/watch?v=UCBR8-60-B28hp2BmDPdntcQ_sample',
                channelId: 'UCBR8-60-B28hp2BmDPdntcQ',
                channelName: 'YouTube',
                videoTitle: 'Sample Medium Credibility Video',
                credibilityScore: 65.8,
                credibilityGrade: 'C',
                biasScore: 45.2,
                factCheckScore: 68.5,
                sourceScore: 72.1,
                sentimentScore: 55.3,
                analysisBreakdown: {
                    sentiment: { score: 55.3, details: 'Moderate emotional content' },
                    bias: { score: 45.2, details: 'Some bias detected' },
                    factCheck: { score: 68.5, details: 'Mixed verification results' },
                    source: { score: 72.1, details: 'Some reliable sources' }
                },
                explanation: 'This video has mixed credibility with some verified claims but also some bias.',
                confidenceScore: 68.9,
                processingTimeMs: 2600,
                modelVersion: '1.0.0'
            }
        ];
        
        // 분석 결과 데이터 삽입
        for (const analysis of sampleAnalyses) {
            await prisma.analysisResult.create({
                data: analysis
            });
        }
        
        // 샘플 피드백 데이터
        const sampleFeedbacks = [
            {
                analysisResultId: 1, // 첫 번째 분석 결과에 대한 피드백
                userId: 'user123',
                sessionId: 'session456',
                feedbackType: 'accurate',
                feedbackText: '분석 결과가 정확합니다.',
                feedbackScore: 5
            },
            {
                analysisResultId: 1,
                userId: 'user456',
                sessionId: 'session789',
                feedbackType: 'helpful',
                feedbackText: '도움이 되었습니다.',
                feedbackScore: 4
            },
            {
                analysisResultId: 2, // 두 번째 분석 결과에 대한 피드백
                userId: 'user789',
                sessionId: 'session123',
                feedbackType: 'inaccurate',
                feedbackText: '분석 결과가 부정확합니다.',
                feedbackScore: 2
            }
        ];
        
        // 피드백 데이터 삽입
        for (const feedback of sampleFeedbacks) {
            await prisma.userFeedback.create({
                data: feedback
            });
        }
        
        console.log('Seed data inserted successfully!');
        console.log(`- ${sampleChannels.length} channels created`);
        console.log(`- ${sampleAnalyses.length} analysis results created`);
        console.log(`- ${sampleFeedbacks.length} feedback entries created`);
        
    } catch (error) {
        console.error('Error seeding data:', error);
        throw error;
    } finally {
        await prisma.$disconnect();
    }
}

// 스크립트가 직접 실행될 때만 실행
if (require.main === module) {
    seedData()
        .then(() => {
            console.log('Seeding completed successfully');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Seeding failed:', error);
            process.exit(1);
        });
}

module.exports = { seedData }; 