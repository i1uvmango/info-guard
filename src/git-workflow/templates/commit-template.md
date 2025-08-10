# 커밋 메시지 템플릿

## 📝 커밋 타입

다음 중 하나를 선택하여 커밋 타입을 지정하세요:

- **feat**: 새로운 기능 추가
- **fix**: 버그 수정
- **docs**: 문서 수정
- **style**: 코드 포맷팅, 세미콜론 누락 등 (코드 변경 없음)
- **refactor**: 코드 리팩토링
- **test**: 테스트 추가 또는 수정
- **chore**: 빌드 프로세스 또는 보조 도구 변경

## 🎯 커밋 메시지 형식

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 예시

```
feat(database): PostgreSQL 연결 구현

- Prisma ORM 설정 추가
- 데이터베이스 스키마 정의
- 연결 풀 설정

Closes #123
```

```
fix(auth): 로그인 인증 오류 수정

- JWT 토큰 검증 로직 개선
- 세션 만료 시간 조정

Fixes #456
```

## 📋 작성 가이드라인

### 1. 제목 (첫 번째 줄)
- 50자 이내로 작성
- 명령형 현재 시제 사용 (add, fix, update 등)
- 첫 글자는 소문자로 시작
- 마침표로 끝내지 않음

### 2. 본문 (선택사항)
- 무엇을, 왜 변경했는지 설명
- 이전 동작과의 차이점 설명
- 각 줄은 72자 이내로 작성

### 3. 푸터 (선택사항)
- Breaking Changes 설명
- 관련 이슈 번호 참조

## 🔍 스코프 예시

- **frontend**: 프론트엔드 관련 변경
- **backend**: 백엔드 관련 변경
- **database**: 데이터베이스 관련 변경
- **api**: API 관련 변경
- **auth**: 인증 관련 변경
- **ui**: 사용자 인터페이스 관련 변경
- **test**: 테스트 관련 변경
- **docs**: 문서 관련 변경

## ⚠️ 주의사항

- 커밋 메시지는 변경사항을 명확하게 설명해야 함
- 불필요한 정보는 제외
- 팀원이 이해할 수 있는 수준으로 작성
- 영어로 작성하는 것을 권장

## 🎨 자동 생성

이 템플릿은 `./git-workflow/scripts/auto-commit.sh` 스크립트에서 자동으로 사용됩니다.

파일 타입에 따라 적절한 커밋 타입과 스코프가 자동으로 결정됩니다:

- `.js`, `.ts`, `.jsx`, `.tsx` → `feat(frontend)`
- `.py` → `feat(backend)`
- `.sql`, `database`, `prisma` → `feat(database)`
- `.md`, `docs`, `README` → `docs`
- `test`, `spec`, `__tests__` → `test`
- `.json`, `package.json` → `chore` 