/**
 * Info-Guard Chrome Extension Popup JavaScript
 * YouTube 영상 신뢰도 분석을 위한 팝업 로직
 */

class InfoGuardPopup {
    constructor() {
        this.currentVideoId = null;
        this.analysisResult = null;
        this.apiBaseUrl = 'http://localhost:8000';
        
        this.init();
    }

    async init() {
        try {
            // 현재 YouTube 페이지에서 영상 정보 가져오기
            await this.getCurrentVideoInfo();
            
            // 이벤트 리스너 등록
            this.setupEventListeners();
            
            // 상태 표시 업데이트
            this.updateConnectionStatus();
            
        } catch (error) {
            console.error('팝업 초기화 실패:', error);
            this.showError('팝업 초기화에 실패했습니다.');
        }
    }

    async getCurrentVideoInfo() {
        try {
            // 현재 활성 탭에서 YouTube 영상 정보 가져오기
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab.url && tab.url.includes('youtube.com/watch')) {
                const videoId = this.extractVideoId(tab.url);
                if (videoId) {
                    this.currentVideoId = videoId;
                    await this.analyzeVideo(videoId);
                } else {
                    this.showError('YouTube 영상을 찾을 수 없습니다.');
                }
            } else {
                this.showMessage('YouTube 영상 페이지에서만 사용할 수 있습니다.');
            }
        } catch (error) {
            console.error('영상 정보 가져오기 실패:', error);
            this.showError('영상 정보를 가져올 수 없습니다.');
        }
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    async analyzeVideo(videoId) {
        try {
            this.showLoading(true);
            
            // 분석 요청
            const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: `https://www.youtube.com/watch?v=${videoId}`,
                    analysis_types: ['sentiment', 'bias', 'credibility', 'content'],
                    include_comments: true,
                    include_subtitles: true
                })
            });

            if (!response.ok) {
                throw new Error(`분석 요청 실패: ${response.status}`);
            }

            const result = await response.json();
            this.analysisResult = result;
            
            // 분석 상태 모니터링 시작
            this.monitorAnalysisProgress(result.analysis_id);
            
        } catch (error) {
            console.error('영상 분석 실패:', error);
            this.showError('영상 분석에 실패했습니다.');
            this.showLoading(false);
        }
    }

    async monitorAnalysisProgress(analysisId) {
        try {
            let attempts = 0;
            const maxAttempts = 60; // 최대 5분 대기
            
            const checkProgress = async () => {
                attempts++;
                
                const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/status/${analysisId}`);
                if (!response.ok) {
                    throw new Error('분석 상태 확인 실패');
                }
                
                const status = await response.json();
                
                if (status.status === 'completed') {
                    // 분석 완료 - 결과 가져오기
                    await this.getAnalysisResult(analysisId);
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
            };
            
            checkProgress();
            
        } catch (error) {
            console.error('분석 진행상황 모니터링 실패:', error);
            this.showError('분석 진행상황을 확인할 수 없습니다.');
            this.showLoading(false);
        }
    }

    async getAnalysisResult(analysisId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/v1/analysis/result/${analysisId}`);
            if (!response.ok) {
                throw new Error('분석 결과 가져오기 실패');
            }
            
            const result = await response.json();
            this.displayAnalysisResult(result);
            
        } catch (error) {
            console.error('분석 결과 가져오기 실패:', error);
            this.showError('분석 결과를 가져올 수 없습니다.');
        } finally {
            this.showLoading(false);
        }
    }

    displayAnalysisResult(result) {
        try {
            // 영상 정보 표시
            this.showVideoDetails(result);
            
            // 분석 결과 표시
            this.showAnalysisResults(result);
            
            // 설명 표시
            this.showExplanation(result);
            
            // 피드백 섹션 표시
            this.showFeedbackSection();
            
        } catch (error) {
            console.error('결과 표시 실패:', error);
            this.showError('결과를 표시할 수 없습니다.');
        }
    }

    showVideoDetails(result) {
        const videoDetails = document.getElementById('videoDetails');
        const videoTitle = document.getElementById('videoTitle');
        const credibilityScore = document.getElementById('credibilityScore');
        const credibilityGrade = document.getElementById('credibilityGrade');
        
        if (videoDetails && videoTitle && credibilityScore && credibilityGrade) {
            videoTitle.textContent = result.video_title;
            credibilityScore.textContent = `${Math.round(result.overall_credibility_score * 100)}%`;
            credibilityGrade.textContent = this.getCredibilityGrade(result.overall_credibility_score);
            
            videoDetails.style.display = 'block';
        }
    }

    showAnalysisResults(result) {
        const analysisResults = document.getElementById('analysisResults');
        if (!analysisResults) return;
        
        // 편향성 점수
        this.updateScore('bias', result.results.bias?.total_bias_score || 0);
        
        // 신뢰도 점수
        this.updateScore('fact', result.results.credibility?.credibility_score || 0);
        
        // 출처 정보 점수
        this.updateScore('source', result.results.credibility?.factors?.channel_credibility || 0);
        
        // 감정 분석 점수
        const sentimentScore = result.results.sentiment?.neutral_score || 0;
        this.updateScore('sentiment', sentimentScore / 1000); // 0-1 범위로 정규화
        
        analysisResults.style.display = 'block';
    }

    updateScore(type, score) {
        const progressElement = document.getElementById(`${type}Progress`);
        const scoreElement = document.getElementById(`${type}Score`);
        
        if (progressElement && scoreElement) {
            const percentage = Math.round(score * 100);
            progressElement.style.width = `${percentage}%`;
            scoreElement.textContent = `${percentage}%`;
            
            // 색상 설정
            if (percentage >= 70) {
                progressElement.style.backgroundColor = '#4CAF50'; // 녹색
            } else if (percentage >= 40) {
                progressElement.style.backgroundColor = '#FF9800'; // 주황색
            } else {
                progressElement.style.backgroundColor = '#F44336'; // 빨간색
            }
        }
    }

    getCredibilityGrade(score) {
        if (score >= 0.8) return '매우 신뢰할 수 있음';
        if (score >= 0.6) return '신뢰할 수 있음';
        if (score >= 0.4) return '보통';
        if (score >= 0.2) return '신뢰하기 어려움';
        return '매우 신뢰하기 어려움';
    }

    showExplanation(result) {
        const explanation = document.getElementById('explanation');
        const explanationText = document.getElementById('explanationText');
        
        if (explanation && explanationText) {
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
            
            explanationText.textContent = explanation;
            explanation.style.display = 'block';
        }
    }

    showFeedbackSection() {
        const feedbackSection = document.getElementById('feedbackSection');
        if (feedbackSection) {
            feedbackSection.style.display = 'block';
        }
    }

    showLoading(show) {
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = show ? 'block' : 'none';
        }
    }

    showError(message) {
        // 에러 메시지 표시
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = 'color: red; padding: 10px; text-align: center;';
        
        const container = document.querySelector('.container');
        if (container) {
            container.appendChild(errorDiv);
        }
    }

    showMessage(message) {
        // 일반 메시지 표시
        const messageDiv = document.createElement('div');
        messageDiv.className = 'info-message';
        messageDiv.textContent = message;
        messageDiv.style.cssText = 'color: blue; padding: 10px; text-align: center;';
        
        const container = document.querySelector('.container');
        if (container) {
            container.appendChild(messageDiv);
        }
    }

    updateProgress(progress) {
        // 진행률 표시 (선택사항)
        console.log(`분석 진행률: ${progress}%`);
    }

    updateConnectionStatus() {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        
        if (statusDot && statusText) {
            // API 연결 상태 확인
            fetch(`${this.apiBaseUrl}/health/status`)
                .then(response => {
                    if (response.ok) {
                        statusDot.style.backgroundColor = '#4CAF50';
                        statusText.textContent = '연결됨';
                    } else {
                        throw new Error('API 응답 오류');
                    }
                })
                .catch(error => {
                    console.error('API 연결 상태 확인 실패:', error);
                    statusDot.style.backgroundColor = '#F44336';
                    statusText.textContent = '연결 안됨';
                });
        }
    }

    setupEventListeners() {
        // 설정 버튼
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                chrome.runtime.openOptionsPage();
            });
        }

        // 피드백 버튼들
        const positiveFeedback = document.getElementById('positiveFeedback');
        const negativeFeedback = document.getElementById('negativeFeedback');
        
        if (positiveFeedback) {
            positiveFeedback.addEventListener('click', () => this.submitFeedback('positive'));
        }
        
        if (negativeFeedback) {
            negativeFeedback.addEventListener('click', () => this.submitFeedback('negative'));
        }
    }

    async submitFeedback(type) {
        try {
            const feedbackData = {
                analysis_id: this.analysisResult?.analysis_id,
                video_id: this.currentVideoId,
                feedback_type: type,
                timestamp: new Date().toISOString()
            };
            
            // 피드백 전송 (백엔드 API가 구현되면 활성화)
            console.log('피드백 전송:', feedbackData);
            
            // 사용자에게 피드백 감사 메시지 표시
            this.showMessage('피드백을 보내주셔서 감사합니다!');
            
        } catch (error) {
            console.error('피드백 전송 실패:', error);
            this.showError('피드백 전송에 실패했습니다.');
        }
    }
}

// 팝업 초기화
document.addEventListener('DOMContentLoaded', () => {
    new InfoGuardPopup();
});
