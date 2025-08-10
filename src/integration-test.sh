#!/bin/bash

# Info-Guard 전체 시스템 통합 테스트 스크립트
# 사용법: ./integration-test.sh

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 테스트 결과 저장
TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 결과 기록
record_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$result" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        success "$test_name: $message"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        error "$test_name: $message"
    fi
    
    TEST_RESULTS+=("$test_name|$result|$message")
}

# 서비스 상태 확인
check_service() {
    local service_name="$1"
    local url="$2"
    local expected_status="$3"
    
    log "서비스 확인: $service_name ($url)"
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        record_test "$service_name 상태 확인" "PASS" "서비스가 정상 실행 중입니다"
        return 0
    else
        record_test "$service_name 상태 확인" "FAIL" "서비스에 연결할 수 없습니다"
        return 1
    fi
}

# 포트 사용 확인
check_port() {
    local port="$1"
    local service_name="$2"
    
    log "포트 확인: $service_name (포트 $port)"
    
    if lsof -i ":$port" > /dev/null 2>&1; then
        record_test "$service_name 포트 확인" "PASS" "포트 $port가 사용 중입니다"
        return 0
    else
        record_test "$service_name 포트 확인" "FAIL" "포트 $port가 사용되지 않습니다"
        return 1
    fi
}

# API 테스트
test_api() {
    local endpoint="$1"
    local test_name="$2"
    local expected_field="$3"
    
    log "API 테스트: $test_name"
    
    response=$(curl -s "$endpoint" 2>/dev/null)
    if [ $? -eq 0 ] && echo "$response" | grep -q "$expected_field"; then
        record_test "$test_name" "PASS" "API 응답이 정상입니다"
        return 0
    else
        record_test "$test_name" "FAIL" "API 응답이 비정상입니다"
        return 1
    fi
}

# 성능 테스트
performance_test() {
    local endpoint="$1"
    local test_name="$2"
    local timeout="$3"
    
    log "성능 테스트: $test_name (타임아웃: ${timeout}초)"
    
    start_time=$(date +%s)
    
    if timeout "$timeout" curl -s "$endpoint" > /dev/null 2>&1; then
        end_time=$(date +%s)
        response_time=$((end_time - start_time))
        
        if [ $response_time -le $timeout ]; then
            record_test "$test_name" "PASS" "응답 시간: ${response_time}초"
            return 0
        else
            record_test "$test_name" "FAIL" "응답 시간 초과: ${response_time}초"
            return 1
        fi
    else
        record_test "$test_name" "FAIL" "요청 타임아웃"
        return 1
    fi
}

# 파일 존재 확인
check_file() {
    local file_path="$1"
    local test_name="$2"
    
    log "파일 확인: $test_name"
    
    if [ -f "$file_path" ]; then
        record_test "$test_name" "PASS" "파일이 존재합니다"
        return 0
    else
        record_test "$test_name" "FAIL" "파일이 존재하지 않습니다: $file_path"
        return 1
    fi
}

# 메인 테스트 함수
main() {
    echo "=== Info-Guard 전체 시스템 통합 테스트 시작 ==="
    echo "테스트 시작 시간: $(date)"
    echo ""
    
    # 1. 기본 서비스 상태 확인
    log "1. 기본 서비스 상태 확인"
    
    check_service "AI Service" "http://localhost:8000/health" "healthy"
    check_service "Node.js Backend" "http://localhost:3000/health" "healthy"
    check_port "8000" "AI Service"
    check_port "3000" "Node.js Backend"
    check_port "5432" "PostgreSQL"
    check_port "6379" "Redis"
    
    echo ""
    
    # 2. API 기능 테스트
    log "2. API 기능 테스트"
    
    test_api "http://localhost:8000/health" "AI Service 헬스체크" "status"
    test_api "http://localhost:8000/" "AI Service 루트 엔드포인트" "Info-Guard"
    
    echo ""
    
    # 3. 성능 테스트
    log "3. 성능 테스트"
    
    performance_test "http://localhost:8000/health" "AI Service 응답 시간" 5
    performance_test "http://localhost:3000/health" "Node.js Backend 응답 시간" 5
    
    echo ""
    
    # 4. 파일 구조 확인
    log "4. 파일 구조 확인"
    
    check_file "ai-service/main.py" "AI Service 메인 파일"
    check_file "chrome-extension/manifest.json" "Chrome Extension 매니페스트"
    check_file "chrome-extension/popup/popup.html" "Chrome Extension 팝업"
    check_file "chrome-extension/assets/icons/icon-128.png" "Chrome Extension 아이콘"
    check_file "python-server/requirements.txt" "Python 의존성 파일"
    check_file "nodejs-server/package.json" "Node.js 의존성 파일"
    
    echo ""
    
    # 5. 데이터베이스 연결 테스트
    log "5. 데이터베이스 연결 테스트"
    
    if command -v psql >/dev/null 2>&1; then
        if psql -h localhost -U user -d infoguard -c "SELECT 1;" >/dev/null 2>&1; then
            record_test "PostgreSQL 연결" "PASS" "데이터베이스 연결 성공"
        else
            record_test "PostgreSQL 연결" "FAIL" "데이터베이스 연결 실패"
        fi
    else
        warning "PostgreSQL 클라이언트가 설치되지 않았습니다"
    fi
    
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            record_test "Redis 연결" "PASS" "Redis 연결 성공"
        else
            record_test "Redis 연결" "FAIL" "Redis 연결 실패"
        fi
    else
        warning "Redis 클라이언트가 설치되지 않았습니다"
    fi
    
    echo ""
    
    # 6. Chrome Extension 테스트 준비
    log "6. Chrome Extension 테스트 준비"
    
    if [ -d "chrome-extension" ]; then
        record_test "Chrome Extension 디렉토리" "PASS" "Extension 디렉토리가 존재합니다"
        
        # 필수 파일들 확인
        required_files=(
            "manifest.json"
            "popup/popup.html"
            "popup/popup.js"
            "popup/popup.css"
            "content/content.js"
            "background/background.js"
            "options/options.html"
            "utils/api-client.js"
            "utils/storage-manager.js"
            "assets/icons/icon-16.png"
            "assets/icons/icon-48.png"
            "assets/icons/icon-128.png"
        )
        
        for file in "${required_files[@]}"; do
            if [ -f "chrome-extension/$file" ]; then
                record_test "Extension 파일: $file" "PASS" "파일이 존재합니다"
            else
                record_test "Extension 파일: $file" "FAIL" "파일이 없습니다"
            fi
        done
    else
        record_test "Chrome Extension 디렉토리" "FAIL" "Extension 디렉토리가 없습니다"
    fi
    
    echo ""
    
    # 7. 환경 변수 확인
    log "7. 환경 변수 확인"
    
    if [ -f ".env" ]; then
        record_test "환경 변수 파일" "PASS" ".env 파일이 존재합니다"
        
        # 중요한 환경 변수들 확인
        if grep -q "YOUTUBE_API_KEY" .env; then
            record_test "YouTube API 키" "PASS" "API 키가 설정되어 있습니다"
        else
            record_test "YouTube API 키" "FAIL" "API 키가 설정되지 않았습니다"
        fi
    else
        record_test "환경 변수 파일" "FAIL" ".env 파일이 없습니다"
    fi
    
    echo ""
    
    # 8. 테스트 결과 요약
    log "8. 테스트 결과 요약"
    
    echo "=== 테스트 결과 ==="
    echo "총 테스트: $TOTAL_TESTS"
    echo "성공: $PASSED_TESTS"
    echo "실패: $FAILED_TESTS"
    
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)
        echo "성공률: ${success_rate}%"
    fi
    
    echo ""
    
    # 실패한 테스트 상세 출력
    if [ $FAILED_TESTS -gt 0 ]; then
        echo "=== 실패한 테스트 상세 ==="
        for result in "${TEST_RESULTS[@]}"; do
            IFS='|' read -r test_name result_status message <<< "$result"
            if [ "$result_status" = "FAIL" ]; then
                error "$test_name: $message"
            fi
        done
        echo ""
    fi
    
    # 최종 결과
    if [ $FAILED_TESTS -eq 0 ]; then
        success "🎉 모든 테스트가 통과했습니다!"
        exit 0
    else
        error "❌ $FAILED_TESTS개의 테스트가 실패했습니다."
        exit 1
    fi
}

# 스크립트 실행
main "$@" 