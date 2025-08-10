#!/bin/bash

# Info-Guard 브랜치 생성 스크립트
# 새로운 브랜치를 생성하고 자동으로 체크아웃합니다.

# 유틸리티 함수들 로드
source "$(dirname "$0")/git-utils.sh"

# 사용법 출력
show_usage() {
    echo "사용법: $0 <브랜치_타입> <브랜치_이름>"
    echo ""
    echo "브랜치 타입:"
    echo "  feature    새로운 기능 개발"
    echo "  bugfix     버그 수정"
    echo "  hotfix     긴급 수정"
    echo "  release    릴리즈 준비"
    echo ""
    echo "예시:"
    echo "  $0 feature database-implementation"
    echo "  $0 bugfix connection-issue"
    echo "  $0 hotfix security-patch"
    echo "  $0 release v1.0.0"
    echo ""
}

# 브랜치 타입 검증
validate_branch_type() {
    local branch_type="$1"
    local valid_types=("feature" "bugfix" "hotfix" "release")
    
    for valid_type in "${valid_types[@]}"; do
        if [ "$branch_type" == "$valid_type" ]; then
            return 0
        fi
    done
    
    log_error "잘못된 브랜치 타입입니다: $branch_type"
    echo "유효한 브랜치 타입: ${valid_types[*]}"
    return 1
}

# 브랜치 생성 전 준비
prepare_branch_creation() {
    local branch_type="$1"
    local base_branch=""
    
    # 브랜치 타입에 따른 기본 브랜치 결정
    case $branch_type in
        "feature")
            base_branch="main"
            ;;
        "bugfix")
            base_branch="main"
            ;;
        "hotfix")
            base_branch="main"
            ;;
        "release")
            base_branch="main"
            ;;
    esac
    
    # 기본 브랜치가 존재하는지 확인
    if ! branch_exists "$base_branch"; then
        log_error "기본 브랜치 '$base_branch'가 존재하지 않습니다."
        return 1
    fi
    
    # 현재 브랜치가 기본 브랜치가 아닌 경우 기본 브랜치로 전환
    local current_branch=$(get_current_branch)
    if [ "$current_branch" != "$base_branch" ]; then
        log_info "기본 브랜치 '$base_branch'로 전환합니다..."
        if ! safe_checkout "$base_branch"; then
            return 1
        fi
    fi
    
    # 원격 저장소와 동기화
    if check_remote; then
        sync_remote "$base_branch"
    fi
    
    return 0
}

# 메인 함수
main() {
    local branch_type="$1"
    local branch_name="$2"
    
    # 인수 검증
    if [ $# -ne 2 ]; then
        log_error "정확히 2개의 인수가 필요합니다."
        show_usage
        exit 1
    fi
    
    # 브랜치 타입 검증
    if ! validate_branch_type "$branch_type"; then
        exit 1
    fi
    
    # 브랜치 이름 검증
    if [ -z "$branch_name" ]; then
        log_error "브랜치 이름이 비어있습니다."
        exit 1
    fi
    
    log_step "새 브랜치 생성 프로세스 시작"
    
    # Git 상태 확인
    check_git_status
    
    # 브랜치 이름 포맷팅
    local formatted_branch_name=$(format_branch_name "$branch_type" "$branch_name")
    log_info "브랜치 이름: $formatted_branch_name"
    
    # 브랜치가 이미 존재하는지 확인
    if branch_exists "$formatted_branch_name"; then
        log_warning "브랜치 '$formatted_branch_name'이 이미 존재합니다."
        echo -n "기존 브랜치로 체크아웃하시겠습니까? (y/N): "
        read -r checkout_existing
        
        if [[ $checkout_existing =~ ^[Yy]$ ]]; then
            if safe_checkout "$formatted_branch_name"; then
                log_success "기존 브랜치로 체크아웃되었습니다: $formatted_branch_name"
                exit 0
            else
                log_error "브랜치 체크아웃에 실패했습니다."
                exit 1
            fi
        else
            log_info "브랜치 생성을 취소합니다."
            exit 0
        fi
    fi
    
    # 브랜치 생성 전 준비
    if ! prepare_branch_creation "$branch_type"; then
        log_error "브랜치 생성 준비에 실패했습니다."
        exit 1
    fi
    
    # 새 브랜치 생성 및 체크아웃
    log_step "새 브랜치를 생성하고 체크아웃합니다..."
    
    if git checkout -b "$formatted_branch_name"; then
        log_success "브랜치가 성공적으로 생성되었습니다: $formatted_branch_name"
        
        # 브랜치 정보 출력
        local current_branch=$(get_current_branch)
        local commit_hash=$(git rev-parse --short HEAD)
        
        echo ""
        log_info "브랜치 정보:"
        echo "  이름: $current_branch"
        echo "  타입: $branch_type"
        echo "  커밋: $commit_hash"
        echo ""
        
        # 브랜치 타입별 안내 메시지
        case $branch_type in
            "feature")
                log_info "💡 기능 개발을 시작하세요!"
                log_info "   - 코드 작성 후: ./github/scripts/auto-commit.sh"
                log_info "   - 작업 완료 후: ./github/scripts/merge-branch.sh main"
                ;;
            "bugfix")
                log_info "🐛 버그 수정을 시작하세요!"
                log_info "   - 수정 후: ./github/scripts/auto-commit.sh"
                log_info "   - 완료 후: ./github/scripts/merge-branch.sh main"
                ;;
            "hotfix")
                log_info "🚨 긴급 수정을 시작하세요!"
                log_info "   - 수정 후: ./github/scripts/auto-commit.sh"
                log_info "   - 완료 후: ./github/scripts/merge-branch.sh main"
                ;;
            "release")
                log_info "🎉 릴리즈 준비를 시작하세요!"
                log_info "   - 최종 테스트 후: ./github/scripts/release.sh $branch_name"
                ;;
        esac
        
        # 원격 저장소에 브랜치 푸시 여부 확인
        if check_remote; then
            echo -n "원격 저장소에 브랜치를 푸시하시겠습니까? (y/N): "
            read -r push_confirm
            
            if [[ $push_confirm =~ ^[Yy]$ ]]; then
                log_info "원격 저장소에 브랜치를 푸시합니다..."
                if git push -u origin "$formatted_branch_name"; then
                    log_success "원격 브랜치가 생성되었습니다!"
                else
                    log_error "원격 브랜치 생성에 실패했습니다."
                    exit 1
                fi
            else
                log_info "원격 푸시를 건너뜁니다."
            fi
        fi
        
    else
        log_error "브랜치 생성에 실패했습니다."
        exit 1
    fi
}

# 스크립트가 직접 실행될 때만 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 도움말 요청 확인
    if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    # 메인 함수 실행
    main "$@"
fi 