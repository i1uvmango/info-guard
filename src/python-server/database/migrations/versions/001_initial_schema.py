"""초기 데이터베이스 스키마 생성

Revision ID: 001
Revises: 
Create Date: 2024-08-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # UUID 확장 생성
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # users 테이블 생성
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # analysis_results 테이블 생성
    op.create_table('analysis_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('video_id', sa.String(length=20), nullable=False),
        sa.Column('video_title', sa.String(length=500), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('channel_id', sa.String(length=50), nullable=False),
        sa.Column('channel_name', sa.String(length=200), nullable=False),
        sa.Column('analysis_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('include_comments', sa.Boolean(), nullable=False, default=False),
        sa.Column('include_subtitles', sa.Boolean(), nullable=False, default=False),
        sa.Column('results', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_scores', postgresql.JSONB(), nullable=False),
        sa.Column('overall_credibility_score', sa.Float(), nullable=False),
        sa.Column('analysis_time_seconds', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # feedbacks 테이블 생성
    op.create_table('feedbacks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('feedback_type', sa.String(length=20), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # video_metadata 테이블 생성
    op.create_table('video_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('video_id', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel_id', sa.String(length=50), nullable=False),
        sa.Column('channel_name', sa.String(length=200), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('view_count', sa.BigInteger(), nullable=True),
        sa.Column('like_count', sa.BigInteger(), nullable=True),
        sa.Column('comment_count', sa.BigInteger(), nullable=True),
        sa.Column('duration', sa.String(length=20), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('category_id', sa.String(length=20), nullable=True),
        sa.Column('cache_expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_id')
    )
    
    # analysis_cache 테이블 생성
    op.create_table('analysis_cache',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('cache_data', postgresql.JSONB(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    
    # system_metrics 테이블 생성
    op.create_table('system_metrics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('average_response_time', sa.Float(), nullable=False, default=0.0),
        sa.Column('error_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('cpu_usage', sa.Float(), nullable=False, default=0.0),
        sa.Column('memory_usage', sa.Float(), nullable=False, default=0.0),
        sa.Column('disk_usage', sa.Float(), nullable=False, default=0.0),
        sa.Column('model_inference_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('model_inference_time', sa.Float(), nullable=False, default=0.0),
        sa.Column('db_connection_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('db_query_count', sa.BigInteger(), nullable=False, default=0),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 인덱스 생성
    op.create_index('idx_analysis_video_created', 'analysis_results', ['video_id', 'created_at'])
    op.create_index('idx_analysis_user_created', 'analysis_results', ['user_id', 'created_at'])
    op.create_index('idx_analysis_credibility_created', 'analysis_results', ['overall_credibility_score', 'created_at'])
    op.create_index('idx_feedback_analysis_created', 'feedbacks', ['analysis_id', 'created_at'])
    op.create_index('idx_video_metadata_expires', 'video_metadata', ['cache_expires_at'])
    op.create_index('idx_analysis_cache_expires', 'analysis_cache', ['expires_at'])
    op.create_index('idx_system_metrics_timestamp', 'system_metrics', ['timestamp'])


def downgrade() -> None:
    # 인덱스 삭제
    op.drop_index('idx_system_metrics_timestamp', 'system_metrics')
    op.drop_index('idx_analysis_cache_expires', 'analysis_cache')
    op.drop_index('idx_video_metadata_expires', 'video_metadata')
    op.drop_index('idx_feedback_analysis_created', 'feedbacks')
    op.drop_index('idx_analysis_credibility_created', 'analysis_results')
    op.drop_index('idx_analysis_user_created', 'analysis_results')
    op.drop_index('idx_analysis_video_created', 'analysis_results')
    
    # 테이블 삭제
    op.drop_table('system_metrics')
    op.drop_table('analysis_cache')
    op.drop_table('video_metadata')
    op.drop_table('feedbacks')
    op.drop_table('analysis_results')
    op.drop_table('users')
