# 전체 시스템 통합 테스트 가이드

## 개요
이 문서는 Info-Guard 전체 시스템의 통합 테스트 방법을 다룹니다:
- 모든 서비스 실행 및 확인
- End-to-End 테스트 시나리오
- 성능 및 부하 테스트
- 장애 복구 테스트

## 1. 시스템 구성 확인

### 1.1 필수 서비스 목록
```bash
# 전체 시스템 구성
1. AI Service (FastAPI) - 포트 8000
2. Node.js Backend (Express) - 포트 3000
3. PostgreSQL Database - 포트 5432
4. Redis Cache - 포트 6379
5. Chrome Extension
6. Nginx (선택사항) - 포트 80/443
```

### 1.2 서비스 실행 확인
```bash
# 1. AI 서비스 상태 확인
curl -X GET http://localhost:8000/health
# 예상 응답: {"status": "healthy", "timestamp": "..."}

# 2. Node.js 백엔드 상태 확인
curl -X GET http://localhost:3000/health
# 예상 응답: {"status": "healthy", "timestamp": "..."}

# 3. Redis 연결 확인
redis-cli ping
# 예상 응답: PONG

# 4. PostgreSQL 연결 확인
psql -h localhost -U user -d infoguard -c "SELECT 1;"
# 예상 응답: 1

# 5. 포트 사용 확인
lsof -i :8000  # AI Service
lsof -i :3000  # Node.js Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

## 2. End-to-End 테스트 시나리오

### 2.1 기본 통합 테스트
```javascript
// 테스트 시나리오 1: 전체 분석 플로우
1. 모든 서비스 실행
   - AI Service: python main.py
   - Node.js Backend: npm start
   - PostgreSQL: docker-compose up postgres
   - Redis: docker-compose up redis

2. Chrome Extension 로드
   - Chrome에서 chrome://extensions/ 접속
   - 개발자 모드 활성화
   - src/chrome-extension 폴더 로드

3. YouTube 비디오 분석
   - YouTube 비디오 페이지 접속
   - Extension 아이콘 클릭
   - "분석 시작" 버튼 클릭
   - 실시간 진행률 확인
   - 최종 결과 확인

4. 결과 검증
   - 신뢰도 점수 (0-100)
   - 등급 (A, B, C, D, F)
   - 편향 분석 결과
   - 팩트 체크 결과
   - 오버레이 표시
```

### 2.2 WebSocket 통신 테스트
```javascript
// 테스트 시나리오 2: 실시간 통신
1. WebSocket 연결 확인
   - AI Service WebSocket 엔드포인트 활성화
   - Extension에서 WebSocket 연결
   - 연결 상태 로그 확인

2. 실시간 메시지 테스트
   - 분석 시작 메시지 전송
   - 진행률 업데이트 메시지 수신
   - 분석 완료 메시지 수신
   - 에러 메시지 처리

3. 연결 안정성 테스트
   - 네트워크 끊김 시뮬레이션
   - 자동 재연결 확인
   - 메시지 재전송 확인
```

### 2.3 데이터베이스 통합 테스트
```javascript
// 테스트 시나리오 3: 데이터 저장 및 조회
1. 분석 결과 저장
   - 비디오 분석 실행
   - PostgreSQL에 결과 저장 확인
   - Redis 캐시 저장 확인

2. 데이터 조회 테스트
   - 이전 분석 결과 조회
   - 채널 통계 조회
   - 사용자 피드백 저장/조회

3. 데이터 일관성 확인
   - PostgreSQL과 Redis 데이터 동기화
   - 트랜잭션 롤백 테스트
   - 데이터 무결성 확인
```

## 3. 성능 테스트

### 3.1 응답 시간 테스트
```bash
# 단일 분석 응답 시간 측정
time curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# 목표: 30초 이내 응답
```

### 3.2 동시 사용자 테스트
```bash
# 동시 요청 테스트
for i in {1..10}; do
  curl -X POST "http://localhost:8000/analyze" \
    -H "Content-Type: application/json" \
    -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' &
done
wait

# 시스템 안정성 확인
- CPU 사용률 모니터링
- 메모리 사용량 확인
- 데이터베이스 연결 풀 상태
```

### 3.3 부하 테스트
```bash
# Apache Bench를 사용한 부하 테스트
ab -n 100 -c 10 -H "Content-Type: application/json" \
  -p test_data.json http://localhost:8000/analyze

# test_data.json 내용:
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

## 4. 장애 복구 테스트

### 4.1 서비스 중단 테스트
```bash
# 1. AI 서비스 중단 테스트
pkill -f "python main.py"
# Extension에서 에러 처리 확인
# 자동 재연결 시도 확인

# 2. 데이터베이스 중단 테스트
docker-compose stop postgres
# 캐시된 데이터 사용 확인
# 서비스 복구 후 데이터 동기화 확인

# 3. Redis 중단 테스트
docker-compose stop redis
# 캐시 미스 처리 확인
# 데이터베이스 직접 조회 확인
```

### 4.2 네트워크 장애 테스트
```bash
# 네트워크 끊김 시뮬레이션
sudo ifconfig lo0 down  # 로컬 네트워크 끊김
# Extension 재연결 시도 확인
sudo ifconfig lo0 up    # 네트워크 복구
# 자동 재연결 확인
```

### 4.3 데이터 손실 복구 테스트
```bash
# 1. 데이터베이스 백업 테스트
pg_dump -h localhost -U user infoguard > backup.sql

# 2. 데이터 복구 테스트
psql -h localhost -U user infoguard < backup.sql

# 3. 캐시 복구 테스트
redis-cli FLUSHALL
# 캐시 재구축 확인
```

## 5. 보안 테스트

### 5.1 인증 및 권한 테스트
```bash
# 1. API 키 검증 테스트
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "invalid_url"}'

# 2. CORS 설정 테스트
curl -H "Origin: http://malicious-site.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/analyze

# 3. SQL Injection 테스트
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "'; DROP TABLE users; --"}'
```

### 5.2 입력 검증 테스트
```javascript
// 1. 잘못된 URL 테스트
const invalidUrls = [
  "not_a_url",
  "http://malicious-site.com",
  "https://youtube.com/invalid",
  "javascript:alert('xss')"
];

// 2. XSS 공격 테스트
const xssPayloads = [
  "<script>alert('xss')</script>",
  "javascript:alert('xss')",
  "onload=alert('xss')"
];

// 3. SQL Injection 테스트
const sqlInjectionPayloads = [
  "'; DROP TABLE users; --",
  "' OR 1=1 --",
  "'; INSERT INTO users VALUES ('hacker'); --"
];
```

## 6. 모니터링 및 로깅 테스트

### 6.1 로그 수집 테스트
```bash
# 1. 로그 파일 확인
tail -f logs/ai-service.log
tail -f logs/backend.log
tail -f logs/extension.log

# 2. 로그 레벨 테스트
# DEBUG, INFO, WARN, ERROR 레벨별 로그 확인

# 3. 로그 로테이션 테스트
# 로그 파일 크기 제한 및 자동 로테이션 확인
```

### 6.2 메트릭 수집 테스트
```bash
# 1. 성능 메트릭 확인
curl http://localhost:8000/metrics

# 2. 시스템 리소스 모니터링
top -p $(pgrep -f "python main.py")
free -h
df -h

# 3. 데이터베이스 성능 확인
psql -h localhost -U user -d infoguard -c "
SELECT 
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats 
WHERE schemaname = 'public';
"
```

## 7. 테스트 자동화

### 7.1 테스트 스크립트
```bash
#!/bin/bash
# integration_test.sh

echo "=== Info-Guard 통합 테스트 시작 ==="

# 1. 서비스 상태 확인
echo "1. 서비스 상태 확인 중..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000/health || exit 1
redis-cli ping || exit 1

# 2. 기본 분석 테스트
echo "2. 기본 분석 테스트 중..."
response=$(curl -s -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}')

if echo "$response" | grep -q "error"; then
  echo "분석 테스트 실패"
  exit 1
fi

# 3. WebSocket 테스트
echo "3. WebSocket 테스트 중..."
# WebSocket 연결 테스트 (wscat 필요)

# 4. 성능 테스트
echo "4. 성능 테스트 중..."
start_time=$(date +%s)
curl -s -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' > /dev/null
end_time=$(date +%s)
response_time=$((end_time - start_time))

if [ $response_time -gt 30 ]; then
  echo "응답 시간이 너무 깁니다: ${response_time}초"
  exit 1
fi

echo "=== 모든 테스트 통과! ==="
```

### 7.2 CI/CD 파이프라인
```yaml
# .github/workflows/integration-test.yml
name: Integration Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: infoguard
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run integration tests
      run: |
        chmod +x integration_test.sh
        ./integration_test.sh
```

## 8. 테스트 체크리스트

### 8.1 기본 기능 테스트
- [ ] 모든 서비스 정상 실행
- [ ] 서비스 간 통신 정상
- [ ] Chrome Extension 로드 성공
- [ ] YouTube 비디오 분석 성공
- [ ] 결과 표시 정상

### 8.2 성능 테스트
- [ ] 응답 시간 30초 이내
- [ ] 동시 사용자 처리 가능
- [ ] 메모리 사용량 적정
- [ ] CPU 사용률 적정
- [ ] 데이터베이스 성능 적정

### 8.3 장애 복구 테스트
- [ ] 서비스 중단 시 에러 처리
- [ ] 자동 재연결 기능
- [ ] 데이터 백업/복구
- [ ] 로그 수집 정상
- [ ] 모니터링 정상

### 8.4 보안 테스트
- [ ] 입력 검증 정상
- [ ] SQL Injection 방지
- [ ] XSS 공격 방지
- [ ] CORS 설정 정상
- [ ] API 키 검증 정상

## 9. 성공 지표

### 9.1 기능적 지표
- 전체 시스템 가동률: 99.9% 이상
- 분석 성공률: 95% 이상
- 사용자 만족도: 4.5/5.0 이상
- 장애 복구 시간: 5분 이내

### 9.2 기술적 지표
- 평균 응답 시간: 20초 이내
- 에러율: 2% 이하
- 시스템 가용성: 99.9% 이상
- 데이터 일관성: 100%

---

**참고**: 이 가이드를 따라 Info-Guard 전체 시스템을 안전하고 효율적으로 테스트할 수 있습니다. 