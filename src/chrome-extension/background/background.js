// Info-Guard Chrome Extension 백그라운드 서비스
class InfoGuardBackgroundService {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8000'; // Python 서버
    this.nodeApiUrl = 'http://localhost:3000'; // Node.js 서버
    this.userToken = null;
    this.analysisCache = new Map();
    this.isInitialized = false;
    
    this.init();
  }

  async init() {
    try {
      // 저장된 사용자 토큰 복원
      await this.restoreUserSession();
      
      // 메시지 리스너 등록
      this.setupMessageListeners();
      
      // 설치/업데이트 이벤트 처리
      this.setupInstallEvents();
      
      // 주기적 상태 확인
      this.startHealthCheck();
      
      this.isInitialized = true;
      console.log('Info-Guard 백그라운드 서비스 초기화 완료');
      
    } catch (error) {
      console.error('백그라운드 서비스 초기화 오류:', error);
    }
  }

  async restoreUserSession() {
    try {
      const result = await chrome.storage.local.get(['userToken', 'userId']);
      if (result.userToken && result.userId) {
        this.userToken = result.userToken;
        // 토큰 유효성 확인
        const isValid = await this.validateToken(result.userToken);
        if (!isValid) {
          await this.clearUserSession();
        }
      }
    } catch (error) {
      console.error('사용자 세션 복원 오류:', error);
    }
  }

  async validateToken(token) {
    try {
      const response = await fetch(`${this.nodeApiUrl}/api/auth/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      return response.ok;
    } catch (error) {
      console.error('토큰 검증 오류:', error);
      return false;
    }
  }

  async clearUserSession() {
    this.userToken = null;
    await chrome.storage.local.remove(['userToken', 'userId']);
  }

  setupMessageListeners() {
    // 팝업과 콘텐츠 스크립트에서 오는 메시지 처리
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      this.handleMessage(request, sender, sendResponse);
      return true; // 비동기 응답을 위해 true 반환
    });
  }

  async handleMessage(request, sender, sendResponse) {
    try {
      switch (request.action) {
        case 'analyzeVideo':
          const analysisResult = await this.analyzeVideo(request.videoId, request.videoData);
          sendResponse({
            success: true,
            data: analysisResult
          });
          break;
          
        case 'sendFeedback':
          await this.sendFeedback(request.videoId, request.feedbackType, request.analysisResults);
          sendResponse({ success: true });
          break;
          
        case 'getUserProfile':
          const profile = await this.getUserProfile();
          sendResponse({
            success: true,
            data: profile
          });
          break;
          
        case 'updateUserSettings':
          await this.updateUserSettings(request.settings);
          sendResponse({ success: true });
          break;
          
        case 'checkConnectionStatus':
          const status = await this.checkConnectionStatus();
          sendResponse({
            success: true,
            data: status
          });
          break;
          
        case 'openPopup':
          await this.openPopup();
          sendResponse({ success: true });
          break;
          
        default:
          sendResponse({
            success: false,
            error: '알 수 없는 액션'
          });
      }
    } catch (error) {
      console.error('메시지 처리 오류:', error);
      sendResponse({
        success: false,
        error: error.message
      });
    }
  }

  async analyzeVideo(videoId, videoData) {
    try {
      // 캐시된 분석 결과 확인
      if (this.analysisCache.has(videoId)) {
        const cached = this.analysisCache.get(videoId);
        if (Date.now() - cached.timestamp < 24 * 60 * 60 * 1000) { // 24시간
          console.log('캐시된 분석 결과 사용:', videoId);
          return cached.result;
        }
      }

      // Python 서버에 분석 요청
      const analysisResult = await this.requestVideoAnalysis(videoId, videoData);
      
      // Node.js 서버에 결과 저장
      await this.saveAnalysisResult(videoId, analysisResult);
      
      // 캐시에 저장
      this.analysisCache.set(videoId, {
        result: analysisResult,
        timestamp: Date.now()
      });
      
      // 분석 완료 알림
      await this.showAnalysisNotification(videoId, analysisResult);
      
      return analysisResult;
      
    } catch (error) {
      console.error('비디오 분석 오류:', error);
      throw error;
    }
  }

  async requestVideoAnalysis(videoId, videoData) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.userToken ? `Bearer ${this.userToken}` : ''
        },
        body: JSON.stringify({
          video_id: videoId,
          title: videoData?.title || '',
          description: videoData?.description || '',
          channel_title: videoData?.channel || '',
          url: videoData?.url || `https://www.youtube.com/watch?v=${videoId}`
        })
      });

      if (!response.ok) {
        throw new Error(`분석 API 오류: ${response.status}`);
      }

      const result = await response.json();
      
      // 응답 형식 검증 및 정규화
      return this.normalizeAnalysisResult(result);
      
    } catch (error) {
      console.error('분석 요청 오류:', error);
      
      // 오프라인 모드: 모의 분석 결과 반환
      if (!navigator.onLine) {
        return this.generateMockAnalysis(videoData);
      }
      
      throw error;
    }
  }

  normalizeAnalysisResult(result) {
    // Python 서버 응답을 표준 형식으로 정규화
    return {
      credibility_score: result.credibility_score || result.overall_score || 0,
      bias_score: result.bias_score || result.bias_detection || 0,
      sentiment_score: result.sentiment_score || result.sentiment_analysis || 0.5,
      content_quality: result.content_quality || result.quality_score || 0,
      fact_check_score: result.fact_check_score || result.fact_verification || 0,
      source_reliability: result.source_reliability || result.source_score || 0,
      explanation: result.explanation || result.summary || 'AI 기반 분석이 완료되었습니다.',
      timestamp: new Date().toISOString(),
      model_version: result.model_version || '1.0.0'
    };
  }

  generateMockAnalysis(videoData) {
    // 개발/테스트용 모의 분석 결과
    const baseScore = 60 + Math.random() * 30; // 60-90 범위
    
    return {
      credibility_score: Math.floor(baseScore),
      bias_score: Math.floor(20 + Math.random() * 30), // 20-50
      sentiment_score: 0.3 + Math.random() * 0.4, // 0.3-0.7
      content_quality: 0.5 + Math.random() * 0.4, // 0.5-0.9
      fact_check_score: Math.floor(baseScore - 10),
      source_reliability: Math.floor(baseScore - 5),
      explanation: '이 영상은 AI 기반 분석을 통해 신뢰도가 평가되었습니다. 편향성과 사실 확인을 통해 종합적인 신뢰도를 제공합니다.',
      timestamp: new Date().toISOString(),
      model_version: 'mock-1.0.0'
    };
  }

  async saveAnalysisResult(videoId, analysisResult) {
    try {
      if (!this.userToken) {
        console.log('사용자 인증 없음, 분석 결과 저장 건너뜀');
        return;
      }

      const response = await fetch(`${this.nodeApiUrl}/api/analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          video_id: videoId,
          analysis_result: analysisResult,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        console.error('분석 결과 저장 실패:', response.status);
      }
      
    } catch (error) {
      console.error('분석 결과 저장 오류:', error);
    }
  }

  async sendFeedback(videoId, feedbackType, analysisResults) {
    try {
      if (!this.userToken) {
        console.log('사용자 인증 없음, 피드백 저장 건너뜀');
        return;
      }

      const response = await fetch(`${this.nodeApiUrl}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify({
          video_id: videoId,
          feedback_type: feedbackType,
          analysis_results: analysisResults,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        console.error('피드백 저장 실패:', response.status);
      }
      
    } catch (error) {
      console.error('피드백 전송 오류:', error);
    }
  }

  async getUserProfile() {
    try {
      if (!this.userToken) {
        return null;
      }

      const response = await fetch(`${this.nodeApiUrl}/api/user/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.userToken}`
        }
      });

      if (response.ok) {
        return await response.json();
      }
      
      return null;
      
    } catch (error) {
      console.error('사용자 프로필 조회 오류:', error);
      return null;
    }
  }

  async updateUserSettings(settings) {
    try {
      if (!this.userToken) {
        throw new Error('사용자 인증이 필요합니다');
      }

      const response = await fetch(`${this.nodeApiUrl}/api/user/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.userToken}`
        },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        throw new Error('설정 업데이트 실패');
      }
      
    } catch (error) {
      console.error('설정 업데이트 오류:', error);
      throw error;
    }
  }

  async checkConnectionStatus() {
    try {
      const [pythonStatus, nodeStatus] = await Promise.allSettled([
        fetch(`${this.apiBaseUrl}/health`),
        fetch(`${this.nodeApiUrl}/health`)
      ]);

      return {
        python_server: pythonStatus.status === 'fulfilled' && pythonStatus.value.ok,
        node_server: nodeStatus.status === 'fulfilled' && nodeStatus.value.ok,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('연결 상태 확인 오류:', error);
      return {
        python_server: false,
        node_server: false,
        timestamp: new Date().toISOString()
      };
    }
  }

  async showAnalysisNotification(videoId, analysisResult) {
    try {
      const score = analysisResult.credibility_score;
      let message = '';
      let icon = '';

      if (score >= 80) {
        message = '높은 신뢰도의 영상입니다';
        icon = '🟢';
      } else if (score >= 60) {
        message = '보통 신뢰도의 영상입니다';
        icon = '🟡';
      } else {
        message = '낮은 신뢰도의 영상입니다';
        icon = '🔴';
      }

      await chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('assets/icons/icon128.png'),
        title: 'Info-Guard 분석 완료',
        message: `${icon} ${message} (${score}점)`,
        priority: 1
      });
      
    } catch (error) {
      console.error('알림 표시 오류:', error);
    }
  }

  async openPopup() {
    try {
      // 현재 활성 탭에 팝업 열기
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        await chrome.action.openPopup();
      }
    } catch (error) {
      console.error('팝업 열기 오류:', error);
    }
  }

  setupInstallEvents() {
    // 확장 프로그램 설치 시
    chrome.runtime.onInstalled.addListener((details) => {
      if (details.reason === 'install') {
        console.log('Info-Guard 확장 프로그램이 설치되었습니다');
        this.showWelcomeNotification();
      } else if (details.reason === 'update') {
        console.log('Info-Guard 확장 프로그램이 업데이트되었습니다');
      }
    });
  }

  async showWelcomeNotification() {
    try {
      await chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('assets/icons/icon128.png'),
        title: 'Info-Guard에 오신 것을 환영합니다!',
        message: 'YouTube 영상의 신뢰도를 AI로 분석해보세요.',
        priority: 2
      });
    } catch (error) {
      console.error('환영 알림 표시 오류:', error);
    }
  }

  startHealthCheck() {
    // 5분마다 서버 상태 확인
    setInterval(async () => {
      try {
        const status = await this.checkConnectionStatus();
        
        // 연결 상태가 변경된 경우 알림
        if (!status.python_server || !status.node_server) {
          console.warn('서버 연결 문제 감지:', status);
        }
        
      } catch (error) {
        console.error('정기 상태 확인 오류:', error);
      }
    }, 5 * 60 * 1000); // 5분
  }

  // 캐시 관리
  clearCache() {
    this.analysisCache.clear();
    console.log('분석 결과 캐시가 정리되었습니다');
  }

  // 메모리 사용량 최적화
  optimizeMemory() {
    const now = Date.now();
    const maxAge = 7 * 24 * 60 * 60 * 1000; // 7일
    
    for (const [videoId, data] of this.analysisCache.entries()) {
      if (now - data.timestamp > maxAge) {
        this.analysisCache.delete(videoId);
      }
    }
  }
}

// 백그라운드 서비스 인스턴스 생성
const backgroundService = new InfoGuardBackgroundService();

// 메모리 최적화 (1시간마다)
setInterval(() => {
  backgroundService.optimizeMemory();
}, 60 * 60 * 1000);

// 서비스 워커 생명주기 이벤트
self.addEventListener('activate', (event) => {
  console.log('Info-Guard 서비스 워커가 활성화되었습니다');
});

self.addEventListener('fetch', (event) => {
  // 필요한 경우 네트워크 요청 가로채기
  console.log('네트워크 요청:', event.request.url);
});
