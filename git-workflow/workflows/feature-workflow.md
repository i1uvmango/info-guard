# 기능 개발 워크플로우

Info-Guard 프로젝트의 새로운 기능 개발을 위한 워크플로우입니다.

## 📋 개요

이 워크플로우는 새로운 기능을 개발할 때 따라야 하는 단계별 가이드입니다.

## 🔄 워크플로우 단계

### 1단계: 브랜치 생성

```bash
# 기능 브랜치 생성
./git-workflow/scripts/create-branch.sh feature "feature-name"

# 예시
./git-workflow/scripts/create-branch.sh feature "database-implementation"
./git-workflow/scripts/create-branch.sh feature "user-authentication"
./git-workflow/scripts/create-branch.sh feature "api-endpoints"
```

**체크리스트:**
- [ ] 브랜치 이름이 명확하고 설명적인가?
- [ ] 올바른 브랜치 타입을 선택했는가?
- [ ] 브랜치가 성공적으로 생성되었는가?

### 2단계: 개발 작업

**코딩 가이드라인:**
- [ ] 코드 스타일 가이드를 따르는가?
- [ ] 적절한 주석을 작성했는가?
- [ ] 에러 처리를 포함했는가?
- [ ] 테스트를 작성했는가?

**커밋 가이드라인:**
```bash
# 개발 중간 커밋
./git-workflow/scripts/auto-commit.sh

# 특정 파일만 커밋
./git-workflow/scripts/auto-commit.sh "src/database/"

# 커스텀 메시지로 커밋
./git-workflow/scripts/auto-commit.sh "" "feat: 데이터베이스 연결 구현"
```

### 3단계: 테스트

**테스트 체크리스트:**
- [ ] 단위 테스트를 작성했는가?
- [ ] 통합 테스트를 작성했는가?
- [ ] 모든 테스트가 통과하는가?
- [ ] 수동 테스트를 수행했는가?

```bash
# 테스트 실행
npm test

# 테스트 커버리지 확인
npm run test:coverage
```

### 4단계: 코드 리뷰 준비

**리뷰 준비 체크리스트:**
- [ ] 코드가 깔끔하고 읽기 쉬운가?
- [ ] 불필요한 코드를 제거했는가?
- [ ] 성능을 고려했는가?
- [ ] 보안을 고려했는가?
- [ ] 문서를 업데이트했는가?

### 5단계: Pull Request 생성

**PR 생성 전 체크리스트:**
- [ ] 모든 변경사항이 커밋되었는가?
- [ ] 브랜치가 최신 main과 동기화되었는가?
- [ ] PR 제목이 명확한가?
- [ ] PR 설명이 충분한가?

```bash
# 최신 main과 동기화
git fetch origin
git rebase origin/main

# PR 템플릿 사용
# github/templates/pr-template.md 참조
```

### 6단계: 코드 리뷰

**리뷰 체크리스트:**
- [ ] 코드 품질이 적절한가?
- [ ] 테스트가 충분한가?
- [ ] 문서가 업데이트되었는가?
- [ ] 성능에 영향을 주지 않는가?
- [ ] 보안 문제가 없는가?

### 7단계: 머지

```bash
# 리뷰 승인 후 머지
./git-workflow/scripts/merge-branch.sh main
```

**머지 전 체크리스트:**
- [ ] 모든 리뷰 코멘트가 해결되었는가?
- [ ] CI/CD 파이프라인이 통과했는가?
- [ ] 충돌이 해결되었는가?

## 🎯 성공 기준

### 기능 완성도
- [ ] 요구사항이 모두 구현되었는가?
- [ ] 사용자 스토리가 완료되었는가?
- [ ] 에러 케이스가 처리되었는가?

### 코드 품질
- [ ] 코드 리뷰가 완료되었는가?
- [ ] 테스트 커버리지가 적절한가?
- [ ] 문서가 업데이트되었는가?

### 배포 준비
- [ ] 기능이 테스트 환경에서 검증되었는가?
- [ ] 롤백 계획이 준비되었는가?
- [ ] 모니터링이 설정되었는가?

## 🚨 문제 해결

### 일반적인 문제들

**1. 브랜치 충돌**
```bash
# 충돌 해결
git status
# 충돌된 파일들을 편집
git add .
git commit
```

**2. 테스트 실패**
```bash
# 로컬에서 테스트 재실행
npm test

# 특정 테스트만 실행
npm test -- --grep "test-name"
```

**3. 리뷰 코멘트 해결**
```bash
# 코멘트에 따라 코드 수정
./git-workflow/scripts/auto-commit.sh "" "fix: 리뷰 코멘트 반영"
```

## 📚 관련 자료

- [Git Flow 가이드](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PR 템플릿](../templates/pr-template.md)
- [커밋 템플릿](../templates/commit-template.md) 