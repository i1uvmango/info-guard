#!/bin/bash

# Info-Guard 데이터베이스 백업 스크립트

BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="info_guard"
DB_USER="postgres"
DB_HOST="localhost"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# PostgreSQL 백업
echo "Creating PostgreSQL backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

if [ $? -eq 0 ]; then
    echo "PostgreSQL backup completed successfully"
    
    # 압축
    gzip $BACKUP_DIR/backup_$DATE.sql
    
    # 백업 파일 크기 확인
    BACKUP_SIZE=$(du -h $BACKUP_DIR/backup_$DATE.sql.gz | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
    
    # 30일 이상 된 백업 삭제
    echo "Cleaning old backups..."
    find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
    
    echo "Backup completed: backup_$DATE.sql.gz"
else
    echo "PostgreSQL backup failed!"
    exit 1
fi

echo "Backup process completed at $(date)" 