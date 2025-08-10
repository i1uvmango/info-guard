"""
데이터베이스 마이그레이션 스크립트
테이블 생성 및 초기 데이터 설정
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import AsyncSessionLocal, init_database
from .models import Base, User, AnalysisResult, Feedback, VideoMetadata, AnalysisCache, SystemMetrics
from utils.logger import get_logger

logger = get_logger(__name__)

async def create_tables():
    """모든 테이블 생성"""
    try:
        async with AsyncSessionLocal() as session:
            # 테이블 생성
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            await session.run_sync(Base.metadata.create_all)
            await session.commit()
            
            logger.info("데이터베이스 테이블 생성 완료")
            
    except Exception as e:
        logger.error(f"테이블 생성 실패: {e}")
        raise

async def drop_tables():
    """모든 테이블 삭제 (개발용)"""
    try:
        async with AsyncSessionLocal() as session:
            await session.run_sync(Base.metadata.drop_all)
            await session.commit()
            
            logger.info("데이터베이스 테이블 삭제 완료")
            
    except Exception as e:
        logger.error(f"테이블 삭제 실패: {e}")
        raise

async def create_indexes():
    """성능 향상을 위한 인덱스 생성"""
    try:
        async with AsyncSessionLocal() as session:
            # 복합 인덱스들
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analysis_video_created 
                ON analysis_results (video_id, created_at DESC)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analysis_user_created 
                ON analysis_results (user_id, created_at DESC)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analysis_credibility_created 
                ON analysis_results (overall_credibility_score DESC, created_at DESC)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_feedback_analysis_created 
                ON feedbacks (analysis_id, created_at DESC)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_metadata_expires 
                ON video_metadata (cache_expires_at)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires 
                ON analysis_cache (expires_at)
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp 
                ON system_metrics (timestamp DESC)
            """))
            
            await session.commit()
            logger.info("데이터베이스 인덱스 생성 완료")
            
    except Exception as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

async def create_initial_data():
    """초기 데이터 생성"""
    try:
        async with AsyncSessionLocal() as session:
            # 시스템 메트릭 초기화
            initial_metrics = SystemMetrics(
                request_count=0,
                average_response_time=0.0,
                error_count=0,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                model_inference_count=0,
                model_inference_time=0.0,
                db_connection_count=0,
                db_query_count=0
            )
            
            session.add(initial_metrics)
            await session.commit()
            
            logger.info("초기 데이터 생성 완료")
            
    except Exception as e:
        logger.error(f"초기 데이터 생성 실패: {e}")
        raise

async def run_migrations():
    """전체 마이그레이션 실행"""
    try:
        logger.info("데이터베이스 마이그레이션 시작")
        
        # 데이터베이스 초기화
        await init_database()
        
        # 테이블 생성
        await create_tables()
        
        # 인덱스 생성
        await create_indexes()
        
        # 초기 데이터 생성
        await create_initial_data()
        
        logger.info("데이터베이스 마이그레이션 완료")
        
    except Exception as e:
        logger.error(f"마이그레이션 실패: {e}")
        raise

async def reset_database():
    """데이터베이스 초기화 (개발용)"""
    try:
        logger.info("데이터베이스 초기화 시작")
        
        # 테이블 삭제
        await drop_tables()
        
        # 테이블 재생성
        await create_tables()
        
        # 인덱스 생성
        await create_indexes()
        
        # 초기 데이터 생성
        await create_initial_data()
        
        logger.info("데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

async def check_database_schema():
    """데이터베이스 스키마 상태 확인"""
    try:
        async with AsyncSessionLocal() as session:
            # 테이블 목록 조회
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            # 각 테이블의 레코드 수 조회
            table_counts = {}
            for table in tables:
                count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                table_counts[table] = count
            
            logger.info("데이터베이스 스키마 상태:")
            for table, count in table_counts.items():
                logger.info(f"  {table}: {count} 레코드")
            
            return {
                "tables": tables,
                "table_counts": table_counts
            }
            
    except Exception as e:
        logger.error(f"스키마 상태 확인 실패: {e}")
        return None

async def create_sample_data():
    """샘플 데이터 생성 (테스트용)"""
    try:
        async with AsyncSessionLocal() as session:
            # 샘플 사용자 생성
            sample_user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="hashed_password_here",
                full_name="테스트 사용자"
            )
            session.add(sample_user)
            await session.commit()
            await session.refresh(sample_user)
            
            # 샘플 분석 결과 생성
            sample_analysis = AnalysisResult(
                analysis_id="sample_analysis_001",
                user_id=sample_user.id,
                video_id="dQw4w9WgXcQ",
                video_title="샘플 영상 제목",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                channel_id="UC_sample",
                channel_name="샘플 채널",
                analysis_types=["sentiment", "bias", "credibility"],
                include_comments=True,
                include_subtitles=True,
                results={
                    "sentiment": {"label": "positive", "confidence": 0.8},
                    "bias": {"label": "low_bias", "confidence": 0.7},
                    "credibility": {"label": "reliable", "confidence": 0.8}
                },
                confidence_scores={
                    "sentiment": 0.8,
                    "bias": 0.7,
                    "credibility": 0.8
                },
                overall_credibility_score=0.77,
                analysis_time_seconds=15.5,
                status="completed"
            )
            session.add(sample_analysis)
            await session.commit()
            
            logger.info("샘플 데이터 생성 완료")
            
    except Exception as e:
        logger.error(f"샘플 데이터 생성 실패: {e}")
        raise

if __name__ == "__main__":
    # CLI에서 직접 실행할 때
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            asyncio.run(run_migrations())
        elif command == "reset":
            asyncio.run(reset_database())
        elif command == "check":
            asyncio.run(check_database_schema())
        elif command == "sample":
            asyncio.run(create_sample_data())
        else:
            print("사용법: python migrations.py [migrate|reset|check|sample]")
    else:
        # 기본 마이그레이션 실행
        asyncio.run(run_migrations())
