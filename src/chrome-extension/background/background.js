/**
 * Info-Guard Chrome Extension Background Script
 * 백그라운드 서비스 워커로 API 통신 및 상태 관리
 */

class InfoGuardBackground {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.isAuthenticated = false;
        this.userToken = null;
        this.currentTab = null;
        
        this.init();
    }

    init() {
        // 설치 시 초기화
        chrome.runtime.onInstalled.addListener(this.handleInstalled.bind(this));
        
        // 메시지 리스너 등록
        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        
        // 탭 변경 감지
        chrome.tabs.onUpdated.addListener(this.handleTabUpdated.bind(this));
        
        // 확장 프로그램 아이콘 클릭 이벤트
        chrome.action.onClicked.addListener(this.handleActionClicked.bind(this));
        
        // 스토리지에서 사용자 설정 로드
        this.loadUserSettings();
        
        console.log('Info-Guard 백그라운드 서비스가 시작되었습니다.');
    }

    async handleInstalled(details) {
        if (details.reason === 'install') {
            // 새로 설치된 경우
            console.log('Info-Guard가 새로 설치되었습니다.');
            
            // 기본 설정 저장
            await this.saveDefaultSettings();
            
            // 환영 페이지 열기
            chrome.tabs.create({
                url: chrome.runtime.getURL('options/options.html')
            });
            
        } else if (details.reason === 'update') {
            // 업데이트된 경우
            console.log('Info-Guard가 업데이트되었습니다.');
            
            // 새 기능 안내 알림
            this.showUpdateNotification();
        }
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.type) {
                case 'ANALYZE_VIDEO':
                    const result = await this.analyzeVideo(request.videoUrl);
                    sendResponse({ success: true, data: result });
                    break;
                    
                case 'GET_ANALYSIS_STATUS':
                    const status = await this.getAnalysisStatus(request.analysisId);
                    sendResponse({ success: true, data: status });
                    break;
                    
                case 'GET_ANALYSIS_RESULT':
                    const analysisResult = await this.getAnalysisResult(request.analysisId);
                    sendResponse({ success: true, data: analysisResult });
                    break;
                    
                case 'SUBMIT_FEEDBACK':
                    await this.submitFeedback(request.feedbackData);
                    sendResponse({ success: true });
                    break;
                    
                case 'CHECK_CONNECTION':
                    const isConnected = await this.checkConnection();
                    sendResponse({ success: true, connected: isConnected });
                    break;
                    
                case 'GET_USER_SETTINGS':
                    const settings = await this.getUserSettings();
                    sendResponse({ success: true, data: settings });
                    break;
                    
                case 'UPDATE_USER_SETTINGS':
                    await this.updateUserSettings(request.settings);
                    sendResponse({ success: true });
                    break;
                    
                default:
                    sendResponse({ success: false, error: '알 수 없는 메시지 타입' });
            }
        } catch (error) {
            console.error('메시지 처리 중 오류:', error);
            sendResponse({ success: false, error: error.message });
        }
        
        return true; // 비동기 응답을 위해 true 반환
    }

    async handleTabUpdated(tabId, changeInfo, tab) {
        if (changeInfo.status === 'complete' && tab.url) {
            // YouTube 페이지인지 확인
            if (tab.url.includes('youtube.com/watch')) {
                this.currentTab = tab;
                
                // 페이지에 분석 버튼 주입
                await this.injectAnalysisButton(tabId);
                
                // 영상 정보 추출 및 저장
                const videoInfo = await this.extractVideoInfo(tab.url);
                if (videoInfo) {
                    await this.saveVideoInfo(videoInfo);
                }
            }
        }
    }

    async handleActionClicked(tab) {
        // 확장 프로그램 아이콘 클릭 시 팝업 열기
        if (tab.url && tab.url.includes('youtube.com/watch')) {
            // 팝업이 이미 열려있는 경우 새로고침
            const popup = await this.getPopup();
            if (popup) {
                chrome.tabs.reload(popup.id);
            }
        } else {
            // YouTube가 아닌 페이지에서는 안내 메시지
            this.showNotification('Info-Guard', 'YouTube 영상 페이지에서만 사용할 수 있습니다.');
        }
    }

    async analyzeVideo(videoUrl) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.userToken && { 'Authorization': `Bearer ${this.userToken}` })
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    analysis_types: ['sentiment', 'bias', 'credibility', 'content'],
                    include_comments: true,
                    include_subtitles: true
                })
            });

            if (!response.ok) {
                throw new Error(`분석 요청 실패: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('영상 분석 실패:', error);
            throw error;
        }
    }

    async getAnalysisStatus(analysisId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/status/${analysisId}`);
            if (!response.ok) {
                throw new Error('분석 상태 확인 실패');
            }
            return await response.json();
        } catch (error) {
            console.error('분석 상태 확인 실패:', error);
            throw error;
        }
    }

    async getAnalysisResult(analysisId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/result/${analysisId}`);
            if (!response.ok) {
                throw new Error('분석 결과 가져오기 실패');
            }
            return await response.json();
        } catch (error) {
            console.error('분석 결과 가져오기 실패:', error);
            throw error;
        }
    }

    async submitFeedback(feedbackData) {
        try {
            // 로컬 스토리지에 피드백 저장 (백엔드 API가 구현되면 전송)
            const feedbacks = await this.getStoredFeedbacks();
            feedbacks.push({
                ...feedbackData,
                id: Date.now().toString(),
                timestamp: new Date().toISOString()
            });
            
            await chrome.storage.local.set({ feedbacks });
            
            // 백엔드로 피드백 전송 (선택사항)
            if (this.apiBaseUrl) {
                try {
                    await fetch(`${this.apiBaseUrl}/api/v1/feedback`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(this.userToken && { 'Authorization': `Bearer ${this.userToken}` })
                        },
                        body: JSON.stringify(feedbackData)
                    });
                } catch (error) {
                    console.warn('백엔드 피드백 전송 실패:', error);
                }
            }
        } catch (error) {
            console.error('피드백 저장 실패:', error);
            throw error;
        }
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health/status`, {
                method: 'GET',
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.error('연결 확인 실패:', error);
            return false;
        }
    }

    async injectAnalysisButton(tabId) {
        try {
            // 콘텐츠 스크립트에 분석 버튼 주입 요청
            await chrome.tabs.sendMessage(tabId, {
                type: 'INJECT_ANALYSIS_BUTTON',
                data: { tabId }
            });
        } catch (error) {
            console.error('분석 버튼 주입 실패:', error);
        }
    }

    async extractVideoInfo(url) {
        try {
            const videoId = this.extractVideoId(url);
            if (!videoId) return null;

            return {
                videoId,
                url,
                timestamp: new Date().toISOString(),
                tabId: this.currentTab?.id
            };
        } catch (error) {
            console.error('영상 정보 추출 실패:', error);
            return null;
        }
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    async saveVideoInfo(videoInfo) {
        try {
            const videoHistory = await this.getVideoHistory();
            videoHistory.unshift(videoInfo);
            
            // 최근 50개만 유지
            if (videoHistory.length > 50) {
                videoHistory.splice(50);
            }
            
            await chrome.storage.local.set({ videoHistory });
        } catch (error) {
            console.error('영상 정보 저장 실패:', error);
        }
    }

    async getVideoHistory() {
        try {
            const result = await chrome.storage.local.get('videoHistory');
            return result.videoHistory || [];
        } catch (error) {
            console.error('영상 히스토리 가져오기 실패:', error);
            return [];
        }
    }

    async getStoredFeedbacks() {
        try {
            const result = await chrome.storage.local.get('feedbacks');
            return result.feedbacks || [];
        } catch (error) {
            console.error('저장된 피드백 가져오기 실패:', error);
            return [];
        }
    }

    async loadUserSettings() {
        try {
            const result = await chrome.storage.sync.get('userSettings');
            if (result.userSettings) {
                this.apiBaseUrl = result.userSettings.apiBaseUrl || this.apiBaseUrl;
                this.userToken = result.userSettings.userToken || null;
            }
        } catch (error) {
            console.error('사용자 설정 로드 실패:', error);
        }
    }

    async getUserSettings() {
        try {
            const result = await chrome.storage.sync.get('userSettings');
            return result.userSettings || {};
        } catch (error) {
            console.error('사용자 설정 가져오기 실패:', error);
            return {};
        }
    }

    async updateUserSettings(settings) {
        try {
            await chrome.storage.sync.set({ userSettings: settings });
            
            // 메모리 업데이트
            this.apiBaseUrl = settings.apiBaseUrl || this.apiBaseUrl;
            this.userToken = settings.userToken || null;
        } catch (error) {
            console.error('사용자 설정 업데이트 실패:', error);
            throw error;
        }
    }

    async saveDefaultSettings() {
        try {
            const defaultSettings = {
                apiBaseUrl: this.apiBaseUrl,
                theme: 'light',
                language: 'ko',
                notifications: true,
                autoAnalysis: false,
                createdAt: new Date().toISOString()
            };
            
            await chrome.storage.sync.set({ userSettings: defaultSettings });
        } catch (error) {
            console.error('기본 설정 저장 실패:', error);
        }
    }

    async getPopup() {
        try {
            const tabs = await chrome.tabs.query({
                url: chrome.runtime.getURL('popup/popup.html')
            });
            return tabs[0] || null;
        } catch (error) {
            console.error('팝업 탭 찾기 실패:', error);
            return null;
        }
    }

    showNotification(title, message) {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: chrome.runtime.getURL('assets/icons/icon48.png'),
            title: title,
            message: message
        });
    }

    showUpdateNotification() {
        this.showNotification(
            'Info-Guard 업데이트',
            '새로운 기능이 추가되었습니다. 설정 페이지를 확인해보세요!'
        );
    }

    // 주기적 연결 상태 확인
    startConnectionMonitor() {
        setInterval(async () => {
            const isConnected = await this.checkConnection();
            if (!isConnected) {
                console.warn('API 서버 연결이 끊어졌습니다.');
                // 연결 상태를 팝업에 알림
                chrome.runtime.sendMessage({
                    type: 'CONNECTION_STATUS_CHANGED',
                    connected: false
                });
            }
        }, 30000); // 30초마다 확인
    }
}

// 백그라운드 서비스 시작
const backgroundService = new InfoGuardBackground();

// 연결 모니터링 시작
backgroundService.startConnectionMonitor();
