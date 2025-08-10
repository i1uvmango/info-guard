# Info-Guard 데이터베이스 관리 가이드

## 📋 개요

이 디렉토리는 Info-Guard 프로젝트의 데이터베이스 관련 코드를 포함합니다. PostgreSQL을 메인 데이터베이스로 사용하며, Redis를 캐싱 레이어로 활용합니다.

## 🏗️ 구조

```
database/
├── __init__.py          # 패키지 초기화
├── connection.py        # 데이터베이스 연결 관리
├── models.py           # SQLAlchemy 모델 정의
├── migrations.py       # 기본 마이그레이션 스크립트
├── services.py         # 데이터베이스 서비스 레이어
├── alembic.ini         # Alembic 설정 파일
├── migrations/         # Alembic 마이그레이션 디렉토리
│   ├── env.py         # 마이그레이션 환경 설정
│   ├── script.py.mako # 마이그레이션 템플릿
│   └── versions/      # 마이그레이션 버전 파일들
└── README.md           # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 설정
cp env.example .env
# .env 파일에서 데이터베이스 설정 수정
```

### 2. 데이터베이스 초기화

```bash
# 기본 마이그레이션 실행
python scripts/manage_db.py migrate

# 또는 Alembic 사용
python scripts/manage_db.py alembic
```

### 3. 샘플 데이터 생성

```bash
python scripts/manage_db.py sample
```

## 📊 데이터베이스 스키마

### 주요 테이블

#### users
- 사용자 계정 정보
- 인증 및 권한 관리

#### analysis_results
- YouTube 영상 분석 결과
- AI 모델 추론 결과 저장

#### feedbacks
- 사용자 피드백 수집
- 분석 결과에 대한 평가

#### video_metadata
- YouTube 영상 메타데이터
- 캐싱을 위한 만료 시간 관리

#### analysis_cache
- 분석 결과 캐싱
- 성능 향상을 위한 임시 저장

#### system_metrics
- 시스템 성능 메트릭
- 모니터링 및 최적화

## 🔄 마이그레이션 관리

### 기본 마이그레이션

```python
from database.migrations import run_migrations, reset_database

# 마이그레이션 실행
await run_migrations()

# 데이터베이스 초기화 (개발용)
await reset_database()
```

### Alembic 마이그레이션

```bash
# 새 마이그레이션 생성
cd database
alembic revision --autogenerate -m "설명"

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 되돌리기
alembic downgrade -1
```

### CLI 도구 사용

```bash
# 데이터베이스 상태 확인
python scripts/manage_db.py check

# 백업 생성
python scripts/manage_db.py backup

# 백업 목록 조회
python scripts/manage_db.py list-backups

# 백업에서 복구
python scripts/manage_db.py restore --backup-file backups/infoguard_backup_20240810.sql
```

## 🛠️ 개발 도구

### 데이터베이스 연결 테스트

```python
from database.connection import test_connection

# 연결 테스트
await test_connection()
```

### 스키마 검증

```python
from database.migrations import check_database_schema

# 스키마 상태 확인
schema_info = await check_database_schema()
```

## 📈 성능 최적화

### 인덱스

- `analysis_results`: video_id, user_id, created_at
- `feedbacks`: analysis_id, created_at
- `video_metadata`: cache_expires_at
- `analysis_cache`: expires_at

### 캐싱 전략

- Redis를 사용한 분석 결과 캐싱
- 영상 메타데이터 TTL 기반 만료
- 사용자 세션 관리

## 🔒 보안 고려사항

- 환경 변수를 통한 민감 정보 관리
- SQL 인젝션 방지를 위한 파라미터 바인딩
- 사용자 권한 검증
- 데이터 암호화 (필요시)

## 🧪 테스트

### 단위 테스트

```bash
# 데이터베이스 테스트 실행
pytest tests/test_database.py -v
```

### 통합 테스트

```bash
# 전체 데이터베이스 통합 테스트
pytest tests/integration/test_database_integration.py -v
```

## 📚 참고 자료

- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [Alembic 마이그레이션 가이드](https://alembic.sqlalchemy.org/)
- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation)

## 🆘 문제 해결

### 일반적인 문제들

1. **연결 실패**
   - 데이터베이스 서비스 실행 상태 확인
   - 환경 변수 설정 검증
   - 방화벽 설정 확인

2. **마이그레이션 실패**
   - 데이터베이스 권한 확인
   - 기존 스키마 충돌 검사
   - 로그 파일 확인

3. **성능 문제**
   - 인덱스 사용률 확인
   - 쿼리 실행 계획 분석
   - 캐시 히트율 모니터링

### 로그 확인

```bash
# 애플리케이션 로그
tail -f logs/app.log

# 데이터베이스 로그 (PostgreSQL)
tail -f /var/log/postgresql/postgresql-*.log
```

## 🤝 기여하기

새로운 마이그레이션이나 스키마 변경이 필요한 경우:

1. 이슈 생성
2. 브랜치 생성
3. 마이그레이션 파일 작성
4. 테스트 코드 작성
5. PR 생성

## 📝 변경 이력

- 2024-08-10: 초기 데이터베이스 스키마 생성
- 2024-08-10: Alembic 마이그레이션 시스템 구축
- 2024-08-10: CLI 관리 도구 추가
