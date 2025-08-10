# Chrome Extension 구현 가이드

## 개요
Info-Guard Chrome Extension은 YouTube 페이지에서 실시간으로 영상의 신뢰도를 분석하고 표시하는 브라우저 확장 프로그램입니다.

## 목표
1. YouTube 페이지 자동 감지 및 분석
2. 실시간 신뢰도 점수 표시
3. 상세 분석 결과 제공
4. 사용자 피드백 수집
5. 개인화된 설정 관리

## 기술 스택
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Chrome APIs**: Extension Manifest V3
- **통신**: WebSocket, HTTP API
- **스타일링**: Tailwind CSS
- **상태 관리**: Chrome Storage API

## 1. 기본 구조 설정

### 1.1 프로젝트 구조
```
src/chrome-extension/
├── manifest.json
├── popup/
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
├── content/
│   ├── content.js
│   ├── content.css
│   └── youtube-detector.js
├── background/
│   └── background.js
├── options/
│   ├── options.html
│   ├── options.css
│   └── options.js
├── assets/
│   ├── icons/
│   └── images/
└── utils/
    ├── api-client.js
    ├── websocket-client.js
    └── storage-manager.js
```

### 1.2 Manifest V3 설정
```json
{
  "manifest_version": 3,
  "name": "Info-Guard",
  "version": "1.0.0",
  "description": "YouTube 영상 신뢰도 분석 도구",
  "permissions": [
    "activeTab",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "https://www.youtube.com/*",
    "http://localhost:8000/*"
  ],
  "background": {
    "service_worker": "background/background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://www.youtube.com/*"],
      "js": ["content/content.js"],
      "css": ["content/content.css"]
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_title": "Info-Guard"
  },
  "options_page": "options/options.html",
  "icons": {
    "16": "assets/icons/icon16.png",
    "48": "assets/icons/icon48.png",
    "128": "assets/icons/icon128.png"
  }
}
```

## 2. YouTube 페이지 통합

### 2.1 YouTube 비디오 감지
```javascript
// content/youtube-detector.js
class YouTubeDetector {
  constructor() {
    this.currentVideoId = null;
    this.observer = null;
    this.init();
  }

  init() {
    // YouTube 페이지 변경 감지
    this.observePageChanges();
    // 초기 비디오 ID 확인
    this.checkCurrentVideo();
  }

  observePageChanges() {
    this.observer = new MutationObserver(() => {
      this.checkCurrentVideo();
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  checkCurrentVideo() {
    const videoId = this.extractVideoId();
    if (videoId && videoId !== this.currentVideoId) {
      this.currentVideoId = videoId;
      this.onVideoChanged(videoId);
    }
  }

  extractVideoId() {
    // URL에서 비디오 ID 추출
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('v');
  }

  onVideoChanged(videoId) {
    // 비디오 변경 이벤트 발생
    chrome.runtime.sendMessage({
      type: 'VIDEO_CHANGED',
      videoId: videoId
    });
  }
}
```

### 2.2 신뢰도 표시 UI
```javascript
// content/content.js
class CredibilityUI {
  constructor() {
    this.overlay = null;
    this.scoreDisplay = null;
    this.init();
  }

  init() {
    this.createOverlay();
    this.injectStyles();
  }

  createOverlay() {
    this.overlay = document.createElement('div');
    this.overlay.id = 'info-guard-overlay';
    this.overlay.className = 'info-guard-overlay';
    
    this.scoreDisplay = document.createElement('div');
    this.scoreDisplay.className = 'credibility-score';
    
    this.overlay.appendChild(this.scoreDisplay);
    document.body.appendChild(this.overlay);
  }

  updateScore(score, grade) {
    this.scoreDisplay.innerHTML = `
      <div class="score-container">
        <div class="score-value">${score}</div>
        <div class="score-grade">${grade}</div>
        <div class="score-label">신뢰도</div>
      </div>
    `;
    
    this.scoreDisplay.className = `credibility-score grade-${grade.toLowerCase()}`;
  }

  showLoading() {
    this.scoreDisplay.innerHTML = `
      <div class="loading-container">
        <div class="spinner"></div>
        <div class="loading-text">분석 중...</div>
      </div>
    `;
  }

  showError(message) {
    this.scoreDisplay.innerHTML = `
      <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-text">${message}</div>
      </div>
    `;
  }
}
```

## 3. API 통신 및 WebSocket

### 3.1 API 클라이언트
```javascript
// utils/api-client.js
class APIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000';
  }

  async analyzeVideo(videoId, videoData) {
    try {
      const response = await fetch(`${this.baseURL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          video_id: videoId,
          transcript: videoData.transcript,
          metadata: videoData.metadata
        })
      });

      return await response.json();
    } catch (error) {
      console.error('API 요청 실패:', error);
      throw error;
    }
  }

  async submitFeedback(feedbackData) {
    try {
      const response = await fetch(`${this.baseURL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
      });

      return await response.json();
    } catch (error) {
      console.error('피드백 제출 실패:', error);
      throw error;
    }
  }

  async getChannelStats(channelId) {
    try {
      const response = await fetch(`${this.baseURL}/channel/${channelId}`);
      return await response.json();
    } catch (error) {
      console.error('채널 통계 조회 실패:', error);
      throw error;
    }
  }
}
```

### 3.2 WebSocket 클라이언트
```javascript
// utils/websocket-client.js
class WebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(videoId) {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`ws://localhost:8000/ws/analysis/${videoId}`);
        
        this.ws.onopen = () => {
          console.log('WebSocket 연결됨');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket 오류:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket 연결 해제');
          this.handleReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  handleMessage(data) {
    switch (data.event_type) {
      case 'analysis_started':
        this.onAnalysisStarted(data.data);
        break;
      case 'analysis_progress':
        this.onAnalysisProgress(data.data);
        break;
      case 'analysis_completed':
        this.onAnalysisCompleted(data.data);
        break;
      case 'analysis_error':
        this.onAnalysisError(data.data);
        break;
    }
  }

  onAnalysisStarted(data) {
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_STARTED',
      data: data
    });
  }

  onAnalysisProgress(data) {
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_PROGRESS',
      data: data
    });
  }

  onAnalysisCompleted(data) {
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_COMPLETED',
      data: data
    });
  }

  onAnalysisError(data) {
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_ERROR',
      data: data
    });
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect(this.currentVideoId);
      }, 1000 * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

## 4. 팝업 인터페이스

### 4.1 팝업 HTML
```html
<!-- popup/popup.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="popup-container">
    <div class="header">
      <h1>Info-Guard</h1>
      <div class="status-indicator" id="statusIndicator"></div>
    </div>

    <div class="current-video" id="currentVideo">
      <div class="video-info">
        <div class="video-title" id="videoTitle">비디오를 찾을 수 없습니다</div>
        <div class="video-channel" id="videoChannel"></div>
      </div>
    </div>

    <div class="analysis-section" id="analysisSection">
      <div class="credibility-score" id="credibilityScore">
        <div class="score-value">--</div>
        <div class="score-grade">?</div>
      </div>
      
      <div class="analysis-details" id="analysisDetails">
        <div class="detail-item">
          <span class="label">편향성:</span>
          <span class="value" id="biasScore">--</span>
        </div>
        <div class="detail-item">
          <span class="label">팩트 체크:</span>
          <span class="value" id="factCheckScore">--</span>
        </div>
        <div class="detail-item">
          <span class="label">출처 검증:</span>
          <span class="value" id="sourceScore">--</span>
        </div>
      </div>
    </div>

    <div class="progress-section" id="progressSection" style="display: none;">
      <div class="progress-bar">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <div class="progress-text" id="progressText">분석 준비 중...</div>
    </div>

    <div class="actions">
      <button id="analyzeBtn" class="btn-primary">분석 시작</button>
      <button id="feedbackBtn" class="btn-secondary">피드백</button>
      <button id="optionsBtn" class="btn-secondary">설정</button>
    </div>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

### 4.2 팝업 JavaScript
```javascript
// popup/popup.js
class PopupManager {
  constructor() {
    this.currentVideoId = null;
    this.apiClient = new APIClient();
    this.init();
  }

  async init() {
    this.bindEvents();
    await this.loadCurrentVideo();
    await this.loadSettings();
  }

  bindEvents() {
    document.getElementById('analyzeBtn').addEventListener('click', () => {
      this.startAnalysis();
    });

    document.getElementById('feedbackBtn').addEventListener('click', () => {
      this.showFeedbackDialog();
    });

    document.getElementById('optionsBtn').addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });
  }

  async loadCurrentVideo() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (tab.url.includes('youtube.com/watch')) {
        const videoId = this.extractVideoId(tab.url);
        if (videoId) {
          this.currentVideoId = videoId;
          await this.loadVideoInfo(videoId);
        }
      }
    } catch (error) {
      console.error('현재 비디오 로드 실패:', error);
    }
  }

  async loadVideoInfo(videoId) {
    try {
      // YouTube API를 통해 비디오 정보 가져오기
      const videoInfo = await this.getYouTubeVideoInfo(videoId);
      
      document.getElementById('videoTitle').textContent = videoInfo.title;
      document.getElementById('videoChannel').textContent = videoInfo.channelTitle;
      
      // 저장된 분석 결과가 있는지 확인
      const savedResult = await this.getSavedAnalysis(videoId);
      if (savedResult) {
        this.displayAnalysisResult(savedResult);
      }
    } catch (error) {
      console.error('비디오 정보 로드 실패:', error);
    }
  }

  async startAnalysis() {
    if (!this.currentVideoId) {
      this.showMessage('YouTube 비디오 페이지에서만 분석할 수 있습니다.');
      return;
    }

    try {
      this.showProgress();
      
      // 백그라운드 스크립트에 분석 요청
      chrome.runtime.sendMessage({
        type: 'START_ANALYSIS',
        videoId: this.currentVideoId
      });

    } catch (error) {
      console.error('분석 시작 실패:', error);
      this.showError('분석을 시작할 수 없습니다.');
    }
  }

  displayAnalysisResult(result) {
    const score = result.overall_score || 0;
    const grade = this.calculateGrade(score);
    
    document.getElementById('credibilityScore').innerHTML = `
      <div class="score-value">${Math.round(score)}</div>
      <div class="score-grade">${grade}</div>
    `;

    document.getElementById('biasScore').textContent = 
      result.analysis_results?.bias?.score || '--';
    document.getElementById('factCheckScore').textContent = 
      result.analysis_results?.fact_check?.score || '--';
    document.getElementById('sourceScore').textContent = 
      result.analysis_results?.source_validation?.score || '--';

    // 점수에 따른 색상 변경
    document.getElementById('credibilityScore').className = 
      `credibility-score grade-${grade.toLowerCase()}`;
  }

  calculateGrade(score) {
    if (score >= 80) return 'A';
    if (score >= 60) return 'B';
    if (score >= 40) return 'C';
    if (score >= 20) return 'D';
    return 'F';
  }

  showProgress() {
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('analysisSection').style.display = 'none';
  }

  showMessage(message) {
    // 간단한 메시지 표시
    const messageEl = document.createElement('div');
    messageEl.className = 'message';
    messageEl.textContent = message;
    document.body.appendChild(messageEl);
    
    setTimeout(() => {
      messageEl.remove();
    }, 3000);
  }

  showError(message) {
    this.showMessage(`오류: ${message}`);
  }
}

// 팝업 초기화
document.addEventListener('DOMContentLoaded', () => {
  new PopupManager();
});
```

## 5. 백그라운드 스크립트

### 5.1 백그라운드 서비스
```javascript
// background/background.js
class BackgroundService {
  constructor() {
    this.currentAnalysis = null;
    this.wsClient = new WebSocketClient();
    this.apiClient = new APIClient();
    this.init();
  }

  init() {
    this.setupMessageListeners();
    this.setupTabListeners();
  }

  setupMessageListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      switch (message.type) {
        case 'START_ANALYSIS':
          this.handleStartAnalysis(message.videoId);
          break;
        case 'ANALYSIS_PROGRESS':
          this.handleAnalysisProgress(message.data);
          break;
        case 'ANALYSIS_COMPLETED':
          this.handleAnalysisCompleted(message.data);
          break;
        case 'SUBMIT_FEEDBACK':
          this.handleSubmitFeedback(message.data);
          break;
      }
    });
  }

  setupTabListeners() {
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (changeInfo.status === 'complete' && tab.url?.includes('youtube.com/watch')) {
        this.onYouTubeVideoLoaded(tabId, tab);
      }
    });
  }

  async handleStartAnalysis(videoId) {
    try {
      // 이전 분석 중지
      if (this.currentAnalysis) {
        this.currentAnalysis.cancel();
      }

      // 새로운 분석 시작
      this.currentAnalysis = new AnalysisSession(videoId, this.wsClient, this.apiClient);
      await this.currentAnalysis.start();

    } catch (error) {
      console.error('분석 시작 실패:', error);
      this.notifyError('분석을 시작할 수 없습니다.');
    }
  }

  async handleAnalysisProgress(data) {
    // 팝업에 진행률 업데이트 전송
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_PROGRESS',
      data: data
    });
  }

  async handleAnalysisCompleted(data) {
    // 분석 결과 저장
    await this.saveAnalysisResult(data);
    
    // 팝업에 완료 알림
    chrome.runtime.sendMessage({
      type: 'ANALYSIS_COMPLETED',
      data: data
    });
  }

  async handleSubmitFeedback(data) {
    try {
      const result = await this.apiClient.submitFeedback(data);
      if (result.success) {
        this.notifySuccess('피드백이 제출되었습니다.');
      } else {
        this.notifyError('피드백 제출에 실패했습니다.');
      }
    } catch (error) {
      console.error('피드백 제출 실패:', error);
      this.notifyError('피드백 제출 중 오류가 발생했습니다.');
    }
  }

  async saveAnalysisResult(result) {
    try {
      await chrome.storage.local.set({
        [`analysis_${result.video_id}`]: {
          ...result,
          timestamp: Date.now()
        }
      });
    } catch (error) {
      console.error('분석 결과 저장 실패:', error);
    }
  }

  notifySuccess(message) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'assets/icons/icon48.png',
      title: 'Info-Guard',
      message: message
    });
  }

  notifyError(message) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'assets/icons/icon48.png',
      title: 'Info-Guard 오류',
      message: message
    });
  }
}

// 백그라운드 서비스 초기화
new BackgroundService();
```

## 6. 설정 페이지

### 6.1 설정 HTML
```html
<!-- options/options.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Info-Guard 설정</title>
  <link rel="stylesheet" href="options.css">
</head>
<body>
  <div class="options-container">
    <h1>Info-Guard 설정</h1>
    
    <div class="section">
      <h2>일반 설정</h2>
      <div class="setting-item">
        <label>
          <input type="checkbox" id="autoAnalyze">
          자동 분석 활성화
        </label>
        <p class="description">YouTube 비디오 페이지에 접속하면 자동으로 분석을 시작합니다.</p>
      </div>
      
      <div class="setting-item">
        <label>
          <input type="checkbox" id="showOverlay">
          오버레이 표시
        </label>
        <p class="description">YouTube 페이지에 신뢰도 점수를 오버레이로 표시합니다.</p>
      </div>
    </div>

    <div class="section">
      <h2>분석 설정</h2>
      <div class="setting-item">
        <label for="analysisLevel">분석 수준:</label>
        <select id="analysisLevel">
          <option value="basic">기본</option>
          <option value="detailed">상세</option>
          <option value="comprehensive">종합</option>
        </select>
      </div>
      
      <div class="setting-item">
        <label for="apiEndpoint">API 서버:</label>
        <input type="text" id="apiEndpoint" placeholder="http://localhost:8000">
      </div>
    </div>

    <div class="section">
      <h2>알림 설정</h2>
      <div class="setting-item">
        <label>
          <input type="checkbox" id="enableNotifications">
          알림 활성화
        </label>
      </div>
      
      <div class="setting-item">
        <label for="notificationThreshold">알림 임계값:</label>
        <select id="notificationThreshold">
          <option value="all">모든 분석</option>
          <option value="low">낮은 신뢰도만</option>
          <option value="critical">위험한 콘텐츠만</option>
        </select>
      </div>
    </div>

    <div class="actions">
      <button id="saveBtn" class="btn-primary">저장</button>
      <button id="resetBtn" class="btn-secondary">초기화</button>
    </div>
  </div>

  <script src="options.js"></script>
</body>
</html>
```

## 7. 구현 단계별 계획

### Step 1: 기본 구조 설정
1. 프로젝트 디렉토리 생성
2. Manifest V3 설정
3. 기본 파일 구조 생성

### Step 2: YouTube 페이지 통합
1. YouTube 비디오 감지 로직
2. 신뢰도 표시 UI 구현
3. 페이지 변경 감지

### Step 3: API 통신 구현
1. API 클라이언트 구현
2. WebSocket 연결 설정
3. 실시간 분석 통신

### Step 4: 팝업 인터페이스
1. 팝업 UI 디자인
2. 분석 결과 표시
3. 사용자 상호작용

### Step 5: 백그라운드 서비스
1. 메시지 처리 로직
2. 분석 세션 관리
3. 결과 저장 및 캐싱

### Step 6: 설정 및 옵션
1. 설정 페이지 구현
2. 사용자 설정 저장
3. 개인화 기능

## 8. 성공 지표

### 기능적 지표
- [ ] YouTube 페이지 자동 감지
- [ ] 실시간 신뢰도 표시
- [ ] 분석 결과 캐싱
- [ ] 사용자 피드백 수집
- [ ] 설정 페이지 완성

### 기술적 지표
- [ ] 페이지 로드 후 3초 내 분석 시작
- [ ] WebSocket 연결 안정성 > 95%
- [ ] 메모리 사용량 < 50MB
- [ ] 사용자 만족도 > 4.0/5.0

## 9. 다음 단계
Chrome Extension 완료 후:
- 모바일 앱 개발
- 서버 확장 및 최적화
- 다국어 지원
- 고급 보안 기능

---

# Chrome Extension 구현 시작! 🚀

이제 YouTube 페이지에서 실시간으로 영상의 신뢰도를 분석하고 표시하는 Chrome Extension을 개발하겠습니다. 