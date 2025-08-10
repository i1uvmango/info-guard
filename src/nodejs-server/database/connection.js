const { PrismaClient } = require('@prisma/client');
const Redis = require('ioredis');

class DatabaseManager {
    constructor() {
        this.prisma = new PrismaClient({
            log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
        });
        
        this.redis = new Redis({
            host: process.env.REDIS_HOST || 'localhost',
            port: process.env.REDIS_PORT || 6379,
            password: process.env.REDIS_PASSWORD,
            retryDelayOnFailover: 100,
            maxRetriesPerRequest: 3,
        });
        
        this.redis.on('error', (err) => {
            console.error('Redis connection error:', err);
        });
    }
    
    async connect() {
        try {
            await this.prisma.$connect();
            await this.redis.ping();
            console.log('Database connections established');
        } catch (error) {
            console.error('Database connection failed:', error);
            throw error;
        }
    }
    
    async disconnect() {
        await this.prisma.$disconnect();
        await this.redis.quit();
    }
    
    async healthCheck() {
        try {
            await this.prisma.$queryRaw`SELECT 1`;
            await this.redis.ping();
            return { status: 'healthy', timestamp: new Date() };
        } catch (error) {
            return { status: 'unhealthy', error: error.message, timestamp: new Date() };
        }
    }
}

module.exports = new DatabaseManager(); 