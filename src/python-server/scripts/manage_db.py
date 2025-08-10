#!/usr/bin/env python3
"""
데이터베이스 관리 CLI 스크립트
마이그레이션, 백업, 복구 등의 작업을 수행
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.migrations import (
    run_migrations, 
    reset_database, 
    check_database_schema,
    create_sample_data
)
from database.connection import init_database
from utils.logger import get_logger
from utils.config import get_settings

logger = get_logger(__name__)

async def run_alembic_migration():
    """Alembic을 사용한 마이그레이션 실행"""
    try:
        import subprocess
        import shutil
        
        # alembic 명령어 확인
        if not shutil.which('alembic'):
            logger.error("alembic이 설치되지 않았습니다. 'pip install alembic'로 설치하세요.")
            return False
        
        # 데이터베이스 디렉토리로 이동
        db_dir = Path(__file__).parent.parent / "database"
        os.chdir(db_dir)
        
        # 마이그레이션 실행
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Alembic 마이그레이션 완료")
            return True
        else:
            logger.error(f"Alembic 마이그레이션 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Alembic 마이그레이션 실행 중 오류: {e}")
        return False

async def backup_database():
    """데이터베이스 백업"""
    try:
        settings = get_settings()
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"infoguard_backup_{timestamp}.sql"
        
        # PostgreSQL 백업 명령어
        import subprocess
        
        cmd = [
            'pg_dump',
            '-h', settings.database_host,
            '-U', settings.database_user,
            '-d', settings.database_name,
            '-f', str(backup_file)
        ]
        
        # 환경변수 설정
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.database_password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"데이터베이스 백업 완료: {backup_file}")
            return True
        else:
            logger.error(f"백업 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"백업 중 오류: {e}")
        return False

async def restore_database(backup_file: str):
    """데이터베이스 복구"""
    try:
        if not os.path.exists(backup_file):
            logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
            return False
        
        settings = get_settings()
        
        # PostgreSQL 복구 명령어
        import subprocess
        
        cmd = [
            'psql',
            '-h', settings.database_host,
            '-U', settings.database_user,
            '-d', settings.database_name,
            '-f', backup_file
        ]
        
        # 환경변수 설정
        env = os.environ.copy()
        env['PGPASSWORD'] = settings.database_password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"데이터베이스 복구 완료: {backup_file}")
            return True
        else:
            logger.error(f"복구 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"복구 중 오류: {e}")
        return False

async def list_backups():
    """백업 파일 목록 조회"""
    try:
        backup_dir = Path("backups")
        if not backup_dir.exists():
            logger.info("백업 디렉토리가 존재하지 않습니다.")
            return
        
        backup_files = list(backup_dir.glob("*.sql"))
        if not backup_files:
            logger.info("백업 파일이 없습니다.")
            return
        
        logger.info("사용 가능한 백업 파일:")
        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            size = backup_file.stat().st_size
            logger.info(f"  {backup_file.name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')} - {size:,} bytes")
            
    except Exception as e:
        logger.error(f"백업 목록 조회 중 오류: {e}")

async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Info-Guard 데이터베이스 관리 도구")
    parser.add_argument('command', choices=[
        'migrate', 'reset', 'check', 'sample', 'alembic',
        'backup', 'restore', 'list-backups', 'init'
    ], help='실행할 명령어')
    parser.add_argument('--backup-file', help='복구할 백업 파일 경로')
    parser.add_argument('--force', action='store_true', help='확인 없이 실행')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'init':
            logger.info("데이터베이스 초기화 중...")
            await init_database()
            logger.info("데이터베이스 초기화 완료")
            
        elif args.command == 'migrate':
            logger.info("기본 마이그레이션 실행 중...")
            await run_migrations()
            logger.info("마이그레이션 완료")
            
        elif args.command == 'alembic':
            logger.info("Alembic 마이그레이션 실행 중...")
            success = await run_alembic_migration()
            if success:
                logger.info("Alembic 마이그레이션 완료")
            else:
                sys.exit(1)
                
        elif args.command == 'reset':
            if not args.force:
                confirm = input("정말로 데이터베이스를 초기화하시겠습니까? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("취소되었습니다.")
                    return
            
            logger.info("데이터베이스 초기화 중...")
            await reset_database()
            logger.info("데이터베이스 초기화 완료")
            
        elif args.command == 'check':
            logger.info("데이터베이스 스키마 상태 확인 중...")
            schema_info = await check_database_schema()
            if schema_info:
                logger.info("스키마 상태 확인 완료")
            else:
                logger.error("스키마 상태 확인 실패")
                
        elif args.command == 'sample':
            logger.info("샘플 데이터 생성 중...")
            await create_sample_data()
            logger.info("샘플 데이터 생성 완료")
            
        elif args.command == 'backup':
            logger.info("데이터베이스 백업 중...")
            success = await backup_database()
            if not success:
                sys.exit(1)
                
        elif args.command == 'restore':
            if not args.backup_file:
                logger.error("--backup-file 옵션이 필요합니다.")
                sys.exit(1)
            
            if not args.force:
                confirm = input(f"정말로 {args.backup_file}에서 복구하시겠습니까? (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("취소되었습니다.")
                    return
            
            logger.info("데이터베이스 복구 중...")
            success = await restore_database(args.backup_file)
            if not success:
                sys.exit(1)
                
        elif args.command == 'list-backups':
            await list_backups()
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
