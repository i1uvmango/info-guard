# 학습된 모델 통합 가이드

## 개요

Windows 환경에서 학습된 `multitask_credibility_model_optimized.pth` 모델을 Python AI 서비스, Node.js 백엔드, Chrome Extension에 통합하는 작업입니다.

## 현재 상황 분석

### ✅ 보유 자산
- **학습된 모델**: `multitask_credibility_model_optimized.pth` (422MB)
- **모델 구조**: `multitask_credibility_model.py` (10KB, 283줄)
- **데이터 전처리**: `data_preprocessor.py` (12KB, 319줄)
- **AI 서비스**: `main.py` (19KB, 528줄)

### 🔍 구조 분석 필요
- 모델 입력/출력 형식 확인
- 전처리 파이프라인 검증
- API 엔드포인트 호환성 확인
- Chrome Extension 통신 형식 검증

## 통합 계획

### Phase 1: 모델 구조 분석 및 검증

#### 1.1 모델 파일 검증
```python
# 모델 로딩 테스트
import torch
from models.multitask_credibility_model import MultitaskCredibilityModel

# 모델 인스턴스 생성
model = MultitaskCredibilityModel()

# 학습된 가중치 로드
model.load_state_dict(torch.load('multitask_credibility_model_optimized.pth'))

# GPU 사용 가능 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
```

#### 1.2 입력/출력 형식 확인
```python
# 예상 입력 형식
sample_input = {
    "text": "분석할 텍스트",
    "title": "영상 제목",
    "description": "영상 설명",
    "transcript": "자막 텍스트"
}

# 예상 출력 형식
expected_output = {
    "credibility_score": 75.5,
    "bias_score": 0.3,
    "fact_check_score": 0.8,
    "sentiment_score": 0.6,
    "overall_grade": "높음"
}
```

### Phase 2: Python AI 서비스 통합

#### 2.1 모델 로딩 서비스 구현
```python
# services/model_service.py
class TrainedModelService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_model()
    
    def load_model(self):
        """학습된 모델 로드"""
        try:
            self.model = MultitaskCredibilityModel()
            self.model.load_state_dict(
                torch.load('multitask_credibility_model_optimized.pth', 
                          map_location=self.device)
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("학습된 모델 로드 완료")
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise
```

#### 2.2 전처리 파이프라인 통합
```python
# services/preprocessing_service.py
class PreprocessingService:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
    
    def preprocess_video_data(self, video_data):
        """영상 데이터 전처리"""
        return {
            "text": self._combine_text(video_data),
            "title": video_data.get("title", ""),
            "description": video_data.get("description", ""),
            "transcript": video_data.get("transcript", "")
        }
    
    def _combine_text(self, video_data):
        """텍스트 결합"""
        texts = [
            video_data.get("title", ""),
            video_data.get("description", ""),
            video_data.get("transcript", "")
        ]
        return " ".join([t for t in texts if t])
```

#### 2.3 분석 서비스 업데이트
```python
# services/analysis_service.py
class TrainedAnalysisService:
    def __init__(self):
        self.model_service = TrainedModelService()
        self.preprocessing_service = PreprocessingService()
    
    def analyze_video(self, video_data):
        """영상 신뢰도 분석"""
        try:
            # 전처리
            processed_data = self.preprocessing_service.preprocess_video_data(video_data)
            
            # 모델 예측
            with torch.no_grad():
                predictions = self.model_service.model(processed_data)
            
            # 결과 후처리
            result = self._postprocess_predictions(predictions)
            
            return {
                "success": True,
                "data": result,
                "model_version": "trained_v1.0",
                "processing_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"success": False, "error": str(e)}
```

### Phase 3: Node.js 백엔드 통합

#### 3.1 API 엔드포인트 업데이트
```javascript
// routes/analysis.js
router.post('/analyze-video', auth.optionalAuth, async (req, res) => {
    try {
        const { videoId, videoUrl, transcript, metadata } = req.body;
        
        // YouTube 데이터 수집
        const videoData = await youtubeService.getVideoInfo(videoId);
        
        // AI 서비스 호출 (학습된 모델)
        const analysisResult = await analysisService.analyzeWithTrainedModel({
            videoId,
            videoUrl,
            transcript: transcript || videoData.transcript,
            metadata: metadata || videoData
        });
        
        // 캐시 저장
        await cacheService.set(`analysis:${videoId}`, analysisResult);
        
        res.json(analysisResult);
    } catch (error) {
        logger.error('분석 실패:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});
```

#### 3.2 분석 서비스 업데이트
```javascript
// services/analysisService.js
class AnalysisService {
    constructor() {
        this.aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
        this.aiServiceApiKey = process.env.AI_SERVICE_API_KEY;
    }
    
    async analyzeWithTrainedModel(videoData) {
        try {
            const response = await axios.post(
                `${this.aiServiceUrl}/analyze`,
                {
                    video_id: videoData.videoId,
                    video_url: videoData.videoUrl,
                    transcript: videoData.transcript,
                    metadata: videoData.metadata
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.aiServiceApiKey}`
                    },
                    timeout: 30000 // 30초 타임아웃
                }
            );
            
            return this._formatTrainedModelResult(response.data);
        } catch (error) {
            logger.error('AI 서비스 호출 실패:', error);
            return this._performFallbackAnalysis(videoData);
        }
    }
    
    _formatTrainedModelResult(aiResult) {
        return {
            credibility_score: aiResult.data.credibility_score,
            credibility_grade: this._getGrade(aiResult.data.credibility_score),
            analysis_breakdown: {
                sentiment: aiResult.data.sentiment_score * 100,
                bias: (1 - aiResult.data.bias_score) * 100,
                fact_check: aiResult.data.fact_check_score * 100,
                source: aiResult.data.source_score * 100
            },
            explanation: aiResult.data.explanation,
            confidence: aiResult.data.confidence,
            processing_time: aiResult.processing_time,
            model_version: aiResult.model_version,
            analyzed_at: new Date().toISOString()
        };
    }
}
```

### Phase 4: Chrome Extension 통합

#### 4.1 Content Script 업데이트
```javascript
// chrome-extension/content/content.js
class CredibilityUI {
    async analyzeVideo(videoId) {
        try {
            console.log('Info-Guard: 학습된 모델로 분석 시작');
            
            const response = await fetch('http://localhost:3000/api/v1/analysis/analyze-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    videoId: videoId,
                    videoUrl: window.location.href
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateOverlay(result.data);
                console.log('Info-Guard: 학습된 모델 분석 완료', result.data);
            } else {
                console.error('Info-Guard: 분석 실패', result.error);
            }
        } catch (error) {
            console.error('Info-Guard: 분석 중 오류', error);
        }
    }
    
    updateOverlay(analysisData) {
        const overlay = this.getOrCreateOverlay();
        
        overlay.innerHTML = `
            <div class="info-guard-overlay">
                <div class="credibility-score">
                    <span class="score">${analysisData.credibility_score}/100</span>
                    <span class="grade">${analysisData.credibility_grade}</span>
                </div>
                <div class="breakdown">
                    <div class="metric">
                        <span class="label">감정</span>
                        <span class="value">${analysisData.analysis_breakdown.sentiment}%</span>
                    </div>
                    <div class="metric">
                        <span class="label">편향</span>
                        <span class="value">${analysisData.analysis_breakdown.bias}%</span>
                    </div>
                    <div class="metric">
                        <span class="label">사실검증</span>
                        <span class="value">${analysisData.analysis_breakdown.fact_check}%</span>
                    </div>
                </div>
                <div class="explanation">${analysisData.explanation}</div>
            </div>
        `;
    }
}
```

#### 4.2 Popup 업데이트
```javascript
// chrome-extension/popup/popup.js
class PopupManager {
    async loadCurrentVideo() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab.url.includes('youtube.com/watch')) {
                const videoId = this.extractVideoId(tab.url);
                
                // Content Script에서 분석 결과 가져오기
                const response = await chrome.tabs.sendMessage(tab.id, {
                    type: 'GET_ANALYSIS_STATUS'
                });
                
                if (response && response.success) {
                    this.displayAnalysisResult(response.data);
                } else {
                    // 직접 백엔드 API 호출
                    await this.performDirectAnalysis(videoId);
                }
            } else {
                this.showNoVideoMessage();
            }
        } catch (error) {
            console.error('Popup 오류:', error);
            this.showErrorMessage();
        }
    }
    
    async performDirectAnalysis(videoId) {
        try {
            const response = await fetch('http://localhost:3000/api/v1/analysis/analyze-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ videoId })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayAnalysisResult(result.data);
            } else {
                this.showErrorMessage();
            }
        } catch (error) {
            console.error('직접 분석 실패:', error);
            this.showErrorMessage();
        }
    }
    
    displayAnalysisResult(data) {
        const scoreElement = document.getElementById('credibility-score');
        const gradeElement = document.getElementById('credibility-grade');
        const breakdownElement = document.getElementById('analysis-breakdown');
        
        scoreElement.textContent = `${data.credibility_score}/100`;
        gradeElement.textContent = data.credibility_grade;
        
        breakdownElement.innerHTML = `
            <div class="breakdown-item">
                <span class="label">감정</span>
                <span class="value">${data.analysis_breakdown.sentiment}%</span>
            </div>
            <div class="breakdown-item">
                <span class="label">편향</span>
                <span class="value">${data.analysis_breakdown.bias}%</span>
            </div>
            <div class="breakdown-item">
                <span class="label">사실검증</span>
                <span class="value">${data.analysis_breakdown.fact_check}%</span>
            </div>
            <div class="breakdown-item">
                <span class="label">출처</span>
                <span class="value">${data.analysis_breakdown.source}%</span>
            </div>
        `;
    }
}
```

## 구현 체크리스트

### ✅ Phase 1: 모델 구조 분석
- [ ] 모델 파일 로딩 테스트
- [ ] 입력/출력 형식 확인
- [ ] GPU 호환성 검증
- [ ] 메모리 사용량 측정

### ✅ Phase 2: Python AI 서비스 통합
- [ ] 모델 로딩 서비스 구현
- [ ] 전처리 파이프라인 통합
- [ ] 분석 서비스 업데이트
- [ ] 에러 처리 및 로깅

### ✅ Phase 3: Node.js 백엔드 통합
- [ ] API 엔드포인트 업데이트
- [ ] 분석 서비스 수정
- [ ] 응답 형식 통일
- [ ] 캐싱 시스템 연동

### ✅ Phase 4: Chrome Extension 통합
- [ ] Content Script 업데이트
- [ ] Popup 인터페이스 개선
- [ ] 실시간 분석 결과 표시
- [ ] 에러 처리 개선

## 테스트 계획

### 단위 테스트
```python
# tests/test_trained_model.py
def test_model_loading():
    """모델 로딩 테스트"""
    model_service = TrainedModelService()
    assert model_service.model is not None
    assert model_service.model.training == False

def test_preprocessing():
    """전처리 파이프라인 테스트"""
    preprocessor = PreprocessingService()
    video_data = {
        "title": "테스트 제목",
        "description": "테스트 설명",
        "transcript": "테스트 자막"
    }
    processed = preprocessor.preprocess_video_data(video_data)
    assert "text" in processed
    assert len(processed["text"]) > 0

def test_analysis_pipeline():
    """전체 분석 파이프라인 테스트"""
    analysis_service = TrainedAnalysisService()
    result = analysis_service.analyze_video({
        "title": "신뢰할 수 있는 뉴스",
        "description": "정확한 정보를 제공합니다",
        "transcript": "이 뉴스는 사실을 바탕으로 작성되었습니다"
    })
    assert result["success"] == True
    assert "credibility_score" in result["data"]
```

### 통합 테스트
```javascript
// tests/integration_test.js
describe('Trained Model Integration', () => {
    test('should analyze video with trained model', async () => {
        const response = await request(app)
            .post('/api/v1/analysis/analyze-video')
            .send({
                videoId: 'test_video_id',
                videoUrl: 'https://youtube.com/watch?v=test'
            });
        
        expect(response.status).toBe(200);
        expect(response.body.success).toBe(true);
        expect(response.body.data.credibility_score).toBeDefined();
        expect(response.body.data.model_version).toBe('trained_v1.0');
    });
});
```

## 성능 최적화

### GPU 메모리 관리
```python
# 메모리 사용량 최적화
torch.cuda.empty_cache()  # 메모리 정리
model.half()  # FP16 사용
BATCH_SIZE = 1  # 배치 크기 조정
```

### 응답 시간 최적화
```python
# 캐싱 전략
@lru_cache(maxsize=1000)
def analyze_cached(text_hash):
    return model.analyze(text)

# 비동기 처리
async def analyze_multiple_videos(video_list):
    tasks = [analyze_video(video) for video in video_list]
    return await asyncio.gather(*tasks)
```

## 문제 해결 가이드

### 모델 로딩 실패
```python
# 해결 방법
try:
    model.load_state_dict(torch.load('model.pth', map_location='cpu'))
except Exception as e:
    logger.error(f"모델 로딩 실패: {e}")
    # Fallback 모델 사용
```

### GPU 메모리 부족
```python
# 해결 방법
torch.cuda.empty_cache()
model = model.cpu()  # CPU로 이동
# 또는
model.half()  # FP16 사용
```

### API 응답 형식 불일치
```javascript
// 해결 방법
function normalizeResponse(aiResponse) {
    return {
        credibility_score: aiResponse.credibility_score || 50,
        credibility_grade: getGrade(aiResponse.credibility_score),
        analysis_breakdown: {
            sentiment: aiResponse.sentiment_score * 100,
            bias: (1 - aiResponse.bias_score) * 100,
            fact_check: aiResponse.fact_check_score * 100,
            source: aiResponse.source_score * 100
        }
    };
}
```

## 결론

학습된 모델을 통합하여 실제 의미 있는 신뢰도 분석을 제공할 수 있습니다. 각 단계별로 체계적으로 진행하여 안정적인 시스템을 구축하겠습니다.

### 주요 성과 예상
- ✅ 실제 학습된 모델 활용
- ✅ 정확한 신뢰도 분석
- ✅ 빠른 응답 시간
- ✅ 안정적인 시스템 운영 