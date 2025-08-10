# Info-Guard 배포 및 운영 가이드

## 개요
이 문서는 Info-Guard 프로젝트의 배포 및 운영을 위한 가이드입니다:
- Docker 컨테이너화
- 모니터링 설정
- 백업 및 복구
- 성능 최적화
- 보안 설정

## 1. Docker 컨테이너화

### 1.1 멀티스테이지 빌드 Dockerfile
```dockerfile
# AI Service Dockerfile
FROM python:3.10-slim as builder

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로덕션 이미지
FROM python:3.10-slim

WORKDIR /app

# 보안을 위한 비root 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 애플리케이션 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .

# 권한 설정
RUN chown -R appuser:appuser /app
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Docker Compose 설정
```yaml
version: '3.8'

services:
  ai-service:
    build: ./ai-service
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:password@postgres:5432/infoguard
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: infoguard
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - ai-service
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

## 2. 모니터링 설정

### 2.1 Prometheus 설정
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-service'
    static_configs:
      - targets: ['ai-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### 2.2 Grafana 대시보드
```json
{
  "dashboard": {
    "title": "Info-Guard 모니터링",
    "panels": [
      {
        "title": "CPU 사용률",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU %"
          }
        ]
      },
      {
        "title": "메모리 사용률",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_percent",
            "legendFormat": "Memory %"
          }
        ]
      },
      {
        "title": "응답 시간",
        "type": "graph",
        "targets": [
          {
            "expr": "response_time_avg",
            "legendFormat": "Response Time (ms)"
          }
        ]
      },
      {
        "title": "에러율",
        "type": "graph",
        "targets": [
          {
            "expr": "error_rate_percent",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### 2.3 알림 설정
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alert@infoguard.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-mail'

receivers:
  - name: 'team-mail'
    email_configs:
      - to: 'admin@infoguard.com'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

## 3. 백업 및 복구

### 3.1 데이터베이스 백업 스크립트
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="infoguard"

# PostgreSQL 백업
pg_dump -h localhost -U user -d $DB_NAME > $BACKUP_DIR/postgres_$DATE.sql

# Redis 백업
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 로그 백업
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /app/logs/

# 오래된 백업 삭제 (7일 이상)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "백업 완료: $DATE"
```

### 3.2 복구 스크립트
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
DB_NAME="infoguard"

if [ -z "$BACKUP_FILE" ]; then
    echo "사용법: $0 <백업파일>"
    exit 1
fi

# PostgreSQL 복구
psql -h localhost -U user -d $DB_NAME < $BACKUP_FILE

# Redis 복구
redis-cli FLUSHALL
redis-cli RESTORE $BACKUP_FILE 0

echo "복구 완료: $BACKUP_FILE"
```

### 3.3 자동 백업 스케줄
```bash
# crontab 설정
# 매일 새벽 2시에 백업 실행
0 2 * * * /app/scripts/backup.sh

# 매주 일요일 새벽 3시에 전체 백업
0 3 * * 0 /app/scripts/full_backup.sh
```

## 4. 성능 최적화

### 4.1 Nginx 설정
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream ai_service {
        server ai-service:8000;
    }

    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;

    # 캐시 설정
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=10g inactive=60m use_temp_path=off;

    server {
        listen 80;
        server_name infoguard.com;

        # API 캐시
        location /api/ {
            proxy_cache api_cache;
            proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
            proxy_cache_valid 200 1h;
            proxy_cache_valid 404 1m;

            proxy_pass http://ai_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 정적 파일
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://ai_service;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 4.2 Redis 최적화
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 4.3 Python 애플리케이션 최적화
```python
# main.py 최적화
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 미들웨어 추가
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로덕션 설정
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
```

## 5. 보안 설정

### 5.1 환경 변수 관리
```bash
# .env.production
# 데이터베이스
DATABASE_URL=postgresql://user:password@postgres:5432/infoguard
REDIS_URL=redis://redis:6379

# API 키
YOUTUBE_API_KEY=your_youtube_api_key
SECRET_KEY=your_secret_key

# 보안
CORS_ORIGINS=https://infoguard.com,https://www.infoguard.com
ALLOWED_HOSTS=infoguard.com,www.infoguard.com

# 모니터링
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### 5.2 SSL/TLS 설정
```nginx
# SSL 설정
server {
    listen 443 ssl http2;
    server_name infoguard.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### 5.3 방화벽 설정
```bash
# UFW 설정
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 6. 배포 스크립트

### 6.1 자동 배포 스크립트
```bash
#!/bin/bash
# deploy.sh

set -e

echo "배포 시작..."

# Git에서 최신 코드 가져오기
git pull origin main

# Docker 이미지 빌드
docker-compose build

# 기존 컨테이너 중지
docker-compose down

# 새 컨테이너 시작
docker-compose up -d

# 헬스체크
echo "헬스체크 중..."
for i in {1..30}; do
    if curl -f http://localhost/health; then
        echo "배포 성공!"
        exit 0
    fi
    sleep 2
done

echo "배포 실패!"
exit 1
```

### 6.2 롤백 스크립트
```bash
#!/bin/bash
# rollback.sh

echo "롤백 시작..."

# 이전 버전으로 복원
git checkout HEAD~1

# Docker 이미지 빌드
docker-compose build

# 컨테이너 재시작
docker-compose down
docker-compose up -d

echo "롤백 완료!"
```

## 7. 운영 체크리스트

### 7.1 일일 체크리스트
- [ ] 시스템 상태 확인
- [ ] 로그 확인
- [ ] 백업 상태 확인
- [ ] 성능 메트릭 확인
- [ ] 에러 알림 확인

### 7.2 주간 체크리스트
- [ ] 보안 업데이트 확인
- [ ] 성능 분석
- [ ] 용량 계획 검토
- [ ] 백업 테스트
- [ ] 장애 복구 테스트

### 7.3 월간 체크리스트
- [ ] 전체 시스템 점검
- [ ] 성능 최적화 검토
- [ ] 보안 감사
- [ ] 비용 분석
- [ ] 사용자 피드백 분석

## 8. 문제 해결

### 8.1 일반적인 문제들
```bash
# 로그 확인
docker-compose logs ai-service

# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats

# 데이터베이스 연결 확인
docker-compose exec postgres psql -U user -d infoguard -c "SELECT 1;"
```

### 8.2 성능 문제 해결
```bash
# CPU 사용량 높은 프로세스 확인
docker-compose exec ai-service top

# 메모리 사용량 확인
docker-compose exec ai-service free -h

# 네트워크 연결 확인
docker-compose exec ai-service netstat -tulpn
```

## 9. 성공 지표

### 9.1 기술적 지표
- 시스템 가용성: 99.9% 이상
- 평균 응답 시간: 2초 이하
- 에러율: 1% 이하
- CPU 사용률: 80% 이하
- 메모리 사용률: 80% 이하

### 9.2 비즈니스 지표
- 일일 활성 사용자 수
- 분석 요청 수
- 사용자 만족도
- 피드백 수집률

---

**참고**: 이 가이드를 따라 Info-Guard 프로젝트를 안전하고 효율적으로 배포하고 운영할 수 있습니다. 