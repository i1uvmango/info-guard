# Chrome Extension 로드 및 테스트 가이드

## 개요
이 문서는 Info-Guard Chrome Extension의 로드, 테스트, 디버깅 방법을 다룹니다:
- Chrome Extension 로드 방법
- 기능별 테스트 시나리오
- 디버깅 및 문제 해결
- 전체 시스템 통합 테스트

## 1. Chrome Extension 로드 방법

### 1.1 개발자 모드 활성화
1. Chrome 브라우저에서 `chrome://extensions/` 접속
2. 우측 상단의 "개발자 모드" 토글 활성화
3. "압축해제된 확장 프로그램을 로드합니다" 버튼 클릭

### 1.2 Extension 로드
```bash
# Chrome Extension 디렉토리 선택
cd src/chrome-extension
# 또는 전체 경로: /Users/kapr/Documents/Info-Guard/src/chrome-extension
```

### 1.3 필수 파일 확인
```
src/chrome-extension/
├── manifest.json          # Extension 메타데이터
├── popup/
│   ├── popup.html        # 팝업 UI
│   ├── popup.css         # 팝업 스타일
│   └── popup.js          # 팝업 로직
├── content/
│   ├── content.js        # 콘텐츠 스크립트
│   └── content.css       # 오버레이 스타일
├── background/
│   └── background.js     # 백그라운드 스크립트
├── options/
│   ├── options.html      # 옵션 페이지
│   ├── options.css       # 옵션 스타일
│   └── options.js        # 옵션 로직
├── utils/
│   ├── api-client.js     # API 클라이언트
│   ├── websocket-client.js # WebSocket 클라이언트
│   └── storage-manager.js # 스토리지 관리
└── assets/
    └── icons/
        ├── icon-16.png   # 16x16 아이콘
        ├── icon-48.png   # 48x48 아이콘
        └── icon-128.png  # 128x128 아이콘
```

## 2. 기능별 테스트 시나리오

### 2.1 기본 로드 테스트
```javascript
// 테스트 시나리오
1. Extension이 정상적으로 로드되는지 확인
2. 아이콘이 툴바에 표시되는지 확인
3. 팝업이 정상적으로 열리는지 확인
4. 옵션 페이지에 접근 가능한지 확인
```

### 2.2 YouTube 페이지 감지 테스트
```javascript
// 테스트 시나리오
1. YouTube 홈페이지 접속
2. Extension 아이콘 클릭
3. "YouTube 페이지가 아닙니다" 메시지 확인
4. YouTube 비디오 페이지 접속
5. Extension 아이콘 클릭
6. 분석 시작 버튼 표시 확인
```

### 2.3 비디오 분석 테스트
```javascript
// 테스트 시나리오
1. YouTube 비디오 페이지 접속
2. Extension 팝업에서 "분석 시작" 클릭
3. 진행률 표시 확인
4. 실시간 분석 결과 확인
5. 신뢰도 점수 및 등급 표시 확인
```

### 2.4 WebSocket 통신 테스트
```javascript
// 테스트 시나리오
1. AI 서비스가 실행 중인지 확인
2. Extension에서 분석 요청
3. WebSocket 연결 상태 확인
4. 실시간 진행률 업데이트 확인
5. 분석 완료 메시지 확인
```

### 2.5 스토리지 기능 테스트
```javascript
// 테스트 시나리오
1. Extension 옵션 페이지 접속
2. 설정 변경 및 저장
3. Chrome Storage에 저장 확인
4. Extension 재시작 후 설정 유지 확인
5. 데이터 관리 기능 테스트
```

## 3. 디버깅 방법

### 3.1 Chrome DevTools 사용
```javascript
// Extension 디버깅
1. Extension 아이콘 우클릭 → "검사" 클릭
2. Console 탭에서 로그 확인
3. Network 탭에서 API 호출 확인
4. Sources 탭에서 코드 디버깅

// 콘텐츠 스크립트 디버깅
1. YouTube 페이지에서 F12
2. Console에서 content script 로그 확인
3. Elements 탭에서 오버레이 확인
```

### 3.2 로그 확인
```javascript
// Extension 로그 레벨 설정
const LOG_LEVEL = 'DEBUG'; // 'INFO', 'WARN', 'ERROR'

// 로그 출력 예시
console.log('[Info-Guard] Extension loaded');
console.log('[Info-Guard] Video detected:', videoId);
console.log('[Info-Guard] Analysis started');
console.log('[Info-Guard] WebSocket connected');
```

### 3.3 에러 처리
```javascript
// 에러 핸들링 예시
try {
    const result = await apiClient.analyzeVideo(videoId);
    console.log('Analysis result:', result);
} catch (error) {
    console.error('Analysis failed:', error);
    showErrorMessage('분석 중 오류가 발생했습니다.');
}
```

## 4. 전체 시스템 통합 테스트

### 4.1 시스템 구성 확인
```bash
# 1. AI 서비스 실행 확인
curl http://localhost:8000/health

# 2. Node.js 백엔드 실행 확인  
curl http://localhost:3000/health

# 3. Redis 연결 확인
redis-cli ping

# 4. PostgreSQL 연결 확인
psql -h localhost -U user -d infoguard -c "SELECT 1;"
```

### 4.2 End-to-End 테스트 시나리오
```javascript
// 전체 플로우 테스트
1. 모든 서비스 실행
   - AI Service (포트 8000)
   - Node.js Backend (포트 3000)
   - Redis (포트 6379)
   - PostgreSQL (포트 5432)

2. Chrome Extension 로드
   - Extension 설치 및 활성화
   - 아이콘 표시 확인

3. YouTube 비디오 분석
   - YouTube 비디오 페이지 접속
   - Extension 팝업에서 분석 시작
   - 실시간 진행률 확인
   - 최종 결과 표시 확인

4. 결과 검증
   - 신뢰도 점수 확인
   - 편향 분석 결과 확인
   - 팩트 체크 결과 확인
   - 오버레이 표시 확인
```

### 4.3 성능 테스트
```javascript
// 성능 테스트 시나리오
1. 응답 시간 측정
   - 분석 요청부터 결과까지 시간 측정
   - 목표: 30초 이내

2. 동시 사용자 테스트
   - 여러 탭에서 동시 분석
   - 시스템 안정성 확인

3. 메모리 사용량 확인
   - Extension 메모리 사용량 모니터링
   - 메모리 누수 확인
```

## 5. 테스트 체크리스트

### 5.1 Extension 로드 테스트
- [ ] Extension이 Chrome에 정상 로드됨
- [ ] 아이콘이 툴바에 표시됨
- [ ] 팝업이 정상적으로 열림
- [ ] 옵션 페이지 접근 가능
- [ ] 아이콘 파일들이 정상 로드됨

### 5.2 YouTube 통합 테스트
- [ ] YouTube 홈페이지에서 "YouTube 페이지가 아님" 메시지
- [ ] YouTube 비디오 페이지에서 분석 버튼 표시
- [ ] 비디오 ID 정상 추출
- [ ] 비디오 메타데이터 정상 로드
- [ ] 자막 데이터 정상 로드

### 5.3 분석 기능 테스트
- [ ] 분석 시작 버튼 동작
- [ ] 진행률 표시 정상
- [ ] 실시간 업데이트 동작
- [ ] 최종 결과 표시
- [ ] 에러 처리 정상

### 5.4 WebSocket 통신 테스트
- [ ] WebSocket 연결 성공
- [ ] 실시간 메시지 수신
- [ ] 연결 끊김 처리
- [ ] 재연결 시도
- [ ] 메시지 전송 성공

### 5.5 스토리지 테스트
- [ ] 설정 저장/로드
- [ ] 분석 결과 캐싱
- [ ] 데이터 관리 기능
- [ ] 스토리지 용량 확인
- [ ] 데이터 삭제 기능

### 5.6 UI/UX 테스트
- [ ] 팝업 UI 정상 표시
- [ ] 오버레이 정상 표시
- [ ] 반응형 디자인
- [ ] 다크모드 지원
- [ ] 접근성 확인

## 6. 문제 해결

### 6.1 일반적인 문제들
```javascript
// 1. Extension이 로드되지 않는 경우
- manifest.json 문법 오류 확인
- 필수 파일 누락 확인
- Chrome 버전 호환성 확인

// 2. YouTube 감지가 안 되는 경우
- content script 로드 확인
- YouTube URL 패턴 확인
- 비디오 ID 추출 로직 확인

// 3. API 호출이 실패하는 경우
- AI 서비스 실행 상태 확인
- CORS 설정 확인
- 네트워크 연결 확인

// 4. WebSocket 연결 실패
- AI 서비스 WebSocket 엔드포인트 확인
- 방화벽 설정 확인
- 포트 충돌 확인
```

### 6.2 디버깅 명령어
```bash
# AI 서비스 상태 확인
curl -X GET http://localhost:8000/health

# WebSocket 연결 테스트
wscat -c ws://localhost:8000/ws/analysis/test

# Extension 로그 확인
# Chrome DevTools → Console 탭

# 네트워크 요청 확인
# Chrome DevTools → Network 탭
```

## 7. 성공 지표

### 7.1 기능적 지표
- Extension 로드 성공률: 100%
- YouTube 감지 정확도: 95% 이상
- 분석 완료율: 90% 이상
- 사용자 만족도: 4.0/5.0 이상

### 7.2 기술적 지표
- 응답 시간: 30초 이내
- 에러율: 5% 이하
- 메모리 사용량: 50MB 이하
- CPU 사용률: 10% 이하

---

**참고**: 이 가이드를 따라 Chrome Extension을 안전하고 효율적으로 테스트할 수 있습니다. 