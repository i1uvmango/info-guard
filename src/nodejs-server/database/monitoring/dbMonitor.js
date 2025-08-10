const db = require('../connection');

class DatabaseMonitor {
    async getDatabaseStats() {
        try {
            const stats = await db.prisma.$queryRaw`
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                ORDER BY tablename, attname;
            `;
            
            return stats;
        } catch (error) {
            console.error('Error getting database stats:', error);
            throw error;
        }
    }
    
    async getTableSizes() {
        try {
            const sizes = await db.prisma.$queryRaw`
                SELECT 
                    table_name,
                    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
                    pg_total_relation_size(quote_ident(table_name)) as size_bytes
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
            `;
            
            return sizes;
        } catch (error) {
            console.error('Error getting table sizes:', error);
            throw error;
        }
    }
    
    async getSlowQueries() {
        try {
            const slowQueries = await db.prisma.$queryRaw`
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE mean_time > 100
                ORDER BY mean_time DESC
                LIMIT 10;
            `;
            
            return slowQueries;
        } catch (error) {
            console.error('Error getting slow queries:', error);
            return [];
        }
    }
    
    async getConnectionStats() {
        try {
            const connections = await db.prisma.$queryRaw`
                SELECT 
                    state,
                    count(*) as count
                FROM pg_stat_activity 
                WHERE datname = current_database()
                GROUP BY state;
            `;
            
            return connections;
        } catch (error) {
            console.error('Error getting connection stats:', error);
            throw error;
        }
    }
    
    async getRedisStats() {
        try {
            const info = await db.redis.info();
            const memory = await db.redis.memory('USAGE');
            const keyspace = await db.redis.info('keyspace');
            
            return {
                info: info.split('\r\n').reduce((acc, line) => {
                    if (line.includes(':')) {
                        const [key, value] = line.split(':');
                        acc[key] = value;
                    }
                    return acc;
                }, {}),
                memory,
                keyspace
            };
        } catch (error) {
            console.error('Error getting Redis stats:', error);
            throw error;
        }
    }
    
    async getSystemHealth() {
        try {
            const [dbHealth, redisHealth] = await Promise.all([
                db.prisma.$queryRaw`SELECT 1 as health`,
                db.redis.ping()
            ]);
            
            return {
                database: dbHealth.length > 0 ? 'healthy' : 'unhealthy',
                redis: redisHealth === 'PONG' ? 'healthy' : 'unhealthy',
                timestamp: new Date()
            };
        } catch (error) {
            console.error('Error checking system health:', error);
            return {
                database: 'unhealthy',
                redis: 'unhealthy',
                error: error.message,
                timestamp: new Date()
            };
        }
    }
    
    async generateReport() {
        try {
            const [health, tableSizes, connectionStats] = await Promise.all([
                this.getSystemHealth(),
                this.getTableSizes(),
                this.getConnectionStats()
            ]);
            
            return {
                health,
                tableSizes,
                connectionStats,
                timestamp: new Date()
            };
        } catch (error) {
            console.error('Error generating report:', error);
            throw error;
        }
    }
}

module.exports = new DatabaseMonitor(); 