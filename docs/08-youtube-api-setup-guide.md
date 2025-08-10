# YouTube API 키 설정 가이드

## 개요
Info-Guard 프로젝트에서 YouTube 영상 정보를 가져오기 위해 YouTube Data API v3를 사용합니다. 이 가이드는 API 키를 설정하는 방법을 설명합니다.

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 이름: `Info-Guard` (또는 원하는 이름)

### 1.2 YouTube Data API v3 활성화
1. 왼쪽 메뉴에서 "API 및 서비스" → "라이브러리" 선택
2. 검색창에 "YouTube Data API v3" 입력
3. YouTube Data API v3 선택 후 "사용" 버튼 클릭

### 1.3 사용자 인증 정보 생성
1. "API 및 서비스" → "사용자 인증 정보" 선택
2. "사용자 인증 정보 만들기" → "API 키" 선택
3. 생성된 API 키 복사

## 2. API 키 보안 설정

### 2.1 API 키 제한 설정
1. 생성된 API 키 클릭
2. "애플리케이션 제한사항" 섹션에서 "HTTP 리퍼러" 선택
3. "웹사이트 제한사항"에 다음 도메인 추가:
   - `http://localhost:8000/*`
   - `http://localhost:3000/*`
   - `chrome-extension://*`

### 2.2 API 제한 설정
1. "API 제한사항" 섹션에서 "API 제한" 선택
2. "YouTube Data API v3"만 선택
3. "저장" 클릭

## 3. 환경 변수에 API 키 추가

### 3.1 .env 파일 업데이트
```bash
# .env 파일에서 다음 줄을 찾아 실제 API 키로 교체
YOUTUBE_API_KEY=your_actual_youtube_api_key_here
```

### 3.2 API 키 테스트
```bash
# API 키 유효성 테스트
curl "https://www.googleapis.com/youtube/v3/videos?id=dQw4w9WgXcQ&key=YOUR_API_KEY"
```

## 4. 할당량 관리

### 4.1 기본 할당량
- YouTube Data API v3: 일일 10,000 유닛
- 비디오 정보 조회: 1회당 1 유닛
- 채널 정보 조회: 1회당 1 유닛

### 4.2 할당량 모니터링
1. Google Cloud Console → "API 및 서비스" → "대시보드"
2. YouTube Data API v3 선택
3. "할당량" 탭에서 사용량 확인

### 4.3 할당량 증가 요청 (필요시)
1. "할당량" 탭에서 "할당량 편집" 클릭
2. 증가 요청 양식 작성
3. 사용 사례 및 필요성 설명

## 5. 코드에서 API 키 사용

### 5.1 Python (AI 서비스)
```python
import os
from dotenv import load_dotenv

load_dotenv()
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

if not youtube_api_key:
    raise ValueError("YouTube API 키가 설정되지 않았습니다.")
```

### 5.2 JavaScript (Chrome Extension)
```javascript
// 환경 변수는 빌드 시점에 주입되므로 별도 설정 필요
const YOUTUBE_API_KEY = process.env.YOUTUBE_API_KEY;
```

## 6. 문제 해결

### 6.1 API 키 오류
**문제**: `API key not valid` 오류
**해결**:
- API 키가 올바르게 복사되었는지 확인
- API 키 제한 설정 확인
- 프로젝트에서 YouTube Data API v3가 활성화되었는지 확인

### 6.2 할당량 초과
**문제**: `Quota exceeded` 오류
**해결**:
- 할당량 사용량 확인
- 요청 빈도 줄이기
- 할당량 증가 요청

### 6.3 리퍼러 제한
**문제**: `Referer not allowed` 오류
**해결**:
- API 키 설정에서 허용된 도메인 확인
- 개발 환경에서는 `localhost` 추가

## 7. 보안 고려사항

### 7.1 API 키 보호
- API 키를 소스 코드에 직접 포함하지 않기
- .env 파일을 .gitignore에 추가
- 프로덕션 환경에서는 환경 변수 사용

### 7.2 할당량 보호
- 요청 빈도 제한 구현
- 캐싱 전략 사용
- 에러 처리 및 재시도 로직 구현

## 8. 테스트

### 8.1 API 키 테스트 스크립트
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_youtube_api():
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ YouTube API 키가 설정되지 않았습니다.")
        return False
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        'id': 'dQw4w9WgXcQ',
        'key': api_key,
        'part': 'snippet'
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("✅ YouTube API 키가 정상적으로 작동합니다.")
            return True
        else:
            print(f"❌ API 요청 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 요청 중 오류: {e}")
        return False

if __name__ == "__main__":
    test_youtube_api()
```

### 8.2 실행 방법
```bash
cd src/ai-service
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv('../.env')
api_key = os.getenv('YOUTUBE_API_KEY')
if api_key and api_key != 'your_youtube_api_key_here':
    print('✅ YouTube API 키가 설정되었습니다.')
else:
    print('❌ YouTube API 키 설정이 필요합니다.')
"
```

## 9. 다음 단계

API 키 설정 완료 후:
1. AI 서비스에서 YouTube API 테스트
2. Chrome Extension에서 API 호출 테스트
3. 전체 시스템 통합 테스트
4. 성능 최적화 및 모니터링 설정

---

**참고**: 이 가이드를 따라 YouTube API 키를 설정한 후, 실제 API 키를 .env 파일에 추가하세요. 보안을 위해 API 키는 절대 공개 저장소에 커밋하지 마세요. 