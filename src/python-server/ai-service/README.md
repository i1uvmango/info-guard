# Info-Guard AI Service

YouTube 영상 신뢰도 분석을 위한 AI 서비스입니다.

## 설치

프로젝트 루트의 `src/requirements.txt`를 사용하여 의존성을 설치하세요:

```bash
cd src
pip install -r requirements.txt
```

## 실행

```bash
cd src/ai-service
python main.py
```

또는 개발 모드로:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 기능

- YouTube 영상 신뢰도 분석
- 실시간 WebSocket 통신
- 사용자 피드백 시스템
- 채널별 통계 분석
- 상세 분석 리포트 생성 