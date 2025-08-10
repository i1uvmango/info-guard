#!/bin/bash

# Info-Guard 브랜치 머지 스크립트
# 브랜치를 안전하게 머지하고 정리합니다.

# 유틸리티 함수들 로드
source "$(dirname "$0")/git-utils.sh"

# 사용법 출력
show_usage() {
    echo "사용법: $0 <대상_브랜치> [소스_브랜치]"
    echo ""
    echo "옵션:"
    echo "  대상_브랜치    머지할 대상 브랜치 (예: main, develop)"
    echo "  소스_브랜치    머지할 소스 브랜치 (생략 시 현재 브랜치)"
    echo ""
    echo "예시:"
    echo "  $0 main                    # 현재 브랜치를 main에 머지"
    echo "  $0 main feature/database   # feature/database를 main에 머지"
    echo "  $0 develop bugfix/issue    # bugfix/issue를 develop에 머지"
    echo ""
}

# 머지 전 준비
prepare_merge() {
    local target_branch="$1"
    local source_branch="$2"
    
    # 대상 브랜치가 존재하는지 확인
    if ! branch_exists "$target_branch"; then
        log_error "대상 브랜치 '$target_branch'가 존재하지 않습니다."
        return 1
    fi
    
    # 소스 브랜치가 존재하는지 확인
    if ! branch_exists "$source_branch"; then
        log_error "소스 브랜치 '$source_branch'가 존재하지 않습니다."
        return 1
    fi
    
    # 현재 브랜치 확인
    local current_branch=$(get_current_branch)
    
    # 대상 브랜치로 전환
    if [ "$current_branch" != "$target_branch" ]; then
        log_info "대상 브랜치 '$target_branch'로 전환합니다..."
        if ! safe_checkout "$target_branch"; then
            return 1
        fi
    fi
    
    # 원격 저장소와 동기화
    if check_remote; then
        sync_remote "$target_branch"
    fi
    
    return 0
}

# 충돌 해결 가이드
show_conflict_resolution_guide() {
    echo ""
    log_warning "머지 충돌이 발생했습니다!"
    echo ""
    echo "충돌 해결 방법:"
    echo "1. 충돌된 파일들을 편집기에서 열어 충돌을 해결하세요"
    echo "2. 충돌 해결 후 다음 명령어를 실행하세요:"
    echo "   git add ."
    echo "   git commit"
    echo ""
    echo "또는 머지를 취소하려면:"
    echo "   git merge --abort"
    echo ""
}

# 머지 후 정리
cleanup_after_merge() {
    local source_branch="$1"
    local target_branch="$2"
    
    # 소스 브랜치가 현재 브랜치가 아닌 경우 삭제
    local current_branch=$(get_current_branch)
    if [ "$source_branch" != "$current_branch" ] && [ "$source_branch" != "main" ] && [ "$source_branch" != "master" ]; then
        log_info "소스 브랜치 '$source_branch'를 삭제합니다..."
        git branch -d "$source_branch" 2>/dev/null || log_warning "브랜치 삭제에 실패했습니다."
        
        # 원격 브랜치도 삭제
        if check_remote; then
            echo -n "원격 브랜치도 삭제하시겠습니까? (y/N): "
            read -r delete_remote
            
            if [[ $delete_remote =~ ^[Yy]$ ]]; then
                git push origin --delete "$source_branch" 2>/dev/null || log_warning "원격 브랜치 삭제에 실패했습니다."
            fi
        fi
    fi
}

# 메인 함수
main() {
    local target_branch="$1"
    local source_branch="$2"
    
    # 인수 검증
    if [ $# -lt 1 ] || [ $# -gt 2 ]; then
        log_error "잘못된 인수 개수입니다."
        show_usage
        exit 1
    fi
    
    # 소스 브랜치가 지정되지 않은 경우 현재 브랜치 사용
    if [ -z "$source_branch" ]; then
        source_branch=$(get_current_branch)
        log_info "소스 브랜치를 현재 브랜치로 설정: $source_branch"
    fi
    
    log_step "브랜치 머지 프로세스 시작"
    
    # Git 상태 확인
    check_git_status
    
    # 브랜치 정보 출력
    log_info "머지 정보:"
    echo "  소스 브랜치: $source_branch"
    echo "  대상 브랜치: $target_branch"
    echo ""
    
    # 머지 전 준비
    if ! prepare_merge "$target_branch" "$source_branch"; then
        log_error "머지 준비에 실패했습니다."
        exit 1
    fi
    
    # 현재 브랜치 확인 (전환 후)
    local current_branch=$(get_current_branch)
    log_info "현재 브랜치: $current_branch"
    
    # 머지 실행
    log_step "브랜치를 머지합니다..."
    
    if git merge "$source_branch" --no-ff -m "Merge branch '$source_branch' into $target_branch"; then
        log_success "머지가 성공적으로 완료되었습니다!"
        
        # 머지 정보 출력
        local merge_commit=$(git rev-parse --short HEAD)
        echo ""
        log_info "머지 정보:"
        echo "  커밋 해시: $merge_commit"
        echo "  소스 브랜치: $source_branch"
        echo "  대상 브랜치: $target_branch"
        echo ""
        
        # 원격 저장소에 푸시
        if check_remote; then
            echo -n "원격 저장소에 푸시하시겠습니까? (y/N): "
            read -r push_confirm
            
            if [[ $push_confirm =~ ^[Yy]$ ]]; then
                log_info "원격 저장소에 푸시합니다..."
                if git push origin "$target_branch"; then
                    log_success "푸시가 완료되었습니다!"
                else
                    log_error "푸시에 실패했습니다."
                    exit 1
                fi
            else
                log_info "푸시를 건너뜁니다."
            fi
        fi
        
        # 머지 후 정리
        cleanup_after_merge "$source_branch" "$target_branch"
        
    else
        log_error "머지에 실패했습니다."
        
        # 충돌 확인
        if check_conflicts; then
            show_conflict_resolution_guide
        fi
        
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