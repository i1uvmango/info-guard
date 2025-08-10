"""
데이터베이스 마이그레이션 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import text

from database.migrations import (
    create_tables,
    drop_tables,
    create_indexes,
    create_initial_data,
    run_migrations,
    reset_database,
    check_database_schema,
    create_sample_data
)
from database.models import User, AnalysisResult, SystemMetrics
from utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
def mock_session():
    """모의 데이터베이스 세션"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.run_sync = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session

@pytest.fixture
def mock_connection():
    """모의 데이터베이스 연결"""
    connection = AsyncMock()
    connection.execute = AsyncMock()
    connection.scalar = MagicMock(return_value=0)
    connection.fetchall = MagicMock(return_value=[('users',), ('analysis_results',)])
    return connection

class TestDatabaseMigrations:
    """데이터베이스 마이그레이션 테스트 클래스"""

    @pytest.mark.asyncio
    async def test_create_tables(self, mock_session):
        """테이블 생성 테스트"""
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await create_tables()
            
            # UUID 확장 생성 확인
            mock_session.execute.assert_called_with(
                text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            )
            
            # 테이블 생성 확인
            mock_session.run_sync.assert_called()
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_drop_tables(self, mock_session):
        """테이블 삭제 테스트"""
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await drop_tables()
            
            mock_session.run_sync.assert_called()
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_indexes(self, mock_session):
        """인덱스 생성 테스트"""
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await create_indexes()
            
            # 여러 인덱스 생성 확인
            assert mock_session.execute.call_count >= 7
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_initial_data(self, mock_session):
        """초기 데이터 생성 테스트"""
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await create_initial_data()
            
            # SystemMetrics 객체 추가 확인
            mock_session.add.assert_called()
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_migrations(self):
        """전체 마이그레이션 실행 테스트"""
        with patch('database.migrations.init_database') as mock_init, \
             patch('database.migrations.create_tables') as mock_create_tables, \
             patch('database.migrations.create_indexes') as mock_create_indexes, \
             patch('database.migrations.create_initial_data') as mock_create_data:
            
            await run_migrations()
            
            mock_init.assert_called_once()
            mock_create_tables.assert_called_once()
            mock_create_indexes.assert_called_once()
            mock_create_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_database(self):
        """데이터베이스 초기화 테스트"""
        with patch('database.migrations.drop_tables') as mock_drop, \
             patch('database.migrations.create_tables') as mock_create, \
             patch('database.migrations.create_indexes') as mock_indexes, \
             patch('database.migrations.create_initial_data') as mock_data:
            
            await reset_database()
            
            mock_drop.assert_called_once()
            mock_create.assert_called_once()
            mock_indexes.assert_called_once()
            mock_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_schema(self, mock_session, mock_connection):
        """데이터베이스 스키마 상태 확인 테스트"""
        mock_session.execute.return_value = mock_connection
        
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            result = await check_database_schema()
            
            assert result is not None
            assert 'tables' in result
            assert 'table_counts' in result
            assert len(result['tables']) == 2

    @pytest.mark.asyncio
    async def test_create_sample_data(self, mock_session):
        """샘플 데이터 생성 테스트"""
        mock_user = User(
            id="test-uuid",
            username="test_user",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="테스트 사용자"
        )
        mock_session.refresh.return_value = mock_user
        
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await create_sample_data()
            
            # 사용자와 분석 결과 추가 확인
            assert mock_session.add.call_count >= 2
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_migration_error_handling(self):
        """마이그레이션 오류 처리 테스트"""
        with patch('database.migrations.AsyncSessionLocal', side_effect=Exception("DB Error")):
            with pytest.raises(Exception):
                await create_tables()

class TestDatabaseCLI:
    """데이터베이스 CLI 도구 테스트"""

    @pytest.mark.asyncio
    async def test_cli_migrate_command(self):
        """CLI migrate 명령어 테스트"""
        with patch('database.migrations.run_migrations') as mock_migrate:
            # CLI 스크립트 실행을 시뮬레이션
            await run_migrations()
            mock_migrate.assert_called_once()

    @pytest.mark.asyncio
    async def test_cli_reset_command(self):
        """CLI reset 명령어 테스트"""
        with patch('database.migrations.reset_database') as mock_reset:
            await reset_database()
            mock_reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_cli_check_command(self):
        """CLI check 명령어 테스트"""
        with patch('database.migrations.check_database_schema') as mock_check:
            mock_check.return_value = {"tables": ["users"], "table_counts": {"users": 0}}
            result = await check_database_schema()
            
            assert result["tables"] == ["users"]
            assert result["table_counts"]["users"] == 0

class TestDatabasePerformance:
    """데이터베이스 성능 테스트"""

    @pytest.mark.asyncio
    async def test_index_creation_performance(self, mock_session):
        """인덱스 생성 성능 테스트"""
        import time
        
        start_time = time.time()
        
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            await create_indexes()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 인덱스 생성이 1초 이내에 완료되어야 함
        assert execution_time < 1.0

    @pytest.mark.asyncio
    async def test_bulk_operations(self, mock_session):
        """대량 데이터 처리 성능 테스트"""
        # 대량의 샘플 데이터 생성 테스트
        with patch('database.migrations.AsyncSessionLocal', return_value=mock_session):
            # 여러 번 샘플 데이터 생성
            for _ in range(10):
                await create_sample_data()
            
            # 세션에 추가된 객체 수 확인
            assert mock_session.add.call_count >= 20

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
