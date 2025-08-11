"""
Info-Guard Python Server 메인 진입점
FastAPI 애플리케이션을 시작하고 설정합니다.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger
from app.api.v1 import health, analysis, websocket
from app.services import initialize_services, cleanup_services

# 설정 및 로거 초기화
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 이벤트 관리"""
    # 시작 시
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 시작 중...")
    logger.info(f"📡 서버 주소: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"🔧 디버그 모드: {settings.DEBUG}")
    logger.info(f"🤖 GPU 사용: {settings.USE_GPU}")
    
    # 서비스 초기화
    logger.info("🔧 서비스 초기화 중...")
    if await initialize_services():
        logger.info("✅ 모든 서비스 초기화 완료")
    else:
        logger.error("❌ 서비스 초기화 실패")
    
    # WebSocket 연동 설정
    logger.info("🔌 WebSocket 연동 설정 중...")
    try:
        await websocket.setup_websocket_integration()
        logger.info("✅ WebSocket 연동 설정 완료")
    except Exception as e:
        logger.error(f"❌ WebSocket 연동 설정 실패: {e}")
    
    yield
    
    # 종료 시
    logger.info("🛑 서버 종료 중...")
    
    # 서비스 정리
    logger.info("🧹 서비스 정리 중...")
    if await cleanup_services():
        logger.info("✅ 모든 서비스 정리 완료")
    else:
        logger.error("❌ 서비스 정리 실패")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="YouTube 영상 신뢰도 분석을 위한 AI 기반 백엔드 서비스",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(analysis.router, prefix=settings.API_V1_STR, tags=["analysis"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    logger.info("Python 서버 시작 중...")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
