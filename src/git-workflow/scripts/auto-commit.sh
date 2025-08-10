#!/bin/bash

# Info-Guard 자동 커밋 스크립트
# 변경사항을 자동으로 감지하고 적절한 커밋 메시지와 함께 커밋합니다.

# 유틸리티 함수들 로드
source "$(dirname "$0")/git-utils.sh"

# 사용법 출력
show_usage() {
    echo "사용법: $0 [파일_패턴] [커스텀_메시지]"
    echo ""
    echo "옵션:"
    echo "  파일_패턴      특정 파일이나 디렉토리만 커밋 (선택사항)"
    echo "  커스텀_메시지   커스텀 커밋 메시지 (선택사항)"
    echo ""
    echo "예시:"
    echo "  $0                           # 모든 변경사항 자동 커밋"
    echo "  $0 \"database/\"         # 데이터베이스 관련 파일만 커밋"
    echo "  $0 \"\" \"feat: 새 기능 추가\"  # 커스텀 메시지로 커밋"
    echo ""
}

# 메인 함수
main() {
    local file_pattern="$1"
    local custom_message="$2"
    
    log_step "자동 커밋 프로세스 시작"
    
    # Git 상태 확인
    check_git_status
    
    # 변경사항 확인
    if ! check_changes; then
        log_warning "커밋할 변경사항이 없습니다."
        exit 0
    fi
    
    # 파일 패턴이 지정된 경우 해당 파일들만 스테이징
    if [ -n "$file_pattern" ]; then
        log_info "패턴 '$file_pattern'에 해당하는 파일들을 스테이징합니다..."
        
        # 파일 패턴에 해당하는 파일들 찾기
        local files_to_stage=$(git diff --name-only | grep "$file_pattern" || true)
        
        if [ -z "$files_to_stage" ]; then
            log_warning "패턴 '$file_pattern'에 해당하는 변경된 파일이 없습니다."
            exit 0
        fi
        
        # 각 파일을 개별적으로 스테이징
        echo "$files_to_stage" | while read -r file; do
            if [ -n "$file" ]; then
                git add "$file"
                log_info "스테이징: $file"
            fi
        done
    else
        # 모든 변경사항을 스테이징
        log_info "모든 변경사항을 스테이징합니다..."
        git add .
    fi
    
    # 스테이징된 파일 목록 가져오기
    local staged_files=$(get_changed_files)
    
    if [ -z "$staged_files" ]; then
        log_warning "스테이징된 파일이 없습니다."
        exit 0
    fi
    
    # 변경사항 요약 생성
    local changes_summary=$(generate_changes_summary "$staged_files")
    log_info "변경사항 요약: $changes_summary"
    
    # 커밋 타입 결정
    local commit_type=$(determine_commit_type "$staged_files")
    log_info "커밋 타입: $commit_type"
    
    # 커밋 메시지 생성
    local commit_message=$(generate_commit_message "$commit_type" "$custom_message" "$staged_files")
    
    # 커밋 실행
    log_step "커밋을 실행합니다..."
    log_info "커밋 메시지: $commit_message"
    
    if git commit -m "$commit_message"; then
        log_success "커밋이 성공적으로 완료되었습니다!"
        
        # 커밋 정보 출력
        local commit_hash=$(git rev-parse --short HEAD)
        local current_branch=$(get_current_branch)
        
        echo ""
        log_info "커밋 정보:"
        echo "  해시: $commit_hash"
        echo "  브랜치: $current_branch"
        echo "  메시지: $commit_message"
        echo "  변경사항: $changes_summary"
        echo ""
        
        # 원격 저장소가 설정된 경우 푸시 여부 확인
        if check_remote; then
            echo -n "원격 저장소에 푸시하시겠습니까? (y/N): "
            read -r push_confirm
            
            if [[ $push_confirm =~ ^[Yy]$ ]]; then
                log_info "원격 저장소에 푸시합니다..."
                if git push origin "$current_branch"; then
                    log_success "푸시가 완료되었습니다!"
                else
                    log_error "푸시에 실패했습니다."
                    exit 1
                fi
            else
                log_info "푸시를 건너뜁니다."
            fi
        fi
        
    else
        log_error "커밋에 실패했습니다."
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
    
    # 인수 개수 확인
    if [ $# -gt 2 ]; then
        log_error "너무 많은 인수가 제공되었습니다."
        show_usage
        exit 1
    fi
    
    # 메인 함수 실행
    main "$@"
fi 