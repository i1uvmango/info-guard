const { PrismaClient } = require('@prisma/client');
const db = require('./connection');
const { seedData } = require('./seeds/seedData');

const prisma = new PrismaClient();

async function initializeDatabase() {
    try {
        console.log('🔧 Initializing Info-Guard database...');
        
        // 1. 데이터베이스 연결 확인
        console.log('📡 Testing database connection...');
        await db.connect();
        console.log('✅ Database connection established');
        
        // 2. Prisma 클라이언트 생성
        console.log('🔨 Generating Prisma client...');
        await prisma.$connect();
        console.log('✅ Prisma client generated');
        
        // 3. 데이터베이스 스키마 동기화
        console.log('🔄 Syncing database schema...');
        await prisma.$executeRaw`SELECT 1`;
        console.log('✅ Database schema synced');
        
        // 4. 시드 데이터 삽입
        console.log('🌱 Inserting seed data...');
        await seedData();
        console.log('✅ Seed data inserted');
        
        // 5. 초기 통계 확인
        console.log('📊 Checking initial statistics...');
        const analysisCount = await prisma.analysisResult.count();
        const channelCount = await prisma.channel.count();
        const feedbackCount = await prisma.userFeedback.count();
        
        console.log(`📈 Initial statistics:`);
        console.log(`   - Analysis Results: ${analysisCount}`);
        console.log(`   - Channels: ${channelCount}`);
        console.log(`   - User Feedbacks: ${feedbackCount}`);
        
        console.log('🎉 Database initialization completed successfully!');
        
    } catch (error) {
        console.error('❌ Database initialization failed:', error);
        throw error;
    } finally {
        await prisma.$disconnect();
        await db.disconnect();
    }
}

// 스크립트가 직접 실행될 때만 실행
if (require.main === module) {
    initializeDatabase()
        .then(() => {
            console.log('✅ Database initialization completed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('❌ Database initialization failed:', error);
            process.exit(1);
        });
}

module.exports = { initializeDatabase }; 