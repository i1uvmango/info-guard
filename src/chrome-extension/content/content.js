// Info-Guard Chrome Extension 콘텐츠 스크립트
class InfoGuardContentScript {
  constructor() {
    this.videoId = null;
    this.videoData = null;
    this.analysisResult = null;
    this.isAnalyzing = false;
    this.overlayElement = null;
    
    this.init();
  }

  async init() {
    try {
      // YouTube 페이지인지 확인
      if (!this.isYouTubePage()) {
        return;
      }

      // 비디오 ID 추출
      this.videoId = this.extractVideoId();
      if (!this.videoId) {
        return;
      }

      // 비디오 메타데이터 수집
      await this.collectVideoMetadata();
      
      // 메시지 리스너 등록
      this.setupMessageListener();
      
      // 페이지 변경 감지
      this.setupPageChangeDetection();
      
      // 초기 UI 요소 추가
      this.addInfoGuardUI();
      
    } catch (error) {
      console.error('Info-Guard 콘텐츠 스크립트 초기화 오류:', error);
    }
  }

  isYouTubePage() {
    return window.location.hostname === 'www.youtube.com' || 
           window.location.hostname === 'youtube.com';
  }

  extractVideoId() {
    const url = window.location.href;
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
  }

  async collectVideoMetadata() {
    try {
      // 비디오 제목
      const titleElement = document.querySelector('h1.ytd-video-primary-info-renderer') ||
                          document.querySelector('h1.title') ||
                          document.querySelector('h1');
      
      const title = titleElement ? titleElement.textContent.trim() : '알 수 없는 제목';
      
      // 채널명
      const channelElement = document.querySelector('a.ytd-video-owner-renderer') ||
                            document.querySelector('.ytd-channel-name a') ||
                            document.querySelector('.ytd-video-owner-renderer a');
      
      const channel = channelElement ? channelElement.textContent.trim() : '알 수 없는 채널';
      
      // 비디오 길이
      const durationElement = document.querySelector('.ytp-time-duration') ||
                              document.querySelector('.ytd-video-primary-info-renderer .ytd-video-primary-info-renderer');
      
      const duration = durationElement ? durationElement.textContent.trim() : '알 수 없음';
      
      // 조회수
      const viewCountElement = document.querySelector('.view-count') ||
                               document.querySelector('.ytd-video-primary-info-renderer .view-count');
      
      const viewCount = viewCountElement ? viewCountElement.textContent.trim() : '알 수 없음';
      
      // 업로드 날짜
      const dateElement = document.querySelector('.date') ||
                          document.querySelector('.ytd-video-primary-info-renderer .date');
      
      const uploadDate = dateElement ? dateElement.textContent.trim() : '알 수 없음';
      
      // 설명
      const descriptionElement = document.querySelector('#description') ||
                                 document.querySelector('.ytd-video-secondary-info-renderer #description');
      
      const description = descriptionElement ? descriptionElement.textContent.trim() : '';
      
      this.videoData = {
        id: this.videoId,
        title: title,
        channel: channel,
        duration: duration,
        viewCount: viewCount,
        uploadDate: uploadDate,
        description: description,
        url: window.location.href
      };
      
      console.log('비디오 메타데이터 수집 완료:', this.videoData);
      
    } catch (error) {
      console.error('비디오 메타데이터 수집 오류:', error);
      this.videoData = {
        id: this.videoId,
        title: '알 수 없는 제목',
        channel: '알 수 없는 채널',
        duration: '알 수 없음',
        viewCount: '알 수 없음',
        uploadDate: '알 수 없음',
        description: '',
        url: window.location.href
      };
    }
  }

  setupMessageListener() {
    // 팝업에서 오는 메시지 처리
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'getVideoMetadata') {
        sendResponse({
          success: true,
          data: this.videoData
        });
        return true;
      }
      
      if (request.action === 'analyzeVideo') {
        this.startAnalysis().then(result => {
          sendResponse({
            success: true,
            data: result
          });
        }).catch(error => {
          sendResponse({
            success: false,
            error: error.message
          });
        });
        return true;
      }
    });
  }

  setupPageChangeDetection() {
    // YouTube SPA 페이지 변경 감지
    let currentUrl = window.location.href;
    
    const observer = new MutationObserver(() => {
      if (window.location.href !== currentUrl) {
        currentUrl = window.location.href;
        this.handlePageChange();
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // URL 변경 감지 (SPA 네비게이션)
    window.addEventListener('popstate', () => {
      this.handlePageChange();
    });
  }

  async handlePageChange() {
    // 기존 UI 요소 제거
    this.removeInfoGuardUI();
    
    // 새로운 비디오 ID 확인
    const newVideoId = this.extractVideoId();
    
    if (newVideoId && newVideoId !== this.videoId) {
      this.videoId = newVideoId;
      this.analysisResult = null;
      this.isAnalyzing = false;
      
      // 새로운 비디오 메타데이터 수집
      await this.collectVideoMetadata();
      
      // 새로운 UI 요소 추가
      this.addInfoGuardUI();
    }
  }

  addInfoGuardUI() {
    try {
      // 기존 UI 제거
      this.removeInfoGuardUI();
      
      // 비디오 제목 아래에 Info-Guard 오버레이 추가
      const titleContainer = document.querySelector('h1.ytd-video-primary-info-renderer') ||
                            document.querySelector('h1.title') ||
                            document.querySelector('h1');
      
      if (titleContainer) {
        this.overlayElement = this.createInfoGuardOverlay();
        titleContainer.parentNode.insertBefore(this.overlayElement, titleContainer.nextSibling);
      }
      
    } catch (error) {
      console.error('Info-Guard UI 추가 오류:', error);
    }
  }

  createInfoGuardOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'info-guard-overlay';
    overlay.innerHTML = `
      <div class="info-guard-container">
        <div class="info-guard-header">
          <span class="info-guard-logo">🛡️ Info-Guard</span>
          <span class="info-guard-status" id="info-guard-status">분석 준비됨</span>
        </div>
        
        <div class="info-guard-content">
          <div class="credibility-display" id="credibility-display">
            <div class="credibility-score" id="credibility-score">--</div>
            <div class="credibility-label">신뢰도 점수</div>
          </div>
          
          <div class="analysis-button-container">
            <button class="analyze-button" id="analyze-button">
              <span class="button-text">영상 분석하기</span>
              <span class="button-icon">🔍</span>
            </button>
          </div>
          
          <div class="analysis-details" id="analysis-details" style="display: none;">
            <div class="detail-item">
              <span class="detail-label">편향성:</span>
              <span class="detail-value" id="bias-value">--</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">감정:</span>
              <span class="detail-value" id="sentiment-value">--</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">품질:</span>
              <span class="detail-value" id="quality-value">--</span>
            </div>
          </div>
        </div>
        
        <div class="info-guard-footer">
          <a href="#" class="info-guard-link" id="info-guard-link">자세한 분석 보기</a>
        </div>
      </div>
    `;
    
    // 이벤트 리스너 등록
    this.bindOverlayEvents(overlay);
    
    return overlay;
  }

  bindOverlayEvents(overlay) {
    // 분석 버튼 클릭 이벤트
    const analyzeButton = overlay.querySelector('#analyze-button');
    if (analyzeButton) {
      analyzeButton.addEventListener('click', () => {
        this.startAnalysis();
      });
    }
    
    // 자세한 분석 링크 클릭 이벤트
    const detailLink = overlay.querySelector('#info-guard-link');
    if (detailLink) {
      detailLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.openDetailedAnalysis();
      });
    }
  }

  async startAnalysis() {
    if (this.isAnalyzing) {
      return;
    }
    
    try {
      this.isAnalyzing = true;
      this.updateAnalysisUI('분석 중...', 'analyzing');
      
      // 백그라운드 스크립트를 통해 분석 요청
      const response = await chrome.runtime.sendMessage({
        action: 'analyzeVideo',
        videoId: this.videoId,
        videoData: this.videoData
      });
      
      if (response && response.success) {
        this.analysisResult = response.data;
        this.displayAnalysisResult(response.data);
        this.updateAnalysisUI('분석 완료', 'completed');
      } else {
        throw new Error(response?.error || '분석에 실패했습니다.');
      }
      
    } catch (error) {
      console.error('분석 오류:', error);
      this.updateAnalysisUI('분석 실패', 'error');
      this.showAnalysisError(error.message);
    } finally {
      this.isAnalyzing = false;
    }
  }

  updateAnalysisUI(status, state) {
    const statusElement = document.getElementById('info-guard-status');
    const analyzeButton = document.getElementById('analyze-button');
    
    if (statusElement) {
      statusElement.textContent = status;
      statusElement.className = `info-guard-status ${state}`;
    }
    
    if (analyzeButton) {
      if (state === 'analyzing') {
        analyzeButton.disabled = true;
        analyzeButton.querySelector('.button-text').textContent = '분석 중...';
        analyzeButton.querySelector('.button-icon').textContent = '⏳';
      } else {
        analyzeButton.disabled = false;
        analyzeButton.querySelector('.button-text').textContent = '영상 분석하기';
        analyzeButton.querySelector('.button-icon').textContent = '🔍';
      }
    }
  }

  displayAnalysisResult(results) {
    // 신뢰도 점수 표시
    const credibilityScore = document.getElementById('credibility-score');
    if (credibilityScore) {
      credibilityScore.textContent = results.credibility_score || '--';
      credibilityScore.className = `credibility-score ${this.getScoreClass(results.credibility_score)}`;
    }
    
    // 상세 분석 결과 표시
    const analysisDetails = document.getElementById('analysis-details');
    if (analysisDetails) {
      const biasValue = document.getElementById('bias-value');
      const sentimentValue = document.getElementById('sentiment-value');
      const qualityValue = document.getElementById('quality-value');
      
      if (biasValue) biasValue.textContent = results.bias_score || '--';
      if (sentimentValue) sentimentValue.textContent = results.sentiment_score || '--';
      if (qualityValue) qualityValue.textContent = results.content_quality || '--';
      
      analysisDetails.style.display = 'block';
    }
  }

  getScoreClass(score) {
    if (!score) return 'unknown';
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
  }

  showAnalysisError(message) {
    const analysisDetails = document.getElementById('analysis-details');
    if (analysisDetails) {
      analysisDetails.innerHTML = `
        <div class="analysis-error">
          <span class="error-icon">⚠️</span>
          <span class="error-message">${message}</span>
        </div>
      `;
      analysisDetails.style.display = 'block';
    }
  }

  openDetailedAnalysis() {
    // 팝업 열기
    chrome.runtime.sendMessage({
      action: 'openPopup'
    });
  }

  removeInfoGuardUI() {
    if (this.overlayElement && this.overlayElement.parentNode) {
      this.overlayElement.parentNode.removeChild(this.overlayElement);
      this.overlayElement = null;
    }
  }
}

// 페이지 로드 완료 후 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new InfoGuardContentScript();
  });
} else {
  new InfoGuardContentScript();
}

// YouTube 동적 콘텐츠 로딩 대기
const waitForYouTubeContent = () => {
  if (document.querySelector('h1') || document.querySelector('.ytd-video-primary-info-renderer')) {
    new InfoGuardContentScript();
  } else {
    setTimeout(waitForYouTubeContent, 1000);
  }
};

// 페이지 로드 후 YouTube 콘텐츠 대기
setTimeout(waitForYouTubeContent, 2000);
