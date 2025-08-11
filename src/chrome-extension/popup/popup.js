/**
 * Info-Guard Chrome Extension 팝업 스크립트
 * YouTube 영상 신뢰도 분석 및 결과 표시
 */

// Info-Guard Chrome Extension 팝업 로직
class InfoGuardPopup {
  constructor() {
    this.currentVideoId = null;
    this.analysisResults = null;
    this.isAnalyzing = false;
    
    this.init();
  }

  async init() {
    try {
      // DOM 요소들 초기화
      this.initializeElements();
      
      // 현재 YouTube 페이지에서 비디오 정보 가져오기
      await this.getCurrentVideoInfo();
      
      // 이벤트 리스너 등록
      this.bindEventListeners();
      
      // 초기 상태 설정
      this.updateUI();
      
    } catch (error) {
      console.error('팝업 초기화 오류:', error);
      this.showError('팝업을 초기화할 수 없습니다.');
    }
  }

  initializeElements() {
    // DOM 요소들 캐시
    this.elements = {
      analyzeBtn: document.getElementById('analyze-btn'),
      statusIndicator: document.getElementById('status-indicator'),
      statusText: document.getElementById('status-text'),
      videoInfo: document.getElementById('video-info'),
      resultsContainer: document.getElementById('results-container'),
      loadingContainer: document.getElementById('loading-container'),
      errorContainer: document.getElementById('error-container'),
      settingsLink: document.getElementById('settings-link')
    };
  }

  async getCurrentVideoInfo() {
    try {
      // 현재 활성 탭에서 YouTube 비디오 정보 가져오기
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.url || !tab.url.includes('youtube.com/watch')) {
        throw new Error('YouTube 비디오 페이지가 아닙니다.');
      }

      // URL에서 비디오 ID 추출
      const videoId = this.extractVideoId(tab.url);
      if (!videoId) {
        throw new Error('비디오 ID를 찾을 수 없습니다.');
      }

      this.currentVideoId = videoId;
      
      // 콘텐츠 스크립트에서 비디오 메타데이터 가져오기
      const videoData = await this.getVideoMetadata(tab.id);
      this.displayVideoInfo(videoData);
      
    } catch (error) {
      console.error('비디오 정보 가져오기 오류:', error);
      this.showError('YouTube 비디오 정보를 가져올 수 없습니다.');
    }
  }

  extractVideoId(url) {
    const match = url.match(/[?&]v=([^&]+)/);
    return match ? match[1] : null;
  }

  async getVideoMetadata(tabId) {
    try {
      const response = await chrome.tabs.sendMessage(tabId, {
        action: 'getVideoMetadata'
      });
      
      if (response && response.success) {
        return response.data;
      } else {
        throw new Error('비디오 메타데이터를 가져올 수 없습니다.');
      }
    } catch (error) {
      console.error('메타데이터 가져오기 오류:', error);
      // 기본 정보로 폴백
      return {
        title: '알 수 없는 비디오',
        channel: '알 수 없는 채널',
        duration: '알 수 없음'
      };
    }
  }

  displayVideoInfo(videoData) {
    if (!this.elements.videoInfo) return;
    
    this.elements.videoInfo.innerHTML = `
      <div class="video-details">
        <h3 class="video-title">${this.escapeHtml(videoData.title)}</h3>
        <p class="video-channel">채널: ${this.escapeHtml(videoData.channel)}</p>
        <p class="video-duration">길이: ${videoData.duration}</p>
      </div>
    `;
  }

  bindEventListeners() {
    // 분석 버튼 클릭 이벤트
    if (this.elements.analyzeBtn) {
      this.elements.analyzeBtn.addEventListener('click', () => {
        this.startAnalysis();
      });
    }

    // 설정 링크 클릭 이벤트
    if (this.elements.settingsLink) {
      this.elements.settingsLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.openOptionsPage();
      });
    }
  }

  async startAnalysis() {
    if (this.isAnalyzing || !this.currentVideoId) {
      return;
    }

    try {
      this.isAnalyzing = true;
      this.updateUI();
      
      // 분석 요청 전송
      const analysisResult = await this.requestAnalysis();
      
      if (analysisResult) {
        this.analysisResults = analysisResult;
        this.displayResults(analysisResult);
      }
      
    } catch (error) {
      console.error('분석 오류:', error);
      this.showError('영상 분석 중 오류가 발생했습니다.');
    } finally {
      this.isAnalyzing = false;
      this.updateUI();
    }
  }

  async requestAnalysis() {
    try {
      // 백그라운드 스크립트를 통해 분석 요청
      const response = await chrome.runtime.sendMessage({
        action: 'analyzeVideo',
        videoId: this.currentVideoId
      });

      if (response && response.success) {
        return response.data;
      } else {
        throw new Error(response?.error || '분석 요청에 실패했습니다.');
      }
      
    } catch (error) {
      console.error('분석 요청 오류:', error);
      throw error;
    }
  }

  displayResults(results) {
    if (!this.elements.resultsContainer) return;
    
    const credibilityScore = results.credibility_score || 0;
    const scoreGrade = this.getScoreGrade(credibilityScore);
    
    this.elements.resultsContainer.innerHTML = `
      <div class="credibility-score">
        <div class="score-label">신뢰도 점수</div>
        <div class="score-number">${credibilityScore}</div>
        <div class="score-grade ${scoreGrade}">${this.getScoreText(scoreGrade)}</div>
      </div>
      
      <div class="results">
        <div class="result-item">
          <div class="result-label">편향성 감지</div>
          <div class="result-value">${results.bias_score || 'N/A'}</div>
          <div class="result-description">${this.getBiasDescription(results.bias_score)}</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">감정 분석</div>
          <div class="result-value">${results.sentiment_score || 'N/A'}</div>
          <div class="result-description">${this.getSentimentDescription(results.sentiment_score)}</div>
        </div>
        
        <div class="result-item">
          <div class="result-label">콘텐츠 품질</div>
          <div class="result-value">${results.content_quality || 'N/A'}</div>
          <div class="result-description">${this.getQualityDescription(results.content_quality)}</div>
        </div>
      </div>
      
      <div class="feedback-section">
        <h4>이 분석 결과가 도움이 되었나요?</h4>
        <div class="feedback-buttons">
          <button class="feedback-btn positive" onclick="this.sendFeedback('positive')">👍 도움됨</button>
          <button class="feedback-btn negative" onclick="this.sendFeedback('negative')">👎 도움안됨</button>
        </div>
      </div>
    `;
    
    // 피드백 이벤트 리스너 등록
    this.bindFeedbackListeners();
  }

  getScoreGrade(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
  }

  getScoreText(grade) {
    const texts = {
      excellent: '매우 좋음',
      good: '좋음',
      fair: '보통',
      poor: '낮음'
    };
    return texts[grade] || '알 수 없음';
  }

  getBiasDescription(score) {
    if (!score) return '분석 불가';
    if (score < 30) return '편향성 낮음';
    if (score < 60) return '편향성 보통';
    return '편향성 높음';
  }

  getSentimentDescription(score) {
    if (!score) return '분석 불가';
    if (score < 0.3) return '부정적';
    if (score < 0.7) return '중립적';
    return '긍정적';
  }

  getQualityDescription(score) {
    if (!score) return '분석 불가';
    if (score < 0.4) return '낮음';
    if (score < 0.7) return '보통';
    return '높음';
  }

  bindFeedbackListeners() {
    const feedbackBtns = document.querySelectorAll('.feedback-btn');
    feedbackBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const feedbackType = e.target.classList.contains('positive') ? 'positive' : 'negative';
        this.sendFeedback(feedbackType);
      });
    });
  }

  async sendFeedback(feedbackType) {
    try {
      await chrome.runtime.sendMessage({
        action: 'sendFeedback',
        videoId: this.currentVideoId,
        feedbackType: feedbackType,
        analysisResults: this.analysisResults
      });
      
      // 피드백 확인 메시지 표시
      this.showFeedbackConfirmation(feedbackType);
      
    } catch (error) {
      console.error('피드백 전송 오류:', error);
    }
  }

  showFeedbackConfirmation(feedbackType) {
    const feedbackSection = document.querySelector('.feedback-section');
    if (feedbackSection) {
      feedbackSection.innerHTML = `
        <div class="feedback-confirmation">
          <p>피드백을 보내주셔서 감사합니다! 🎉</p>
        </div>
      `;
    }
  }

  updateUI() {
    // 상태 표시기 업데이트
    if (this.elements.statusIndicator) {
      this.elements.statusIndicator.className = `status-indicator ${this.getStatusClass()}`;
    }
    
    if (this.elements.statusText) {
      this.elements.statusText.textContent = this.getStatusText();
    }
    
    // 분석 버튼 상태 업데이트
    if (this.elements.analyzeBtn) {
      this.elements.analyzeBtn.disabled = this.isAnalyzing || !this.currentVideoId;
      this.elements.analyzeBtn.textContent = this.isAnalyzing ? '분석 중...' : '영상 분석하기';
    }
    
    // 로딩/결과 컨테이너 표시/숨김
    if (this.elements.loadingContainer) {
      this.elements.loadingContainer.style.display = this.isAnalyzing ? 'block' : 'none';
    }
    
    if (this.elements.resultsContainer) {
      this.elements.resultsContainer.style.display = 
        (this.analysisResults && !this.isAnalyzing) ? 'block' : 'none';
    }
  }

  getStatusClass() {
    if (this.isAnalyzing) return 'analyzing';
    if (this.analysisResults) return 'ready';
    if (!this.currentVideoId) return 'error';
    return 'ready';
  }

  getStatusText() {
    if (this.isAnalyzing) return '분석 중...';
    if (this.analysisResults) return '분석 완료';
    if (!this.currentVideoId) return 'YouTube 비디오를 찾을 수 없음';
    return '분석 준비됨';
  }

  showError(message) {
    if (this.elements.errorContainer) {
      this.elements.errorContainer.innerHTML = `
        <div class="error-message">
          <p>${this.escapeHtml(message)}</p>
          <button onclick="location.reload()">다시 시도</button>
        </div>
      `;
      this.elements.errorContainer.style.display = 'block';
    }
  }

  openOptionsPage() {
    chrome.runtime.openOptionsPage();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// DOM이 로드된 후 팝업 초기화
document.addEventListener('DOMContentLoaded', () => {
  new InfoGuardPopup();
});

// 전역 함수로 피드백 전송 (HTML에서 직접 호출)
window.sendFeedback = function(feedbackType) {
  // 이 함수는 popup.js에서 재정의됨
  console.log('피드백 전송:', feedbackType);
};
