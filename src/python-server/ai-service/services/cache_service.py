"""
캐싱 서비스
Redis를 활용한 분석 결과 캐싱 및 성능 최적화
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import redis
from config.logging_config import get_logger

logger = get_logger(__name__)

class CacheService:
    """
    캐싱 서비스
    Redis를 활용한 분석 결과 캐싱 및 성능 최적화
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = 3600  # 1시간
        self.logger = logger
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """캐시 키 생성"""
        return f"{prefix}:{identifier}"
    
    def _generate_hash_key(self, data: Dict[str, Any]) -> str:
        """데이터 해시 키 생성"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def get_analysis_result(self, video_id: str) -> Optional[Dict[str, Any]]:
        """분석 결과 캐시에서 조회"""
        try:
            cache_key = self._generate_cache_key("analysis", video_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                self.logger.info(f"캐시에서 분석 결과 조회: {video_id}")
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"캐시 조회 실패: {video_id}, 오류: {e}")
            return None
    
    async def set_analysis_result(self, video_id: str, result: Dict[str, Any], ttl: int = None) -> bool:
        """분석 결과 캐시에 저장"""
        try:
            cache_key = self._generate_cache_key("analysis", video_id)
            ttl = ttl or self.default_ttl
            
            # 캐시 데이터에 메타데이터 추가
            cache_data = {
                "result": result,
                "cached_at": datetime.utcnow().isoformat(),
                "video_id": video_id,
                "ttl": ttl
            }
            
            self.redis_client.setex(cache_key, ttl, json.dumps(cache_data))
            self.logger.info(f"분석 결과 캐시 저장: {video_id}, TTL: {ttl}초")
            return True
            
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {video_id}, 오류: {e}")
            return False
    
    async def get_channel_stats(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """채널 통계 캐시에서 조회"""
        try:
            cache_key = self._generate_cache_key("channel_stats", channel_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                self.logger.info(f"캐시에서 채널 통계 조회: {channel_id}")
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"캐시 조회 실패: {channel_id}, 오류: {e}")
            return None
    
    async def set_channel_stats(self, channel_id: str, stats: Dict[str, Any], ttl: int = None) -> bool:
        """채널 통계 캐시에 저장"""
        try:
            cache_key = self._generate_cache_key("channel_stats", channel_id)
            ttl = ttl or self.default_ttl
            
            cache_data = {
                "stats": stats,
                "cached_at": datetime.utcnow().isoformat(),
                "channel_id": channel_id,
                "ttl": ttl
            }
            
            self.redis_client.setex(cache_key, ttl, json.dumps(cache_data))
            self.logger.info(f"채널 통계 캐시 저장: {channel_id}, TTL: {ttl}초")
            return True
            
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {channel_id}, 오류: {e}")
            return False
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """리포트 캐시에서 조회"""
        try:
            cache_key = self._generate_cache_key("report", report_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data)
                self.logger.info(f"캐시에서 리포트 조회: {report_id}")
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"캐시 조회 실패: {report_id}, 오류: {e}")
            return None
    
    async def set_report(self, report_id: str, report: Dict[str, Any], ttl: int = None) -> bool:
        """리포트 캐시에 저장"""
        try:
            cache_key = self._generate_cache_key("report", report_id)
            ttl = ttl or self.default_ttl
            
            cache_data = {
                "report": report,
                "cached_at": datetime.utcnow().isoformat(),
                "report_id": report_id,
                "ttl": ttl
            }
            
            self.redis_client.setex(cache_key, ttl, json.dumps(cache_data))
            self.logger.info(f"리포트 캐시 저장: {report_id}, TTL: {ttl}초")
            return True
            
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {report_id}, 오류: {e}")
            return False
    
    async def invalidate_cache(self, pattern: str) -> bool:
        """패턴에 맞는 캐시 무효화"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                self.logger.info(f"캐시 무효화: {pattern}, 삭제된 키 수: {len(keys)}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"캐시 무효화 실패: {pattern}, 오류: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            stats = {
                "total_keys": self.redis_client.dbsize(),
                "memory_usage": self.redis_client.info("memory"),
                "cache_hits": 0,
                "cache_misses": 0
            }
            
            # 캐시 히트/미스 통계 (Redis INFO에서 가져오기)
            info = self.redis_client.info()
            if "keyspace" in info:
                stats["cache_hits"] = info.get("keyspace", {}).get("hits", 0)
                stats["cache_misses"] = info.get("keyspace", {}).get("misses", 0)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"캐시 통계 조회 실패: {e}")
            return {"error": str(e)}
    
    async def clear_all_cache(self) -> bool:
        """모든 캐시 삭제"""
        try:
            self.redis_client.flushdb()
            self.logger.info("모든 캐시가 삭제되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"캐시 삭제 실패: {e}")
            return False
    
    async def set_with_compression(self, key: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """압축을 사용한 캐시 저장"""
        try:
            import gzip
            
            # 데이터 압축
            data_str = json.dumps(data)
            compressed_data = gzip.compress(data_str.encode())
            
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, compressed_data)
            
            self.logger.info(f"압축된 데이터 캐시 저장: {key}, 크기: {len(compressed_data)} bytes")
            return True
            
        except Exception as e:
            self.logger.error(f"압축 캐시 저장 실패: {key}, 오류: {e}")
            return False
    
    async def get_with_compression(self, key: str) -> Optional[Dict[str, Any]]:
        """압축된 캐시 데이터 조회"""
        try:
            import gzip
            
            compressed_data = self.redis_client.get(key)
            if compressed_data:
                # 데이터 압축 해제
                decompressed_data = gzip.decompress(compressed_data)
                result = json.loads(decompressed_data.decode())
                
                self.logger.info(f"압축된 데이터 캐시 조회: {key}")
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"압축 캐시 조회 실패: {key}, 오류: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """캐시 서비스 헬스 체크"""
        try:
            # Redis 연결 테스트
            self.redis_client.ping()
            
            # 기본 통계 조회
            stats = await self.get_cache_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "cache_stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"캐시 서비스 헬스 체크 실패: {e}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# 전역 캐시 서비스 인스턴스
cache_service = CacheService() 