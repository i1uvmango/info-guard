# 🔒 보안 가이드

## ⚠️ 중요 보안 주의사항

### API 키 및 비밀 정보 관리

**절대로 다음 파일들을 Git에 커밋하지 마세요:**

- `.env` 파일 (실제 API 키가 포함된 환경 변수)
- `secrets.json`, `secrets.yaml` 등 비밀 정보 파일
- `*.key`, `*.pem` 등 인증서 파일
- 실제 API 키가 하드코딩된 소스 코드

### YouTube API 키 설정 방법

1. **환경 변수 파일 생성** (Git에 커밋하지 않음):
   ```bash
   # src/python-server/ 디렉토리에서
   cp env.example .env
   ```

2. **실제 API 키 입력**:
   ```bash
   # .env 파일 편집
   YOUTUBE_API_KEY=your_actual_api_key_here
   ```

3. **환경 변수 로드 확인** (보안 강화됨):
   ```bash
   # 보안 테스트 실행
   cd src/python-server
   python test_security.py
   
   # 또는 직접 확인 (키는 마스킹되어 출력됨)
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); from utils.security import mask_api_key; print('API Key:', mask_api_key(os.getenv('YOUTUBE_API_KEY', 'Not set')))"
   ```

### 보안 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 실제 API 키가 소스 코드에 하드코딩되지 않았는지 확인
- [ ] `env.example`에는 플레이스홀더만 포함되어 있는지 확인
- [ ] 프로덕션 환경에서는 환경 변수나 보안 관리 시스템 사용

### Git 히스토리에서 API 키 제거

만약 실수로 API 키를 커밋했다면:

```bash
# Git 히스토리에서 파일 완전 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch src/python-server/.env" \
  --prune-empty --tag-name-filter cat -- --all

# 강제 푸시 (주의: 팀원들과 협의 필요)
git push origin --force --all
```

### 환경별 설정 관리

- **개발 환경**: `.env.development` (Git에 커밋하지 않음)
- **테스트 환경**: `.env.test` (Git에 커밋하지 않음)
- **프로덕션 환경**: 환경 변수 또는 보안 관리 시스템

## 🚨 보안 위험 신고

보안 취약점을 발견했다면:

1. **즉시** 프로젝트 관리자에게 연락
2. 공개적으로 공유하지 않음
3. 필요한 경우 API 키 재발급

## 🔒 자동 보안 기능

### API 키 자동 마스킹
- 모든 로그에서 API 키가 자동으로 `[API_KEY_MASKED]`로 마스킹됨
- 환경 변수 값도 자동으로 `[MASKED]`로 보호됨
- 민감한 키워드가 포함된 데이터는 자동으로 필터링됨

### 보안 로깅 설정
```python
from utils.security import setup_secure_logging

# 애플리케이션 시작 시 자동으로 적용됨
setup_secure_logging()
```

### 테스트 방법
```bash
cd src/python-server
python test_security.py
```

## 📚 추가 보안 리소스

- [GitHub Security Best Practices](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
