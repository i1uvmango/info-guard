"""
캐시 서비스
Redis를 사용하여 데이터 캐싱을 담당합니다.
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import redis.asyncio as redis
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
    """Redis 기반 캐시 서비스"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1시간 기본 TTL
        
    async def connect(self):
        """Redis 연결 설정"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # 바이너리 데이터 지원
                max_connections=20
            )
            await self.redis_client.ping()
            logger.info("Redis 캐시 서비스 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis 캐시 서비스 연결 해제")
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                # pickle로 직렬화된 데이터 복원
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"캐시 조회 실패 (키: {key}): {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 데이터 저장"""
        if not self.redis_client:
            return False
        
        try:
            # pickle로 직렬화
            serialized_data = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            
            await self.redis_client.setex(key, ttl, serialized_data)
            logger.debug(f"캐시 저장 성공 (키: {key}, TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"캐시 저장 실패 (키: {key}): {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            if result:
                logger.debug(f"캐시 삭제 성공 (키: {key})")
            return bool(result)
        except Exception as e:
            logger.error(f"캐시 삭제 실패 (키: {key}): {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        if not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"키 존재 확인 실패 (키: {key}): {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """키의 TTL 설정"""
        if not self.redis_client:
            return False
        
        try:
            return bool(await self.redis_client.expire(key, ttl))
        except Exception as e:
            logger.error(f"TTL 설정 실패 (키: {key}): {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """패턴에 맞는 키들을 삭제"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"패턴 '{pattern}'에 맞는 {deleted}개 키 삭제")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"패턴 삭제 실패 (패턴: {pattern}): {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """캐시 통계 정보 조회"""
        if not self.redis_client:
            return {}
        
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}


# 전역 캐시 서비스 인스턴스
cache_service = CacheService()
