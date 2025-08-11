/**
 * Info-Guard Chrome Extension Options JavaScript
 * 설정 페이지의 모든 기능을 관리하는 스크립트
 */

class InfoGuardOptions {
    constructor() {
        this.defaultSettings = {
            apiBaseUrl: 'http://localhost:8000',
            nodeApiUrl: 'http://localhost:3000',
            analysisTypes: {
                sentiment: true,
                bias: true,
                credibility: true,
                content: true
            },
            includeComments: true,
            includeSubtitles: true,
            autoAnalysis: false,
            showNotifications: true,
            theme: 'auto',
            language: 'ko',
            credibilityDisplay: 'badge',
            dataRetention: 30,
            debugMode: false,
            connectionTimeout: 30
        };
        
        this.init();
    }

    async init() {
        try {
            // 이벤트 리스너 등록
            this.setupEventListeners();
            
            // 저장된 설정 로드
            await this.loadSettings();
            
            // 연결 상태 확인
            await this.checkConnectionStatus();
            
            // 테마 적용
            this.applyTheme();
            
            console.log('Info-Guard 설정 페이지가 초기화되었습니다.');
        } catch (error) {
            console.error('설정 페이지 초기화 실패:', error);
            this.showMessage('설정 페이지 초기화에 실패했습니다.', 'error');
        }
    }

    setupEventListeners() {
        // 설정 저장
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // 기본값으로 복원
        document.getElementById('resetSettings').addEventListener('click', () => {
            this.resetSettings();
        });

        // 설정 내보내기
        document.getElementById('exportSettings').addEventListener('click', () => {
            this.exportSettings();
        });

        // 설정 가져오기
        document.getElementById('importSettings').addEventListener('click', () => {
            this.importSettings();
        });

        // 데이터 삭제
        document.getElementById('clearHistory').addEventListener('click', () => {
            this.clearHistory();
        });

        document.getElementById('clearCache').addEventListener('click', () => {
            this.clearCache();
        });

        // 테마 변경
        document.getElementById('theme').addEventListener('change', (e) => {
            this.applyTheme(e.target.value);
        });

        // 파일 가져오기
        document.getElementById('importFile').addEventListener('change', (e) => {
            this.handleFileImport(e.target.files[0]);
        });
    }

    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get('settings');
            const settings = result.settings || this.defaultSettings;
            
            // 폼에 설정 값 설정
            this.populateForm(settings);
            
        } catch (error) {
            console.error('설정 로드 실패:', error);
            this.showMessage('설정을 로드할 수 없습니다.', 'error');
        }
    }

    populateForm(settings) {
        // API 설정
        document.getElementById('apiBaseUrl').value = settings.apiBaseUrl || this.defaultSettings.apiBaseUrl;
        document.getElementById('nodeApiUrl').value = settings.nodeApiUrl || this.defaultSettings.nodeApiUrl;
        
        // 분석 설정
        document.getElementById('sentimentAnalysis').checked = settings.analysisTypes?.sentiment ?? true;
        document.getElementById('biasDetection').checked = settings.analysisTypes?.bias ?? true;
        document.getElementById('credibilityAnalysis').checked = settings.analysisTypes?.credibility ?? true;
        document.getElementById('contentClassification').checked = settings.analysisTypes?.content ?? true;
        
        document.getElementById('includeComments').checked = settings.includeComments ?? true;
        document.getElementById('includeSubtitles').checked = settings.includeSubtitles ?? true;
        document.getElementById('autoAnalysis').checked = settings.autoAnalysis ?? false;
        document.getElementById('showNotifications').checked = settings.showNotifications ?? true;
        
        // UI 설정
        document.getElementById('theme').value = settings.theme || 'auto';
        document.getElementById('language').value = settings.language || 'ko';
        document.getElementById('credibilityDisplay').value = settings.credibilityDisplay || 'badge';
        
        // 데이터 관리
        document.getElementById('dataRetention').value = settings.dataRetention || 30;
        
        // 고급 설정
        document.getElementById('debugMode').checked = settings.debugMode ?? false;
        document.getElementById('connectionTimeout').value = settings.connectionTimeout || 30;
    }

    async saveSettings() {
        try {
            const settings = this.collectFormData();
            
            // Chrome 스토리지에 저장
            await chrome.storage.sync.set({ settings });
            
            // 백그라운드 스크립트에 설정 업데이트 알림
            await chrome.runtime.sendMessage({
                type: 'UPDATE_USER_SETTINGS',
                settings: settings
            });
            
            this.showMessage('설정이 성공적으로 저장되었습니다.', 'success');
            
            // 연결 상태 재확인
            await this.checkConnectionStatus();
            
        } catch (error) {
            console.error('설정 저장 실패:', error);
            this.showMessage('설정 저장에 실패했습니다.', 'error');
        }
    }

    collectFormData() {
        return {
            apiBaseUrl: document.getElementById('apiBaseUrl').value,
            nodeApiUrl: document.getElementById('nodeApiUrl').value,
            analysisTypes: {
                sentiment: document.getElementById('sentimentAnalysis').checked,
                bias: document.getElementById('biasDetection').checked,
                credibility: document.getElementById('credibilityAnalysis').checked,
                content: document.getElementById('contentClassification').checked
            },
            includeComments: document.getElementById('includeComments').checked,
            includeSubtitles: document.getElementById('includeSubtitles').checked,
            autoAnalysis: document.getElementById('autoAnalysis').checked,
            showNotifications: document.getElementById('showNotifications').checked,
            theme: document.getElementById('theme').value,
            language: document.getElementById('language').value,
            credibilityDisplay: document.getElementById('credibilityDisplay').value,
            dataRetention: parseInt(document.getElementById('dataRetention').value),
            debugMode: document.getElementById('debugMode').checked,
            connectionTimeout: parseInt(document.getElementById('connectionTimeout').value)
        };
    }

    async resetSettings() {
        try {
            if (confirm('모든 설정을 기본값으로 복원하시겠습니까?')) {
                // 기본 설정으로 폼 초기화
                this.populateForm(this.defaultSettings);
                
                // Chrome 스토리지에서 설정 제거
                await chrome.storage.sync.remove('settings');
                
                this.showMessage('설정이 기본값으로 복원되었습니다.', 'success');
            }
        } catch (error) {
            console.error('설정 복원 실패:', error);
            this.showMessage('설정 복원에 실패했습니다.', 'error');
        }
    }

    async exportSettings() {
        try {
            const settings = this.collectFormData();
            const dataStr = JSON.stringify(settings, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'info-guard-settings.json';
            link.click();
            
            URL.revokeObjectURL(url);
            
            this.showMessage('설정이 성공적으로 내보내졌습니다.', 'success');
        } catch (error) {
            console.error('설정 내보내기 실패:', error);
            this.showMessage('설정 내보내기에 실패했습니다.', 'error');
        }
    }

    importSettings() {
        document.getElementById('importFile').click();
    }

    async handleFileImport(file) {
        try {
            if (!file) return;
            
            const text = await file.text();
            const settings = JSON.parse(text);
            
            // 설정 유효성 검사
            if (this.validateSettings(settings)) {
                this.populateForm(settings);
                this.showMessage('설정이 성공적으로 가져와졌습니다.', 'success');
            } else {
                this.showMessage('잘못된 설정 파일입니다.', 'error');
            }
        } catch (error) {
            console.error('설정 가져오기 실패:', error);
            this.showMessage('설정 가져오기에 실패했습니다.', 'error');
        }
    }

    validateSettings(settings) {
        // 기본적인 설정 구조 검사
        return settings && 
               typeof settings === 'object' &&
               typeof settings.apiBaseUrl === 'string' &&
               typeof settings.analysisTypes === 'object';
    }

    async clearHistory() {
        try {
            if (confirm('모든 분석 기록을 삭제하시겠습니까?')) {
                await chrome.storage.local.remove(['analysisHistory', 'videoHistory']);
                this.showMessage('분석 기록이 삭제되었습니다.', 'success');
            }
        } catch (error) {
            console.error('기록 삭제 실패:', error);
            this.showMessage('기록 삭제에 실패했습니다.', 'error');
        }
    }

    async clearCache() {
        try {
            if (confirm('모든 캐시를 삭제하시겠습니까?')) {
                await chrome.storage.local.remove(['analysisCache', 'modelCache']);
                this.showMessage('캐시가 삭제되었습니다.', 'success');
            }
        } catch (error) {
            console.error('캐시 삭제 실패:', error);
            this.showMessage('캐시 삭제에 실패했습니다.', 'error');
        }
    }

    async checkConnectionStatus() {
        try {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            // 백그라운드 스크립트에 연결 상태 확인 요청
            const response = await chrome.runtime.sendMessage({
                type: 'CHECK_CONNECTION'
            });
            
            if (response && response.success && response.connected) {
                statusDot.style.backgroundColor = '#059669'; // 성공 (초록)
                statusText.textContent = '연결됨';
                statusText.style.color = '#059669';
            } else {
                statusDot.style.backgroundColor = '#dc2626'; // 실패 (빨강)
                statusText.textContent = '연결 안됨';
                statusText.style.color = '#dc2626';
            }
        } catch (error) {
            console.error('연결 상태 확인 실패:', error);
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            statusDot.style.backgroundColor = '#dc2626';
            statusText.textContent = '연결 확인 실패';
            statusText.style.color = '#dc2626';
        }
    }

    applyTheme(theme = null) {
        const currentTheme = theme || document.getElementById('theme').value;
        
        if (currentTheme === 'auto') {
            // 시스템 테마 감지
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
            document.documentElement.setAttribute('data-theme', currentTheme);
        }
    }

    showMessage(message, type = 'info') {
        // 기존 메시지 제거
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // 새 메시지 생성
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        // 메인 콘텐츠 상단에 추가
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(messageElement, mainContent.firstChild);
        
        // 5초 후 자동 제거
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 5000);
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new InfoGuardOptions();
});

// 시스템 테마 변경 감지
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const themeSelect = document.getElementById('theme');
    if (themeSelect.value === 'auto') {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
});
