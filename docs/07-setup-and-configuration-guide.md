# Info-Guard 설정 및 구성 가이드

## 개요
이 문서는 Info-Guard 프로젝트의 최종 설정 단계를 다룹니다:
- Chrome Extension 아이콘 파일 생성
- YouTube API 키 설정
- 환경 변수 구성

## 1. Chrome Extension 아이콘 파일 생성

### 1.1 필요한 아이콘 크기
Chrome Extension Manifest V3에서 필요한 아이콘 크기:
- `16x16`: 툴바 아이콘
- `48x48`: 확장 프로그램 관리 페이지
- `128x128`: Chrome Web Store 및 설치 시

### 1.2 아이콘 디자인 가이드라인
- **브랜드 컬러**: 신뢰성을 나타내는 파란색 계열 (#2563EB)
- **디자인 컨셉**: 방패 + 체크마크 (정보 보호 + 검증)
- **스타일**: 플랫 디자인, 모던하고 깔끔한 느낌

### 1.3 아이콘 파일 생성 방법
```bash
# 아이콘 생성 도구 설치
npm install -g pngquant svgo

# SVG에서 PNG 변환
svgo -i icon.svg -o icon-optimized.svg
# 16x16, 48x48, 128x128 크기로 변환
```

## 2. YouTube API 키 설정

### 2.1 Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3.  v3 활성화
4. 사용자 인증 정보 생성 (API 키)

### 2.2 API 키 생성 단계
```bash
# 1. Google Cloud Console에서 API 키 생성
# 2. YouTube Data API v3 활성화
# 3. API 키 제한 설정 (YouTube Data API v3만 허용)
# 4. HTTP 리퍼러 제한 설정 (선택사항)
```

### 2.3 API 키 테스트
```bash
# API 키 유효성 테스트
curl "https://www.googleapis.com/youtube/v3/videos?id=dQw4w9WgXcQ&key=AIzaSyC8_h83XbrUYo-jJJGdgHzJbZLoVaKJcd4"
```

## 3. 환경 변수 설정

### 3.1 필요한 환경 변수 목록
```env
# AI 서비스 설정
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8000
AI_SERVICE_DEBUG=false

# YouTube API 설정
YOUTUBE_API_KEY=your_youtube_api_key_here
YOUTUBE_API_QUOTA_LIMIT=10000

# 데이터베이스 설정
DATABASE_URL=postgresql://username:password@localhost:5432/infoguard
REDIS_URL=redis://localhost:6379

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 보안 설정
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# 개발/프로덕션 설정
NODE_ENV=development
PYTHON_ENV=development
```

### 3.2 환경 변수 파일 생성
```bash
# .env 파일 생성
cp env.example .env
# 환경 변수 값 설정
```

### 3.3 환경 변수 검증
```bash
# 환경 변수 로드 테스트
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('YouTube API Key:', os.getenv('YOUTUBE_API_KEY', 'Not set'))"
```

## 4. 구현 단계

### 4.1 아이콘 파일 생성
1. SVG 아이콘 디자인
2. PNG 변환 (16x16, 48x48, 128x128)
3. Chrome Extension manifest.json 업데이트

### 4.2 YouTube API 설정
1. Google Cloud Console에서 API 키 생성
2. 환경 변수에 API 키 추가
3. API 키 테스트 및 검증

### 4.3 환경 변수 구성
1. .env 파일 생성 및 설정
2. 환경 변수 로드 테스트
3. 애플리케이션에서 환경 변수 사용 확인

## 5. 테스트 및 검증

### 5.1 아이콘 테스트
- Chrome Extension 로드 시 아이콘 표시 확인
- 다양한 크기에서 아이콘 품질 확인

### 5.2 YouTube API 테스트
```bash
# API 키 테스트
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('YOUTUBE_API_KEY')
if api_key:
    print('✅ YouTube API 키 설정됨')
else:
    print('❌ YouTube API 키 설정 필요')
"
```

### 5.3 환경 변수 테스트
```bash
# 환경 변수 로드 테스트
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('환경 변수 테스트:')
print(f'AI_SERVICE_HOST: {os.getenv(\"AI_SERVICE_HOST\", \"Not set\")}')
print(f'YOUTUBE_API_KEY: {os.getenv(\"YOUTUBE_API_KEY\", \"Not set\")}')
print(f'DATABASE_URL: {os.getenv(\"DATABASE_URL\", \"Not set\")}')
"
```

## 6. 문제 해결

### 6.1 아이콘 관련 문제
- **문제**: 아이콘이 표시되지 않음
- **해결**: manifest.json의 아이콘 경로 확인, 파일 크기 검증

### 6.2 YouTube API 관련 문제
- **문제**: API 키 오류
- **해결**: API 키 유효성 확인, 할당량 확인, 제한 설정 확인

### 6.3 환경 변수 관련 문제
- **문제**: 환경 변수가 로드되지 않음
- **해결**: .env 파일 경로 확인, python-dotenv 설치 확인

## 7. 다음 단계

구현 완료 후:
1. 전체 시스템 통합 테스트
2. 성능 최적화
3. 배포 준비
4. 사용자 가이드 작성

---

**참고**: 이 가이드는 Info-Guard 프로젝트의 최종 설정 단계를 다룹니다. 각 단계를 순차적으로 진행하여 안정적인 시스템을 구축하세요. 