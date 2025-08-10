"""
데이터베이스 연결 관리
PostgreSQL 및 Redis 연결 설정 및 관리
"""

import os
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
from contextlib import asynccontextmanager

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy 설정
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # 디버그 모드에서만 SQL 로그 출력
    poolclass=NullPool,   # 개발 환경용 (프로덕션에서는 Pool 사용 권장)
    future=True
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis 클라이언트
redis_client: Optional[redis.Redis] = None

async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"데이터베이스 세션 오류: {e}")
            raise
        finally:
            await session.close()

async def get_redis() -> redis.Redis:
    """Redis 클라이언트 반환"""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 연결 테스트
            await redis_client.ping()
            logger.info("Redis 연결 성공")
            
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            # Redis 연결 실패 시 None 반환 (선택적 의존성)
            return None
    
    return redis_client

async def close_redis():
    """Redis 연결 종료"""
    global redis_client
    
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis 연결 종료")

async def init_database():
    """데이터베이스 초기화"""
    try:
        # 데이터베이스 연결 테스트
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
        
        logger.info("PostgreSQL 연결 성공")
        
        # 테이블 생성
        from .models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("데이터베이스 테이블 생성 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

async def close_database():
    """데이터베이스 연결 종료"""
    await engine.dispose()
    await close_redis()
    logger.info("데이터베이스 연결 종료")

@asynccontextmanager
async def get_db_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()

# 연결 상태 확인 함수들
async def check_database_health() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 상태 확인 실패: {e}")
        return False

async def check_redis_health() -> bool:
    """Redis 연결 상태 확인"""
    try:
        redis_client = await get_redis()
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Redis 상태 확인 실패: {e}")
        return False

async def get_database_stats() -> dict:
    """데이터베이스 통계 정보 반환"""
    try:
        # PostgreSQL 통계
        async with engine.begin() as conn:
            # 테이블 개수
            result = await conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = result.scalar()
            
            # 연결 수
            result = await conn.execute("SELECT COUNT(*) FROM pg_stat_activity")
            connection_count = result.scalar()
        
        # Redis 통계
        redis_stats = {}
        redis_client = await get_redis()
        if redis_client:
            try:
                info = await redis_client.info()
                redis_stats = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            except Exception:
                pass
        
        return {
            "postgresql": {
                "status": "connected",
                "table_count": table_count,
                "connection_count": connection_count
            },
            "redis": {
                "status": "connected" if redis_stats else "disconnected",
                **redis_stats
            }
        }
        
    except Exception as e:
        logger.error(f"데이터베이스 통계 조회 실패: {e}")
        return {
            "postgresql": {"status": "error", "error": str(e)},
            "redis": {"status": "error", "error": str(e)}
        }
