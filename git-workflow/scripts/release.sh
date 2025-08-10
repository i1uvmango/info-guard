#!/bin/bash

# Info-Guard 릴리즈 스크립트
# 새 릴리즈를 생성하고 Git 태그를 만듭니다.

# 유틸리티 함수들 로드
source "$(dirname "$0")/git-utils.sh"

# 사용법 출력
show_usage() {
    echo "사용법: $0 <버전> [릴리즈_노트]"
    echo ""
    echo "옵션:"
    echo "  버전           릴리즈 버전 (예: v1.0.0, v2.1.3)"
    echo "  릴리즈_노트     릴리즈 노트 내용 (선택사항)"
    echo ""
    echo "예시:"
    echo "  $0 v1.0.0"
    echo "  $0 v1.0.0 \"첫 번째 릴리즈 - 데이터베이스 구현 완료\""
    echo ""
}

# 릴리즈 노트 생성
generate_release_notes() {
    local version="$1"
    local custom_notes="$2"
    local template_file="$(dirname "$0")/../templates/release-template.md"
    
    # 커스텀 노트가 있으면 사용
    if [ -n "$custom_notes" ]; then
        echo "$custom_notes"
        return
    fi
    
    # 템플릿 파일이 있으면 사용
    if [ -f "$template_file" ]; then
        local template_content=$(cat "$template_file")
        echo "$template_content" | sed "s/{{VERSION}}/$version/g"
        return
    fi
    
    # 기본 릴리즈 노트 생성
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    local commits_since_last=""
    
    if [ -n "$last_tag" ]; then
        commits_since_last=$(git log --oneline "$last_tag"..HEAD | head -10)
    else
        commits_since_last=$(git log --oneline -10)
    fi
    
    cat << EOF
# Info-Guard $version

## 🎉 새로운 기능

- 새로운 기능들이 추가되었습니다

## 🐛 버그 수정

- 버그들이 수정되었습니다

## 📝 변경사항

\`\`\`
$commits_since_last
\`\`\`

## 🚀 설치 방법

\`\`\`bash
git clone <repository-url>
cd Info-Guard
npm install
\`\`\`

## 📋 릴리즈 노트

이 릴리즈는 Info-Guard 프로젝트의 $version 버전입니다.

생성일: $(date '+%Y-%m-%d %H:%M:%S')
커밋: $(git rev-parse --short HEAD)
EOF
}

# 릴리즈 전 검증
validate_release() {
    local version="$1"
    
    # 버전 형식 검증
    if ! validate_version "$version"; then
        return 1
    fi
    
    # 변경사항이 있는지 확인
    if ! check_changes; then
        log_warning "커밋할 변경사항이 없습니다."
        echo -n "계속 진행하시겠습니까? (y/N): "
        read -r continue_release
        
        if [[ ! $continue_release =~ ^[Yy]$ ]]; then
            log_info "릴리즈를 취소합니다."
            exit 0
        fi
    fi
    
    # 현재 브랜치가 main인지 확인
    local current_branch=$(get_current_branch)
    if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
        log_warning "현재 브랜치가 main이 아닙니다: $current_branch"
        echo -n "main 브랜치로 전환하시겠습니까? (y/N): "
        read -r switch_to_main
        
        if [[ $switch_to_main =~ ^[Yy]$ ]]; then
            if ! safe_checkout "main"; then
                log_error "main 브랜치로 전환에 실패했습니다."
                return 1
            fi
        else
            log_info "릴리즈를 취소합니다."
            exit 0
        fi
    fi
    
    return 0
}

# 메인 함수
main() {
    local version="$1"
    local release_notes="$2"
    
    # 인수 검증
    if [ $# -lt 1 ] || [ $# -gt 2 ]; then
        log_error "잘못된 인수 개수입니다."
        show_usage
        exit 1
    fi
    
    log_step "릴리즈 생성 프로세스 시작"
    
    # Git 상태 확인
    check_git_status
    
    # 릴리즈 전 검증
    if ! validate_release "$version"; then
        exit 1
    fi
    
    # 현재 상태 출력
    local current_branch=$(get_current_branch)
    local commit_hash=$(git rev-parse --short HEAD)
    
    log_info "릴리즈 정보:"
    echo "  버전: $version"
    echo "  브랜치: $current_branch"
    echo "  커밋: $commit_hash"
    echo ""
    
    # 변경사항이 있으면 커밋
    if check_changes; then
        log_info "변경사항을 커밋합니다..."
        if ! git add . && git commit -m "chore: 릴리즈 $version 준비"; then
            log_error "커밋에 실패했습니다."
            exit 1
        fi
    fi
    
    # 릴리즈 노트 생성
    log_step "릴리즈 노트를 생성합니다..."
    local release_notes_content=$(generate_release_notes "$version" "$release_notes")
    
    # 릴리즈 노트를 임시 파일에 저장
    local temp_notes_file="/tmp/release_notes_$version.md"
    echo "$release_notes_content" > "$temp_notes_file"
    
    log_info "릴리즈 노트가 생성되었습니다: $temp_notes_file"
    
    # 릴리즈 노트 확인
    echo -n "릴리즈 노트를 확인하시겠습니까? (y/N): "
    read -r review_notes
    
    if [[ $review_notes =~ ^[Yy]$ ]]; then
        if command -v code > /dev/null 2>&1; then
            code "$temp_notes_file"
        elif command -v nano > /dev/null 2>&1; then
            nano "$temp_notes_file"
        elif command -v vim > /dev/null 2>&1; then
            vim "$temp_notes_file"
        else
            cat "$temp_notes_file"
        fi
    fi
    
    # 태그 생성
    log_step "Git 태그를 생성합니다..."
    
    if git tag -a "$version" -F "$temp_notes_file"; then
        log_success "태그가 성공적으로 생성되었습니다: $version"
        
        # 태그 정보 출력
        local tag_info=$(git show --no-patch --format="%H%n%an%n%ad%n%s" "$version")
        local tag_hash=$(echo "$tag_info" | head -1)
        local tag_author=$(echo "$tag_info" | sed -n '2p')
        local tag_date=$(echo "$tag_info" | sed -n '3p')
        local tag_message=$(echo "$tag_info" | sed -n '4p')
        
        echo ""
        log_info "태그 정보:"
        echo "  해시: $tag_hash"
        echo "  작성자: $tag_author"
        echo "  날짜: $tag_date"
        echo "  메시지: $tag_message"
        echo ""
        
        # 원격 저장소에 푸시
        if check_remote; then
            echo -n "원격 저장소에 태그를 푸시하시겠습니까? (y/N): "
            read -r push_confirm
            
            if [[ $push_confirm =~ ^[Yy]$ ]]; then
                log_info "원격 저장소에 태그를 푸시합니다..."
                if git push origin "$version"; then
                    log_success "태그가 원격 저장소에 푸시되었습니다!"
                else
                    log_error "태그 푸시에 실패했습니다."
                    exit 1
                fi
            else
                log_info "태그 푸시를 건너뜁니다."
            fi
        fi
        
        # 릴리즈 노트 파일 정리
        rm -f "$temp_notes_file"
        
        # 릴리즈 완료 메시지
        echo ""
        log_success "🎉 릴리즈 $version이 성공적으로 생성되었습니다!"
        echo ""
        log_info "다음 단계:"
        echo "  1. GitHub에서 릴리즈 노트를 확인하세요"
        echo "  2. 필요한 경우 릴리즈 노트를 수정하세요"
        echo "  3. 팀원들에게 릴리즈를 알리세요"
        echo ""
        
    else
        log_error "태그 생성에 실패했습니다."
        rm -f "$temp_notes_file"
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