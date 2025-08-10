"""
데이터베이스 서비스
CRUD 작업 및 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import json

from .models import (
    Base, User, AnalysisResult, Feedback, VideoMetadata, 
    AnalysisCache, SystemMetrics
)
from utils.logger import get_logger

logger = get_logger(__name__)

class UserService:
    """사용자 관련 서비스"""
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None
    ) -> User:
        """새 사용자 생성"""
        try:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"새 사용자 생성: {username}")
            return user
            
        except Exception as e:
            await session.rollback()
            logger.error(f"사용자 생성 실패: {e}")
            raise
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        try:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"사용자 조회 실패: {e}")
            return None
    
    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        try:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"사용자명으로 사용자 조회 실패: {e}")
            return None
    
    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        try:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"이메일로 사용자 조회 실패: {e}")
            return None
    
    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """사용자 정보 업데이트"""
        try:
            result = await session.execute(
                update(User)
                .where(User.id == user_id)
                .values(**kwargs, updated_at=datetime.now())
                .returning(User)
            )
            user = result.scalar_one_or_none()
            if user:
                await session.commit()
                logger.info(f"사용자 정보 업데이트: {user_id}")
            return user
            
        except Exception as e:
            await session.rollback()
            logger.error(f"사용자 정보 업데이트 실패: {e}")
            return None

class AnalysisService:
    """분석 결과 관련 서비스"""
    
    @staticmethod
    async def create_analysis_result(
        session: AsyncSession,
        analysis_id: str,
        video_id: str,
        video_title: str,
        video_url: str,
        analysis_types: List[str],
        results: Dict[str, Any],
        confidence_scores: Dict[str, float],
        overall_credibility_score: float,
        analysis_time_seconds: float,
        user_id: Optional[int] = None,
        channel_id: Optional[str] = None,
        channel_name: Optional[str] = None,
        include_comments: bool = True,
        include_subtitles: bool = True
    ) -> AnalysisResult:
        """새 분석 결과 생성"""
        try:
            analysis_result = AnalysisResult(
                analysis_id=analysis_id,
                user_id=user_id,
                video_id=video_id,
                video_title=video_title,
                video_url=video_url,
                channel_id=channel_id,
                channel_name=channel_name,
                analysis_types=analysis_types,
                include_comments=include_comments,
                include_subtitles=include_subtitles,
                results=results,
                confidence_scores=confidence_scores,
                overall_credibility_score=overall_credibility_score,
                analysis_time_seconds=analysis_time_seconds,
                status="completed"
            )
            
            session.add(analysis_result)
            await session.commit()
            await session.refresh(analysis_result)
            
            logger.info(f"분석 결과 생성: {analysis_id}")
            return analysis_result
            
        except Exception as e:
            await session.rollback()
            logger.error(f"분석 결과 생성 실패: {e}")
            raise
    
    @staticmethod
    async def get_analysis_by_id(
        session: AsyncSession,
        analysis_id: str
    ) -> Optional[AnalysisResult]:
        """분석 ID로 결과 조회"""
        try:
            result = await session.execute(
                select(AnalysisResult)
                .where(AnalysisResult.analysis_id == analysis_id)
                .options(selectinload(AnalysisResult.user))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"분석 결과 조회 실패: {e}")
            return None
    
    @staticmethod
    async def get_analysis_by_video_id(
        session: AsyncSession,
        video_id: str,
        limit: int = 10
    ) -> List[AnalysisResult]:
        """비디오 ID로 분석 결과 조회"""
        try:
            result = await session.execute(
                select(AnalysisResult)
                .where(AnalysisResult.video_id == video_id)
                .order_by(desc(AnalysisResult.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"비디오별 분석 결과 조회 실패: {e}")
            return []
    
    @staticmethod
    async def get_user_analyses(
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[AnalysisResult]:
        """사용자의 분석 결과 조회"""
        try:
            result = await session.execute(
                select(AnalysisResult)
                .where(AnalysisResult.user_id == user_id)
                .order_by(desc(AnalysisResult.created_at))
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"사용자 분석 결과 조회 실패: {e}")
            return []
    
    @staticmethod
    async def update_analysis_status(
        session: AsyncSession,
        analysis_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """분석 상태 업데이트"""
        try:
            result = await session.execute(
                update(AnalysisResult)
                .where(AnalysisResult.analysis_id == analysis_id)
                .values(
                    status=status,
                    error_message=error_message,
                    updated_at=datetime.now()
                )
            )
            await session.commit()
            
            logger.info(f"분석 상태 업데이트: {analysis_id} -> {status}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"분석 상태 업데이트 실패: {e}")
            return False
    
    @staticmethod
    async def get_analysis_statistics(
        session: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """분석 통계 조회"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 총 분석 수
            total_result = await session.execute(
                select(func.count(AnalysisResult.id))
                .where(AnalysisResult.created_at >= start_date)
            )
            total_analyses = total_result.scalar()
            
            # 상태별 분석 수
            status_result = await session.execute(
                select(
                    AnalysisResult.status,
                    func.count(AnalysisResult.id)
                )
                .where(AnalysisResult.created_at >= start_date)
                .group_by(AnalysisResult.status)
            )
            status_counts = dict(status_result.all())
            
            # 평균 신뢰도 점수
            avg_score_result = await session.execute(
                select(func.avg(AnalysisResult.overall_credibility_score))
                .where(
                    and_(
                        AnalysisResult.created_at >= start_date,
                        AnalysisResult.status == "completed"
                    )
                )
            )
            avg_credibility_score = avg_score_result.scalar() or 0.0
            
            # 분석 타입별 통계
            type_stats = {}
            for analysis_type in ["sentiment", "bias", "credibility", "content"]:
                type_result = await session.execute(
                    select(func.count(AnalysisResult.id))
                    .where(
                        and_(
                            AnalysisResult.created_at >= start_date,
                            AnalysisResult.analysis_types.contains([analysis_type])
                        )
                    )
                )
                type_stats[analysis_type] = type_result.scalar()
            
            return {
                "total_analyses": total_analyses,
                "status_counts": status_counts,
                "average_credibility_score": round(avg_credibility_score, 3),
                "analysis_type_counts": type_stats,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"분석 통계 조회 실패: {e}")
            return {}

class FeedbackService:
    """피드백 관련 서비스"""
    
    @staticmethod
    async def create_feedback(
        session: AsyncSession,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        user_id: Optional[int] = None,
        analysis_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Feedback:
        """새 피드백 생성"""
        try:
            feedback = Feedback(
                user_id=user_id,
                analysis_id=analysis_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)
            
            logger.info(f"새 피드백 생성: {feedback_type}")
            return feedback
            
        except Exception as e:
            await session.rollback()
            logger.error(f"피드백 생성 실패: {e}")
            raise
    
    @staticmethod
    async def get_feedback_by_analysis(
        session: AsyncSession,
        analysis_id: int
    ) -> List[Feedback]:
        """분석별 피드백 조회"""
        try:
            result = await session.execute(
                select(Feedback)
                .where(Feedback.analysis_id == analysis_id)
                .order_by(desc(Feedback.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"분석별 피드백 조회 실패: {e}")
            return []

class CacheService:
    """캐시 관련 서비스"""
    
    @staticmethod
    async def set_video_metadata(
        session: AsyncSession,
        video_id: str,
        metadata: Dict[str, Any],
        expire_hours: int = 24
    ) -> VideoMetadata:
        """비디오 메타데이터 캐시 설정"""
        try:
            # 기존 캐시 확인
            existing = await session.execute(
                select(VideoMetadata).where(VideoMetadata.video_id == video_id)
            )
            existing_cache = existing.scalar_one_or_none()
            
            if existing_cache:
                # 기존 캐시 업데이트
                existing_cache.title = metadata.get("title", "")
                existing_cache.description = metadata.get("description", "")
                existing_cache.channel_id = metadata.get("channel_id", "")
                existing_cache.channel_name = metadata.get("channel_name", "")
                existing_cache.view_count = metadata.get("view_count", 0)
                existing_cache.like_count = metadata.get("like_count", 0)
                existing_cache.comment_count = metadata.get("comment_count", 0)
                existing_cache.subscriber_count = metadata.get("subscriber_count", 0)
                existing_cache.duration = metadata.get("duration", "")
                existing_cache.published_at = metadata.get("published_at")
                existing_cache.tags = metadata.get("tags", [])
                existing_cache.category_id = metadata.get("category_id", "")
                existing_cache.last_updated = datetime.now()
                existing_cache.cache_expires_at = datetime.now() + timedelta(hours=expire_hours)
                
                await session.commit()
                await session.refresh(existing_cache)
                return existing_cache
            else:
                # 새 캐시 생성
                new_cache = VideoMetadata(
                    video_id=video_id,
                    title=metadata.get("title", ""),
                    description=metadata.get("description", ""),
                    channel_id=metadata.get("channel_id", ""),
                    channel_name=metadata.get("channel_name", ""),
                    view_count=metadata.get("view_count", 0),
                    like_count=metadata.get("like_count", 0),
                    comment_count=metadata.get("comment_count", 0),
                    subscriber_count=metadata.get("subscriber_count", 0),
                    duration=metadata.get("duration", ""),
                    published_at=metadata.get("published_at"),
                    tags=metadata.get("tags", []),
                    category_id=metadata.get("category_id", ""),
                    cache_expires_at=datetime.now() + timedelta(hours=expire_hours)
                )
                
                session.add(new_cache)
                await session.commit()
                await session.refresh(new_cache)
                return new_cache
                
        except Exception as e:
            await session.rollback()
            logger.error(f"비디오 메타데이터 캐시 설정 실패: {e}")
            raise
    
    @staticmethod
    async def get_video_metadata(
        session: AsyncSession,
        video_id: str
    ) -> Optional[VideoMetadata]:
        """비디오 메타데이터 캐시 조회"""
        try:
            result = await session.execute(
                select(VideoMetadata)
                .where(
                    and_(
                        VideoMetadata.video_id == video_id,
                        VideoMetadata.cache_expires_at > datetime.now()
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"비디오 메타데이터 캐시 조회 실패: {e}")
            return None
    
    @staticmethod
    async def set_analysis_cache(
        session: AsyncSession,
        cache_key: str,
        cached_data: Dict[str, Any],
        cache_type: str,
        video_id: Optional[str] = None,
        expire_hours: int = 6
    ) -> AnalysisCache:
        """분석 결과 캐시 설정"""
        try:
            # 기존 캐시 확인
            existing = await session.execute(
                select(AnalysisCache).where(AnalysisCache.cache_key == cache_key)
            )
            existing_cache = existing.scalar_one_or_none()
            
            if existing_cache:
                # 기존 캐시 업데이트
                existing_cache.cached_data = cached_data
                existing_cache.expires_at = datetime.now() + timedelta(hours=expire_hours)
                existing_cache.last_accessed = datetime.now()
                
                await session.commit()
                await session.refresh(existing_cache)
                return existing_cache
            else:
                # 새 캐시 생성
                new_cache = AnalysisCache(
                    cache_key=cache_key,
                    cached_data=cached_data,
                    cache_type=cache_type,
                    video_id=video_id,
                    expires_at=datetime.now() + timedelta(hours=expire_hours)
                )
                
                session.add(new_cache)
                await session.commit()
                await session.refresh(new_cache)
                return new_cache
                
        except Exception as e:
            await session.rollback()
            logger.error(f"분석 결과 캐시 설정 실패: {e}")
            raise
    
    @staticmethod
    async def get_analysis_cache(
        session: AsyncSession,
        cache_key: str
    ) -> Optional[AnalysisCache]:
        """분석 결과 캐시 조회"""
        try:
            result = await session.execute(
                select(AnalysisCache)
                .where(
                    and_(
                        AnalysisCache.cache_key == cache_key,
                        AnalysisCache.expires_at > datetime.now()
                    )
                )
            )
            cache = result.scalar_one_or_none()
            
            if cache:
                # 접근 통계 업데이트
                cache.hit_count += 1
                cache.last_accessed = datetime.now()
                await session.commit()
            
            return cache
        except Exception as e:
            logger.error(f"분석 결과 캐시 조회 실패: {e}")
            return None
    
    @staticmethod
    async def cleanup_expired_cache(session: AsyncSession) -> int:
        """만료된 캐시 정리"""
        try:
            # 만료된 비디오 메타데이터 캐시 삭제
            video_result = await session.execute(
                delete(VideoMetadata)
                .where(VideoMetadata.cache_expires_at <= datetime.now())
            )
            video_deleted = video_result.rowcount
            
            # 만료된 분석 결과 캐시 삭제
            analysis_result = await session.execute(
                delete(AnalysisCache)
                .where(AnalysisCache.expires_at <= datetime.now())
            )
            analysis_deleted = analysis_result.rowcount
            
            await session.commit()
            
            total_deleted = video_deleted + analysis_deleted
            logger.info(f"만료된 캐시 정리 완료: {total_deleted}개")
            return total_deleted
            
        except Exception as e:
            await session.rollback()
            logger.error(f"캐시 정리 실패: {e}")
            return 0
