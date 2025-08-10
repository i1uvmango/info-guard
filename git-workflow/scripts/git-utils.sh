#!/bin/bash

# Info-Guard Git 유틸리티 함수들
# 이 파일은 다른 Git 스크립트들에서 공통으로 사용되는 함수들을 포함합니다.

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Git 상태 확인
check_git_status() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "현재 디렉토리가 Git 저장소가 아닙니다."
        exit 1
    fi
}

# 변경사항 확인
check_changes() {
    if git diff-index --quiet HEAD --; then
        log_warning "커밋할 변경사항이 없습니다."
        return 1
    fi
    return 0
}

# 브랜치 존재 확인
branch_exists() {
    local branch_name=$1
    if git show-ref --verify --quiet refs/heads/$branch_name; then
        return 0
    else
        return 1
    fi
}

# 현재 브랜치 이름 가져오기
get_current_branch() {
    git branch --show-current
}

# 변경된 파일 목록 가져오기
get_changed_files() {
    git diff --name-only --cached
}

# 변경된 파일 타입별 분류
classify_changes() {
    local files="$1"
    local types=""
    
    # 파일 타입별로 분류
    if echo "$files" | grep -q "\.js$\|\.ts$\|\.jsx$\|\.tsx$"; then
        types="$types,frontend"
    fi
    
    if echo "$files" | grep -q "\.py$"; then
        types="$types,backend"
    fi
    
    if echo "$files" | grep -q "\.sql$\|database\|prisma"; then
        types="$types,database"
    fi
    
    if echo "$files" | grep -q "\.md$\|docs\|README"; then
        types="$types,documentation"
    fi
    
    if echo "$files" | grep -q "\.json$\|package\.json\|yarn\.lock"; then
        types="$types,dependencies"
    fi
    
    if echo "$files" | grep -q "\.sh$\|scripts"; then
        types="$types,scripts"
    fi
    
    if echo "$files" | grep -q "\.css$\|\.scss$\|\.sass$"; then
        types="$types,styles"
    fi
    
    if echo "$files" | grep -q "test\|spec\|__tests__"; then
        types="$types,tests"
    fi
    
    # 첫 번째 쉼표 제거
    types=${types#,}
    
    echo "$types"
}

# 커밋 타입 결정
determine_commit_type() {
    local files="$1"
    local types=$(classify_changes "$files")
    
    # 변경사항 타입에 따른 커밋 타입 결정
    if echo "$types" | grep -q "frontend\|backend\|database"; then
        echo "feat"
    elif echo "$types" | grep -q "tests"; then
        echo "test"
    elif echo "$types" | grep -q "documentation"; then
        echo "docs"
    elif echo "$types" | grep -q "dependencies"; then
        echo "chore"
    elif echo "$types" | grep -q "scripts\|styles"; then
        echo "refactor"
    else
        echo "fix"
    fi
}

# 커밋 메시지 생성
generate_commit_message() {
    local commit_type=$1
    local custom_message=$2
    local files="$3"
    
    if [ -n "$custom_message" ]; then
        echo "$custom_message"
        return
    fi
    
    local types=$(classify_changes "$files")
    local scope=""
    
    # 스코프 결정
    if echo "$types" | grep -q "frontend"; then
        scope="frontend"
    elif echo "$types" | grep -q "backend"; then
        scope="backend"
    elif echo "$types" | grep -q "database"; then
        scope="database"
    elif echo "$types" | grep -q "documentation"; then
        scope="docs"
    fi
    
    # 기본 메시지 생성
    local message="$commit_type"
    if [ -n "$scope" ]; then
        message="$message($scope)"
    fi
    
    # 타입별 메시지 추가
    case $commit_type in
        "feat")
            message="$message: 새로운 기능 추가"
            ;;
        "fix")
            message="$message: 버그 수정"
            ;;
        "docs")
            message="$message: 문서 업데이트"
            ;;
        "test")
            message="$message: 테스트 추가"
            ;;
        "refactor")
            message="$message: 코드 리팩토링"
            ;;
        "chore")
            message="$message: 의존성 업데이트"
            ;;
        *)
            message="$message: 변경사항 적용"
            ;;
    esac
    
    echo "$message"
}

# 브랜치 네이밍 컨벤션 적용
format_branch_name() {
    local branch_type=$1
    local branch_name=$2
    
    # 특수문자 제거 및 소문자 변환
    local formatted_name=$(echo "$branch_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
    
    case $branch_type in
        "feature")
            echo "feature/$formatted_name"
            ;;
        "bugfix")
            echo "bugfix/$formatted_name"
            ;;
        "hotfix")
            echo "hotfix/$formatted_name"
            ;;
        "release")
            echo "release/$formatted_name"
            ;;
        *)
            echo "$formatted_name"
            ;;
    esac
}

# 원격 저장소 확인
check_remote() {
    if ! git remote get-url origin > /dev/null 2>&1; then
        log_warning "원격 저장소가 설정되지 않았습니다."
        return 1
    fi
    return 0
}

# 충돌 확인
check_conflicts() {
    if git ls-files -u | grep -q .; then
        log_error "머지 충돌이 발생했습니다. 충돌을 해결한 후 다시 시도하세요."
        return 1
    fi
    return 0
}

# 안전한 브랜치 전환
safe_checkout() {
    local target_branch=$1
    
    # 현재 작업 저장
    if ! git diff-index --quiet HEAD --; then
        log_warning "작업 중인 변경사항을 stash합니다."
        git stash push -m "Auto stash before checkout"
    fi
    
    # 브랜치 전환
    if git checkout "$target_branch" 2>/dev/null; then
        log_success "브랜치를 $target_branch로 전환했습니다."
        
        # stash 복원
        if git stash list | grep -q "Auto stash before checkout"; then
            log_info "이전 작업을 복원합니다."
            git stash pop
        fi
    else
        log_error "브랜치 전환에 실패했습니다."
        return 1
    fi
}

# 원격 브랜치 동기화
sync_remote() {
    local branch=$1
    
    log_info "원격 저장소에서 최신 변경사항을 가져옵니다..."
    git fetch origin
    
    if git rev-parse --verify origin/$branch > /dev/null 2>&1; then
        git pull origin $branch
        log_success "원격 브랜치와 동기화 완료"
    else
        log_warning "원격에 $branch 브랜치가 없습니다."
    fi
}

# 브랜치 정리
cleanup_branch() {
    local branch=$1
    
    if [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
        log_info "브랜치 $branch를 삭제합니다..."
        git branch -d "$branch" 2>/dev/null || log_warning "브랜치 삭제에 실패했습니다."
    fi
}

# 릴리즈 버전 검증
validate_version() {
    local version=$1
    
    if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "올바른 버전 형식이 아닙니다. 예: v1.0.0"
        return 1
    fi
    
    # 이미 존재하는 태그인지 확인
    if git tag | grep -q "^$version$"; then
        log_error "버전 $version은 이미 존재합니다."
        return 1
    fi
    
    return 0
}

# 변경사항 요약 생성
generate_changes_summary() {
    local files="$1"
    local summary=""
    
    # 파일 타입별 개수 계산
    local js_count=$(echo "$files" | grep -c "\.js$\|\.ts$\|\.jsx$\|\.tsx$" || echo "0")
    local py_count=$(echo "$files" | grep -c "\.py$" || echo "0")
    local sql_count=$(echo "$files" | grep -c "\.sql$\|database\|prisma" || echo "0")
    local md_count=$(echo "$files" | grep -c "\.md$\|docs\|README" || echo "0")
    local test_count=$(echo "$files" | grep -c "test\|spec\|__tests__" || echo "0")
    
    if [ "$js_count" -gt 0 ]; then
        summary="$summary JS/TS 파일: $js_count개, "
    fi
    
    if [ "$py_count" -gt 0 ]; then
        summary="$summary Python 파일: $py_count개, "
    fi
    
    if [ "$sql_count" -gt 0 ]; then
        summary="$summary DB 파일: $sql_count개, "
    fi
    
    if [ "$md_count" -gt 0 ]; then
        summary="$summary 문서: $md_count개, "
    fi
    
    if [ "$test_count" -gt 0 ]; then
        summary="$summary 테스트: $test_count개, "
    fi
    
    # 마지막 쉼표 제거
    summary=${summary%, }
    
    echo "$summary"
} 