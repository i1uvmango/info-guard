#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 시스템 사용 예제
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.migrations import (
    run_migrations,
    reset_database,
    check_database_schema,
    create_sample_data
)
from database.connection import init_database, test_connection
from utils.logger import get_logger

logger = get_logger(__name__)

async def example_basic_migration():
    """기본 마이그레이션 예제"""
    logger.info("=== 기본 마이그레이션 예제 ===")
    
    try:
        # 1. 데이터베이스 초기화
        logger.info("1. 데이터베이스 초기화...")
        await init_database()
        
        # 2. 연결 테스트
        logger.info("2. 데이터베이스 연결 테스트...")
        await test_connection()
        
        # 3. 마이그레이션 실행
        logger.info("3. 마이그레이션 실행...")
        await run_migrations()
        
        # 4. 스키마 상태 확인
        logger.info("4. 스키마 상태 확인...")
        schema_info = await check_database_schema()
        
        if schema_info:
            logger.info("테이블 목록:")
            for table, count in schema_info['table_counts'].items():
                logger.info(f"  {table}: {count} 레코드")
        
        logger.info("기본 마이그레이션 완료!")
        
    except Exception as e:
        logger.error(f"마이그레이션 실패: {e}")
        raise

async def example_sample_data():
    """샘플 데이터 생성 예제"""
    logger.info("=== 샘플 데이터 생성 예제 ===")
    
    try:
        # 샘플 데이터 생성
        await create_sample_data()
        logger.info("샘플 데이터 생성 완료!")
        
        # 업데이트된 스키마 상태 확인
        schema_info = await check_database_schema()
        if schema_info:
            logger.info("샘플 데이터 생성 후 테이블 상태:")
            for table, count in schema_info['table_counts'].items():
                logger.info(f"  {table}: {count} 레코드")
                
    except Exception as e:
        logger.error(f"샘플 데이터 생성 실패: {e}")
        raise

async def example_database_reset():
    """데이터베이스 초기화 예제 (개발용)"""
    logger.info("=== 데이터베이스 초기화 예제 ===")
    
    try:
        # 주의: 이 작업은 모든 데이터를 삭제합니다!
        logger.warning("⚠️  모든 데이터가 삭제됩니다!")
        
        # 사용자 확인 (실제 사용시에는 주석 해제)
        # confirm = input("정말로 데이터베이스를 초기화하시겠습니까? (yes/no): ")
        # if confirm.lower() != 'yes':
        #     logger.info("취소되었습니다.")
        #     return
        
        # 데이터베이스 초기화
        await reset_database()
        logger.info("데이터베이스 초기화 완료!")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

async def example_cli_usage():
    """CLI 도구 사용 예제"""
    logger.info("=== CLI 도구 사용 예제 ===")
    
    logger.info("CLI 도구 사용법:")
    logger.info("")
    logger.info("1. 마이그레이션 실행:")
    logger.info("   python scripts/manage_db.py migrate")
    logger.info("")
    logger.info("2. Alembic 마이그레이션:")
    logger.info("   python scripts/manage_db.py alembic")
    logger.info("")
    logger.info("3. 데이터베이스 상태 확인:")
    logger.info("   python scripts/manage_db.py check")
    logger.info("")
    logger.info("4. 샘플 데이터 생성:")
    logger.info("   python scripts/manage_db.py sample")
    logger.info("")
    logger.info("5. 백업 생성:")
    logger.info("   python scripts/manage_db.py backup")
    logger.info("")
    logger.info("6. 백업 목록 조회:")
    logger.info("   python scripts/manage_db.py list-backups")

async def main():
    """메인 함수"""
    logger.info("Info-Guard 데이터베이스 마이그레이션 시스템 예제")
    logger.info("=" * 50)
    
    try:
        # 1. 기본 마이그레이션 예제
        await example_basic_migration()
        logger.info("")
        
        # 2. 샘플 데이터 생성 예제
        await example_sample_data()
        logger.info("")
        
        # 3. CLI 사용법 예제
        await example_cli_usage()
        logger.info("")
        
        # 4. 데이터베이스 초기화 예제 (주석 처리됨)
        # await example_database_reset()
        
        logger.info("모든 예제 실행 완료!")
        
    except Exception as e:
        logger.error(f"예제 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
