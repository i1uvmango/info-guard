/**
 * Info-Guard Chrome Extension Content Script
 * YouTube 페이지에 신뢰도 분석 UI를 주입하는 스크립트
 */

class InfoGuardContent {
    constructor() {
        this.videoId = null;
        this.analysisResult = null;
        this.isAnalyzing = false;
        this.analysisButton = null;
        this.credibilityBadge = null;
        
        this.init();
    }

    init() {
        // 페이지 로드 완료 후 초기화
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this.setup.bind(this));
        } else {
            this.setup();
        }
        
        // 메시지 리스너 등록
        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        
        // YouTube 페이지 변경 감지 (SPA)
        this.observePageChanges();
        
        console.log('Info-Guard 콘텐츠 스크립트가 로드되었습니다.');
    }

    setup() {
        try {
            // 현재 페이지가 YouTube 영상 페이지인지 확인
            if (this.isVideoPage()) {
                this.videoId = this.extractVideoId();
                if (this.videoId) {
                    this.injectAnalysisUI();
                    this.loadExistingAnalysis();
                }
            }
        } catch (error) {
            console.error('콘텐츠 스크립트 설정 실패:', error);
        }
    }

    isVideoPage() {
        return window.location.pathname === '/watch' && 
               window.location.search.includes('v=');
    }

    extractVideoId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('v');
    }

    injectAnalysisUI() {
        try {
            // 분석 버튼 주입
            this.injectAnalysisButton();
            
            // 신뢰도 배지 주입
            this.injectCredibilityBadge();
            
            // 분석 결과 패널 주입
            this.injectAnalysisPanel();
            
        } catch (error) {
            console.error('UI 주입 실패:', error);
        }
    }

    injectAnalysisButton() {
        try {
            // YouTube의 액션 버튼 영역 찾기
            const actionBar = this.findActionBar();
            if (!actionBar) return;

            // 기존 버튼이 있다면 제거
            if (this.analysisButton) {
                this.analysisButton.remove();
            }

            // 분석 버튼 생성
            this.analysisButton = this.createAnalysisButton();
            
            // 액션 바에 삽입
            actionBar.appendChild(this.analysisButton);
            
        } catch (error) {
            console.error('분석 버튼 주입 실패:', error);
        }
    }

    findActionBar() {
        // 여러 가능한 위치에서 액션 바 찾기
        const selectors = [
            '#actions-inner',
            '#actions',
            '.ytd-video-primary-info-renderer #actions',
            '.ytd-video-primary-info-renderer #actions-inner',
            '#top-level-buttons-computed',
            '#top-level-buttons'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) return element;
        }
        
        return null;
    }

    createAnalysisButton() {
        const button = document.createElement('button');
        button.className = 'info-guard-analysis-btn';
        button.innerHTML = `
            <div class="btn-content">
                <svg class="btn-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <span class="btn-text">신뢰도 분석</span>
            </div>
        `;
        
        // 클릭 이벤트 등록
        button.addEventListener('click', this.handleAnalysisClick.bind(this));
        
        return button;
    }

    injectCredibilityBadge() {
        try {
            // 영상 제목 영역 찾기
            const titleElement = this.findVideoTitle();
            if (!titleElement) return;

            // 기존 배지가 있다면 제거
            if (this.credibilityBadge) {
                this.credibilityBadge.remove();
            }

            // 신뢰도 배지 생성
            this.credibilityBadge = this.createCredibilityBadge();
            
            // 제목 아래에 삽입
            titleElement.parentNode.insertBefore(this.credibilityBadge, titleElement.nextSibling);
            
        } catch (error) {
            console.error('신뢰도 배지 주입 실패:', error);
        }
    }

    findVideoTitle() {
        const selectors = [
            'h1.ytd-video-primary-info-renderer',
            '#video-title',
            '.ytd-video-primary-info-renderer h1',
            'h1.title'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) return element;
        }
        
        return null;
    }

    createCredibilityBadge() {
        const badge = document.createElement('div');
        badge.className = 'info-guard-credibility-badge';
        badge.innerHTML = `
            <div class="badge-content">
                <span class="badge-icon">🛡️</span>
                <span class="badge-text">신뢰도 분석 중...</span>
                <span class="badge-score" id="credibilityScore">--</span>
            </div>
        `;
        
        return badge;
    }

    injectAnalysisPanel() {
        try {
            // 사이드바 영역 찾기
            const sidebar = this.findSidebar();
            if (!sidebar) return;

            // 기존 패널이 있다면 제거
            const existingPanel = document.querySelector('.info-guard-analysis-panel');
            if (existingPanel) {
                existingPanel.remove();
            }

            // 분석 패널 생성
            const analysisPanel = this.createAnalysisPanel();
            
            // 사이드바 상단에 삽입
            sidebar.insertBefore(analysisPanel, sidebar.firstChild);
            
        } catch (error) {
            console.error('분석 패널 주입 실패:', error);
        }
    }

    findSidebar() {
        const selectors = [
            '#secondary',
            '#secondary-inner',
            '.ytd-watch-flexy #secondary',
            '#related'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) return element;
        }
        
        return null;
    }

    createAnalysisPanel() {
        const panel = document.createElement('div');
        panel.className = 'info-guard-analysis-panel';
        panel.innerHTML = `
            <div class="panel-header">
                <h3 class="panel-title">🔍 Info-Guard 분석 결과</h3>
                <button class="panel-close-btn" id="closePanel">×</button>
            </div>
            <div class="panel-content">
                <div class="loading-message" id="loadingMessage">
                    <div class="spinner"></div>
                    <p>영상을 분석하고 있습니다...</p>
                </div>
                <div class="analysis-results" id="analysisResults" style="display: none;">
                    <!-- 분석 결과가 여기에 표시됩니다 -->
                </div>
            </div>
        `;
        
        // 닫기 버튼 이벤트
        const closeBtn = panel.querySelector('#closePanel');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                panel.style.display = 'none';
            });
        }
        
        return panel;
    }

    async handleAnalysisClick() {
        if (this.isAnalyzing) {
            this.showMessage('이미 분석 중입니다. 잠시 기다려주세요.');
            return;
        }

        try {
            this.isAnalyzing = true;
            this.updateAnalysisButton(true);
            
            // 백그라운드에 분석 요청
            const response = await chrome.runtime.sendMessage({
                type: 'ANALYZE_VIDEO',
                videoUrl: `https://www.youtube.com/watch?v=${this.videoId}`
            });

            if (response.success) {
                this.analysisResult = response.data;
                this.monitorAnalysisProgress(response.data.analysis_id);
            } else {
                throw new Error(response.error || '분석 요청 실패');
            }
            
        } catch (error) {
            console.error('분석 요청 실패:', error);
            this.showMessage('분석 요청에 실패했습니다. 다시 시도해주세요.');
            this.updateAnalysisButton(false);
            this.isAnalyzing = false;
        }
    }

    async monitorAnalysisProgress(analysisId) {
        try {
            let attempts = 0;
            const maxAttempts = 60; // 최대 5분 대기
            
            const checkProgress = async () => {
                attempts++;
                
                const response = await chrome.runtime.sendMessage({
                    type: 'GET_ANALYSIS_STATUS',
                    analysisId: analysisId
                });
                
                if (response.success) {
                    const status = response.data;
                    
                    if (status.status === 'completed') {
                        // 분석 완료
                        await this.loadAnalysisResult(analysisId);
                        return;
                    } else if (status.status === 'failed') {
                        throw new Error('분석이 실패했습니다.');
                    } else if (attempts >= maxAttempts) {
                        throw new Error('분석 시간이 초과되었습니다.');
                    }
                    
                    // 진행률 업데이트
                    this.updateProgress(status.progress || 0);
                    
                    // 5초 후 다시 확인
                    setTimeout(checkProgress, 5000);
                } else {
                    throw new Error('분석 상태 확인 실패');
                }
            };
            
            checkProgress();
            
        } catch (error) {
            console.error('분석 진행상황 모니터링 실패:', error);
            this.showMessage('분석 진행상황을 확인할 수 없습니다.');
            this.updateAnalysisButton(false);
            this.isAnalyzing = false;
        }
    }

    async loadAnalysisResult(analysisId) {
        try {
            const response = await chrome.runtime.sendMessage({
                type: 'GET_ANALYSIS_RESULT',
                analysisId: analysisId
            });

            if (response.success) {
                this.displayAnalysisResult(response.data);
            } else {
                throw new Error('분석 결과를 가져올 수 없습니다.');
            }
            
        } catch (error) {
            console.error('분석 결과 로드 실패:', error);
            this.showMessage('분석 결과를 가져올 수 없습니다.');
        } finally {
            this.updateAnalysisButton(false);
            this.isAnalyzing = false;
        }
    }

    displayAnalysisResult(result) {
        try {
            // 신뢰도 배지 업데이트
            this.updateCredibilityBadge(result);
            
            // 분석 패널에 결과 표시
            this.updateAnalysisPanel(result);
            
            // 분석 결과 저장
            this.analysisResult = result;
            
        } catch (error) {
            console.error('결과 표시 실패:', error);
        }
    }

    updateCredibilityBadge(result) {
        if (!this.credibilityBadge) return;
        
        const scoreElement = this.credibilityBadge.querySelector('#credibilityScore');
        const textElement = this.credibilityBadge.querySelector('.badge-text');
        
        if (scoreElement && textElement) {
            const score = Math.round(result.overall_credibility_score * 100);
            scoreElement.textContent = `${score}%`;
            
            // 점수에 따른 색상 및 텍스트 설정
            if (score >= 80) {
                this.credibilityBadge.className = 'info-guard-credibility-badge high';
                textElement.textContent = '매우 신뢰할 수 있음';
            } else if (score >= 60) {
                this.credibilityBadge.className = 'info-guard-credibility-badge medium';
                textElement.textContent = '신뢰할 수 있음';
            } else if (score >= 40) {
                this.credibilityBadge.className = 'info-guard-credibility-badge low';
                textElement.textContent = '보통';
            } else {
                this.credibilityBadge.className = 'info-guard-credibility-badge very-low';
                textElement.textContent = '신뢰하기 어려움';
            }
        }
    }

    updateAnalysisPanel(result) {
        const resultsContainer = document.querySelector('#analysisResults');
        const loadingMessage = document.querySelector('#loadingMessage');
        
        if (!resultsContainer || !loadingMessage) return;
        
        // 로딩 메시지 숨기기
        loadingMessage.style.display = 'none';
        
        // 결과 표시
        resultsContainer.innerHTML = this.createResultsHTML(result);
        resultsContainer.style.display = 'block';
    }

    createResultsHTML(result) {
        return `
            <div class="result-summary">
                <div class="overall-score">
                    <span class="score-label">전체 신뢰도</span>
                    <span class="score-value">${Math.round(result.overall_credibility_score * 100)}%</span>
                </div>
            </div>
            
            <div class="result-details">
                <div class="detail-item">
                    <span class="detail-label">편향성</span>
                    <div class="detail-bar">
                        <div class="detail-fill" style="width: ${Math.round((1 - result.results.bias?.total_bias_score || 0) * 100)}%"></div>
                    </div>
                    <span class="detail-value">${Math.round((1 - (result.results.bias?.total_bias_score || 0)) * 100)}%</span>
                </div>
                
                <div class="detail-item">
                    <span class="detail-label">사실 확인</span>
                    <div class="detail-bar">
                        <div class="detail-fill" style="width: ${Math.round((result.results.credibility?.credibility_score || 0) * 100)}%"></div>
                    </div>
                    <span class="detail-value">${Math.round((result.results.credibility?.credibility_score || 0) * 100)}%</span>
                </div>
                
                <div class="detail-item">
                    <span class="detail-label">감정 분석</span>
                    <div class="detail-bar">
                        <div class="detail-fill" style="width: ${Math.round((result.results.sentiment?.neutral_score || 0) / 10)}%"></div>
                    </div>
                    <span class="detail-value">${result.results.sentiment?.label || 'N/A'}</span>
                </div>
            </div>
            
            <div class="result-explanation">
                <p>${this.generateExplanation(result)}</p>
            </div>
        `;
    }

    generateExplanation(result) {
        let explanation = '이 영상은 ';
        
        if (result.results.credibility?.label === 'highly_reliable') {
            explanation += '높은 신뢰도를 보입니다. ';
        } else if (result.results.credibility?.label === 'reliable') {
            explanation += '적당한 신뢰도를 보입니다. ';
        } else {
            explanation += '낮은 신뢰도를 보입니다. ';
        }
        
        if (result.results.bias?.total_bias_score < 0.3) {
            explanation += '편향성이 낮아 객관적입니다. ';
        } else {
            explanation += '편향성이 있을 수 있으니 주의가 필요합니다. ';
        }
        
        return explanation;
    }

    updateAnalysisButton(analyzing) {
        if (!this.analysisButton) return;
        
        if (analyzing) {
            this.analysisButton.disabled = true;
            this.analysisButton.querySelector('.btn-text').textContent = '분석 중...';
            this.analysisButton.classList.add('analyzing');
        } else {
            this.analysisButton.disabled = false;
            this.analysisButton.querySelector('.btn-text').textContent = '신뢰도 분석';
            this.analysisButton.classList.remove('analyzing');
        }
    }

    updateProgress(progress) {
        // 진행률 표시 (선택사항)
        console.log(`분석 진행률: ${progress}%`);
    }

    async loadExistingAnalysis() {
        try {
            // 로컬 스토리지에서 기존 분석 결과 확인
            const result = await chrome.storage.local.get(`analysis_${this.videoId}`);
            if (result[`analysis_${this.videoId}`]) {
                this.analysisResult = result[`analysis_${this.videoId}`];
                this.displayAnalysisResult(this.analysisResult);
            }
        } catch (error) {
            console.error('기존 분석 결과 로드 실패:', error);
        }
    }

    handleMessage(request, sender, sendResponse) {
        try {
            switch (request.type) {
                case 'INJECT_ANALYSIS_BUTTON':
                    this.injectAnalysisUI();
                    break;
                    
                default:
                    // 알 수 없는 메시지 타입
                    break;
            }
        } catch (error) {
            console.error('메시지 처리 실패:', error);
        }
    }

    observePageChanges() {
        // YouTube SPA 페이지 변경 감지
        let currentUrl = window.location.href;
        
        const observer = new MutationObserver(() => {
            if (window.location.href !== currentUrl) {
                currentUrl = window.location.href;
                
                // URL 변경 시 UI 재설정
                setTimeout(() => {
                    this.setup();
                }, 1000);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    showMessage(message) {
        // 간단한 메시지 표시
        const messageDiv = document.createElement('div');
        messageDiv.className = 'info-guard-message';
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 10000;
            font-size: 14px;
        `;
        
        document.body.appendChild(messageDiv);
        
        // 3초 후 자동 제거
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }
}

// 콘텐츠 스크립트 시작
const contentScript = new InfoGuardContent();
