"""
Info-Guard AI 서버
YouTube 영상 신뢰도 분석을 위한 AI 기반 백엔드 서비스
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from contextlib import asynccontextmanager

from api.routers import health, analysis, websocket
from utils.config import settings
from utils.logger import setup_logging
from utils.security import setup_secure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    logging.info("Info-Guard AI 서버 시작 중...")
    
    # AI 모델 로드
    from ai_models.model_manager import ModelManager
    app.state.model_manager = ModelManager()
    await app.state.model_manager.initialize()
    
    logging.info("Info-Guard AI 서버 시작 완료")
    
    yield
    
    # 종료 시 정리
    logging.info("Info-Guard AI 서버 종료 중...")
    if hasattr(app.state, 'model_manager'):
        await app.state.model_manager.cleanup()
    logging.info("Info-Guard AI 서버 종료 완료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title="Info-Guard AI Server",
        description="YouTube 영상 신뢰도 분석 AI 서비스",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # 라우터 등록
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
    
    return app


app = create_app()


if __name__ == "__main__":
    # 보안 로깅 설정 (API 키 마스킹 등)
    setup_secure_logging()
    
    # 로깅 설정
    setup_logging()
    
    # 서버 실행
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
