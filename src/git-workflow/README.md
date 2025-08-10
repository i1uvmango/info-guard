# Info-Guard Git 워크플로우 시스템

Info-Guard 프로젝트의 Git 작업을 자동화하는 워크플로우 시스템입니다.

## 📋 목차

- [시스템 개요](#시스템-개요)
- [폴더 구조](#폴더-구조)
- [사용법](#사용법)
- [워크플로우](#워크플로우)
- [스크립트 설명](#스크립트-설명)
- [템플릿](#템플릿)

## 🎯 시스템 개요

이 시스템은 다음과 같은 Git 작업들을 자동화합니다:

- ✅ 자동 커밋 생성
- ✅ 브랜치 생성 및 체크아웃
- ✅ 코드 리뷰 프로세스
- ✅ 머지 작업
- ✅ 릴리즈 관리
- ✅ 태그 생성

## 📁 폴더 구조

```
git-workflow/
├── README.md                    # 이 파일
├── scripts/                     # 실행 스크립트들
│   ├── auto-commit.sh          # 자동 커밋 스크립트
│   ├── create-branch.sh        # 브랜치 생성 스크립트
│   ├── merge-branch.sh         # 브랜치 머지 스크립트
│   ├── release.sh              # 릴리즈 스크립트
│   └── git-utils.sh            # Git 유틸리티 함수들
├── workflows/                   # 워크플로우 정의
│   ├── feature-workflow.md     # 기능 개발 워크플로우
│   ├── bugfix-workflow.md      # 버그 수정 워크플로우
│   ├── release-workflow.md     # 릴리즈 워크플로우
│   └── hotfix-workflow.md      # 긴급 수정 워크플로우
└── templates/                   # 커밋 메시지 템플릿
    ├── commit-template.md       # 커밋 메시지 템플릿
    ├── pr-template.md          # PR 템플릿
    └── release-template.md     # 릴리즈 노트 템플릿
```

## 🚀 사용법

### 1. 자동 커밋

```bash
# 모든 변경사항을 자동으로 커밋
./git-workflow/scripts/auto-commit.sh

# 특정 파일만 커밋
./git-workflow/scripts/auto-commit.sh "src/database/"

# 커스텀 메시지로 커밋
./git-workflow/scripts/auto-commit.sh "" "feat: 데이터베이스 구현 완료"
```

### 2. 브랜치 생성

```bash
# 기능 브랜치 생성
./git-workflow/scripts/create-branch.sh feature "database-implementation"

# 버그 수정 브랜치 생성
./git-workflow/scripts/create-branch.sh bugfix "fix-connection-issue"

# 핫픽스 브랜치 생성
./git-workflow/scripts/create-branch.sh hotfix "security-patch"
```

### 3. 브랜치 머지

```bash
# 현재 브랜치를 main에 머지
./git-workflow/scripts/merge-branch.sh main

# 특정 브랜치를 main에 머지
./git-workflow/scripts/merge-branch.sh main feature/database-implementation
```

### 4. 릴리즈 생성

```bash
# 새 릴리즈 생성
./git-workflow/scripts/release.sh v1.0.0 "첫 번째 릴리즈"
```

## 🔄 워크플로우

### 기능 개발 워크플로우

1. **브랜치 생성**: `./git-workflow/scripts/create-branch.sh feature "feature-name"`
2. **개발 작업**: 코드 작성 및 테스트
3. **자동 커밋**: `./git-workflow/scripts/auto-commit.sh`
4. **PR 생성**: GitHub에서 Pull Request 생성
5. **코드 리뷰**: 팀원들의 리뷰 진행
6. **머지**: `./git-workflow/scripts/merge-branch.sh main`

### 버그 수정 워크플로우

1. **브랜치 생성**: `./git-workflow/scripts/create-branch.sh bugfix "bug-description"`
2. **버그 수정**: 문제 해결
3. **테스트**: 수정사항 검증
4. **커밋**: `./git-workflow/scripts/auto-commit.sh`
5. **머지**: `./git-workflow/scripts/merge-branch.sh main`

### 릴리즈 워크플로우

1. **릴리즈 브랜치**: `./git-workflow/scripts/create-branch.sh release "v1.0.0"`
2. **최종 테스트**: 모든 기능 검증
3. **릴리즈 생성**: `./git-workflow/scripts/release.sh v1.0.0 "릴리즈 노트"`
4. **태그 생성**: 자동으로 Git 태그 생성

## 📝 스크립트 설명

### auto-commit.sh
- 변경된 파일들을 자동으로 감지
- 커밋 메시지 자동 생성
- 스테이징 및 커밋 자동화

### create-branch.sh
- 브랜치 타입별 생성 (feature, bugfix, hotfix, release)
- 자동으로 새 브랜치로 체크아웃
- 브랜치 네이밍 컨벤션 적용

### merge-branch.sh
- 브랜치 머지 자동화
- 충돌 감지 및 해결 가이드
- 머지 후 브랜치 정리

### release.sh
- 릴리즈 버전 관리
- 릴리즈 노트 자동 생성
- Git 태그 생성

## 🎨 템플릿

### 커밋 메시지 템플릿
- Conventional Commits 형식 사용
- 타입별 메시지 템플릿 제공
- 자동으로 적절한 접두사 선택

### PR 템플릿
- 기능 설명
- 변경사항 목록
- 테스트 방법
- 체크리스트

### 릴리즈 노트 템플릿
- 새로운 기능
- 버그 수정
- 기타 변경사항
- 마이그레이션 가이드

## ⚙️ 설정

### Git 설정

```bash
# 커밋 메시지 템플릿 설정
git config --global commit.template github/templates/commit-template.md

# 브랜치 네이밍 설정
git config --global init.defaultBranch main
```

### 스크립트 권한 설정

```bash
# 모든 스크립트에 실행 권한 부여
chmod +x git-workflow/scripts/*.sh
```

## 🐛 문제 해결

### 일반적인 문제들

1. **권한 오류**
   ```bash
   chmod +x github/scripts/*.sh
   ```

2. **Git 설정 오류**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

3. **브랜치 충돌**
   ```bash
   git stash
   git pull origin main
   git stash pop
   ```

## 📚 추가 자료

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/) 