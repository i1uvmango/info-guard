"""
WebSocket API 라우터
실시간 분석 진행상황 및 결과 전송을 위한 WebSocket 엔드포인트
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional, Set
import json
import asyncio
from datetime import datetime
import uuid

from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# WebSocket 연결 관리
class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.analysis_subscriptions: Dict[str, Set[str]] = {}  # analysis_id -> connection_ids
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        """새로운 WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)
        
        logger.info(f"WebSocket 연결 수락: {client_id}, 사용자: {user_id}")
        
        # 연결 확인 메시지 전송
        await self.send_personal_message(
            client_id,
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket 연결이 성공적으로 설정되었습니다"
            }
        )
    
    def disconnect(self, client_id: str, user_id: Optional[str] = None):
        """WebSocket 연결 해제"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 분석 구독에서도 제거
        for analysis_id, connections in self.analysis_subscriptions.items():
            connections.discard(client_id)
            if not connections:
                del self.analysis_subscriptions[analysis_id]
        
        logger.info(f"WebSocket 연결 해제: {client_id}")
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """특정 클라이언트에게 메시지 전송"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"개인 메시지 전송 실패: {client_id}, 오류: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_analysis_subscribers(self, analysis_id: str, message: Dict[str, Any]):
        """특정 분석을 구독하는 모든 클라이언트에게 메시지 브로드캐스트"""
        if analysis_id in self.analysis_subscriptions:
            disconnected_clients = []
            
            for client_id in self.analysis_subscriptions[analysis_id]:
                try:
                    await self.send_personal_message(client_id, message)
                except Exception as e:
                    logger.error(f"분석 구독자에게 메시지 전송 실패: {client_id}, 오류: {e}")
                    disconnected_clients.append(client_id)
            
            # 연결이 끊어진 클라이언트 정리
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """특정 사용자의 모든 연결에 메시지 브로드캐스트"""
        if user_id in self.user_connections:
            disconnected_clients = []
            
            for client_id in self.user_connections[user_id]:
                try:
                    await self.send_personal_message(client_id, message)
                except Exception as e:
                    logger.error(f"사용자에게 메시지 전송 실패: {user_id}, 오류: {e}")
                    disconnected_clients.append(client_id)
            
            # 연결이 끊어진 클라이언트 정리
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    def subscribe_to_analysis(self, client_id: str, analysis_id: str):
        """분석 진행상황 구독"""
        if analysis_id not in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id] = set()
        self.analysis_subscriptions[analysis_id].add(client_id)
        logger.info(f"분석 구독 추가: {client_id} -> {analysis_id}")
    
    def unsubscribe_from_analysis(self, client_id: str, analysis_id: str):
        """분석 진행상황 구독 해제"""
        if analysis_id in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id].discard(client_id)
            if not self.analysis_subscriptions[analysis_id]:
                del self.analysis_subscriptions[analysis_id]
        logger.info(f"분석 구독 해제: {client_id} -> {analysis_id}")

# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

# 메시지 타입 정의
class WebSocketMessage:
    """WebSocket 메시지 타입"""
    
    # 연결 관련
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CLOSED = "connection_closed"
    
    # 분석 관련
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_CANCELLED = "analysis_cancelled"
    
    # 구독 관련
    SUBSCRIBE_ANALYSIS = "subscribe_analysis"
    UNSUBSCRIBE_ANALYSIS = "unsubscribe_analysis"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    
    # 에러
    ERROR = "error"
    
    # 시스템
    PING = "ping"
    PONG = "pong"
    HEARTBEAT = "heartbeat"

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: Optional[str] = None
):
    """WebSocket 메인 엔드포인트"""
    try:
        # 연결 수락
        await manager.connect(websocket, client_id, user_id)
        
        # 메시지 수신 루프
        while True:
            try:
                # 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 메시지 타입에 따른 처리
                await handle_websocket_message(client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket 연결 해제: {client_id}")
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    client_id,
                    {
                        "type": WebSocketMessage.ERROR,
                        "error": "잘못된 JSON 형식입니다",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 오류: {client_id}, 오류: {e}")
                await manager.send_personal_message(
                    client_id,
                    {
                        "type": WebSocketMessage.ERROR,
                        "error": f"메시지 처리 중 오류 발생: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    except Exception as e:
        logger.error(f"WebSocket 연결 오류: {client_id}, 오류: {e}")
    finally:
        # 연결 정리
        manager.disconnect(client_id, user_id)

async def handle_websocket_message(client_id: str, message: Dict[str, Any]):
    """WebSocket 메시지 처리"""
    message_type = message.get("type")
    
    if message_type == WebSocketMessage.SUBSCRIBE_ANALYSIS:
        await handle_subscribe_analysis(client_id, message)
    
    elif message_type == WebSocketMessage.UNSUBSCRIBE_ANALYSIS:
        await handle_unsubscribe_analysis(client_id, message)
    
    elif message_type == WebSocketMessage.PING:
        await handle_ping(client_id, message)
    
    elif message_type == WebSocketMessage.HEARTBEAT:
        await handle_heartbeat(client_id, message)
    
    else:
        # 알 수 없는 메시지 타입
        await manager.send_personal_message(
            client_id,
            {
                "type": WebSocketMessage.ERROR,
                "error": f"지원하지 않는 메시지 타입: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
        )

async def handle_subscribe_analysis(client_id: str, message: Dict[str, Any]):
    """분석 진행상황 구독 처리"""
    analysis_id = message.get("analysis_id")
    
    if not analysis_id:
        await manager.send_personal_message(
            client_id,
            {
                "type": WebSocketMessage.ERROR,
                "error": "analysis_id가 필요합니다",
                "timestamp": datetime.now().isoformat()
            }
        )
        return
    
    # 분석 구독 추가
    manager.subscribe_to_analysis(client_id, analysis_id)
    
    # 구독 확인 메시지 전송
    await manager.send_personal_message(
        client_id,
        {
            "type": WebSocketMessage.SUBSCRIPTION_CONFIRMED,
            "analysis_id": analysis_id,
            "message": f"분석 {analysis_id}의 진행상황을 구독합니다",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 현재 분석 상태가 있다면 즉시 전송
    await send_current_analysis_status(client_id, analysis_id)

async def handle_unsubscribe_analysis(client_id: str, message: Dict[str, Any]):
    """분석 진행상황 구독 해제 처리"""
    analysis_id = message.get("analysis_id")
    
    if not analysis_id:
        await manager.send_personal_message(
            client_id,
            {
                "type": WebSocketMessage.ERROR,
                "error": "analysis_id가 필요합니다",
                "timestamp": datetime.now().isoformat()
            }
        )
        return
    
    # 분석 구독 해제
    manager.unsubscribe_from_analysis(client_id, analysis_id)
    
    # 구독 해제 확인 메시지 전송
    await manager.send_personal_message(
        client_id,
        {
            "type": WebSocketMessage.SUBSCRIPTION_CONFIRMED,
            "analysis_id": analysis_id,
            "message": f"분석 {analysis_id}의 구독을 해제했습니다",
            "timestamp": datetime.now().isoformat()
        }
    )

async def handle_ping(client_id: str, message: Dict[str, Any]):
    """Ping 메시지 처리"""
    await manager.send_personal_message(
        client_id,
        {
            "type": WebSocketMessage.PONG,
            "timestamp": datetime.now().isoformat(),
            "echo": message.get("echo", "")
        }
    )

async def handle_heartbeat(client_id: str, message: Dict[str, Any]):
    """Heartbeat 메시지 처리"""
    await manager.send_personal_message(
        client_id,
        {
            "type": WebSocketMessage.HEARTBEAT,
            "timestamp": datetime.now().isoformat(),
            "status": "alive"
        }
    )

async def send_current_analysis_status(client_id: str, analysis_id: str):
    """현재 분석 상태 전송"""
    try:
        # analysis.py의 전역 변수에서 상태 조회
        from .analysis import analysis_tasks, analysis_results
        
        if analysis_id in analysis_tasks:
            task = analysis_tasks[analysis_id]
            
            # 분석 상태 메시지 전송
            status_message = {
                "type": "analysis_status",
                "analysis_id": analysis_id,
                "status": task["status"],
                "progress": task.get("progress", 0),
                "message": task.get("message", ""),
                "created_at": task["created_at"].isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(client_id, status_message)
        
        elif analysis_id in analysis_results:
            result = analysis_results[analysis_id]
            
            # 분석 완료 메시지 전송
            completed_message = {
                "type": WebSocketMessage.ANALYSIS_COMPLETED,
                "analysis_id": analysis_id,
                "result": {
                    "video_id": result.video_id,
                    "video_title": result.video_title,
                    "overall_credibility_score": result.overall_credibility_score,
                    "analysis_types": result.analysis_types,
                    "confidence_scores": result.confidence_scores,
                    "analysis_time_seconds": result.analysis_time_seconds
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_personal_message(client_id, completed_message)
    
    except Exception as e:
        logger.error(f"현재 분석 상태 전송 실패: {client_id}, {analysis_id}, 오류: {e}")

# 외부에서 호출할 수 있는 함수들
async def notify_analysis_started(analysis_id: str, video_title: str):
    """분석 시작 알림 전송"""
    message = {
        "type": WebSocketMessage.ANALYSIS_STARTED,
        "analysis_id": analysis_id,
        "video_title": video_title,
        "message": "분석이 시작되었습니다",
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_analysis_subscribers(analysis_id, message)

async def notify_analysis_progress(analysis_id: str, progress: int, message: str):
    """분석 진행상황 알림 전송"""
    progress_message = {
        "type": WebSocketMessage.ANALYSIS_PROGRESS,
        "analysis_id": analysis_id,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_analysis_subscribers(analysis_id, progress_message)

async def notify_analysis_completed(analysis_id: str, result: Any):
    """분석 완료 알림 전송"""
    completed_message = {
        "type": WebSocketMessage.ANALYSIS_COMPLETED,
        "analysis_id": analysis_id,
        "result": {
            "video_id": result.video_id,
            "video_title": result.video_title,
            "overall_credibility_score": result.overall_credibility_score,
            "analysis_types": result.analysis_types,
            "confidence_scores": result.confidence_scores,
            "analysis_time_seconds": result.analysis_time_seconds
        },
        "message": "분석이 완료되었습니다",
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_analysis_subscribers(analysis_id, completed_message)

async def notify_analysis_failed(analysis_id: str, error_message: str):
    """분석 실패 알림 전송"""
    failed_message = {
        "type": WebSocketMessage.ANALYSIS_FAILED,
        "analysis_id": analysis_id,
        "error": error_message,
        "message": "분석 중 오류가 발생했습니다",
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_analysis_subscribers(analysis_id, failed_message)

async def notify_analysis_cancelled(analysis_id: str):
    """분석 취소 알림 전송"""
    cancelled_message = {
        "type": WebSocketMessage.ANALYSIS_CANCELLED,
        "analysis_id": analysis_id,
        "message": "분석이 취소되었습니다",
        "timestamp": datetime.now().isoformat()
    }
    
    await manager.broadcast_to_analysis_subscribers(analysis_id, cancelled_message)

# 연결 상태 조회 API
@router.get("/connections/status")
async def get_connections_status():
    """현재 WebSocket 연결 상태 조회"""
    return {
        "total_connections": len(manager.active_connections),
        "total_users": len(manager.user_connections),
        "total_analysis_subscriptions": len(manager.analysis_subscriptions),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/connections/user/{user_id}")
async def get_user_connections(user_id: str):
    """특정 사용자의 연결 상태 조회"""
    if user_id not in manager.user_connections:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    connections = list(manager.user_connections[user_id])
    return {
        "user_id": user_id,
        "connection_count": len(connections),
        "connection_ids": connections,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/connections/analysis/{analysis_id}")
async def get_analysis_subscribers(analysis_id: str):
    """특정 분석을 구독하는 클라이언트 조회"""
    if analysis_id not in manager.analysis_subscriptions:
        raise HTTPException(status_code=404, detail="분석을 찾을 수 없습니다")
    
    subscribers = list(manager.analysis_subscriptions[analysis_id])
    return {
        "analysis_id": analysis_id,
        "subscriber_count": len(subscribers),
        "subscriber_ids": subscribers,
        "timestamp": datetime.now().isoformat()
    }

# WebSocket 테스트 페이지
@router.get("/test")
async def websocket_test_page():
    """WebSocket 테스트 페이지"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Info-Guard WebSocket 테스트</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .status {
                padding: 15px;
                margin: 20px 0;
                border-radius: 8px;
                font-weight: bold;
                text-align: center;
            }
            .connected { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .disconnected { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .controls {
                display: flex;
                gap: 10px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            button {
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .connect-btn { background-color: #28a745; color: white; }
            .connect-btn:hover { background-color: #218838; }
            .disconnect-btn { background-color: #dc3545; color: white; }
            .disconnect-btn:hover { background-color: #c82333; }
            .send-btn { background-color: #007bff; color: white; }
            .send-btn:hover { background-color: #0056b3; }
            .subscribe-btn { background-color: #17a2b8; color: white; }
            .subscribe-btn:hover { background-color: #138496; }
            .unsubscribe-btn { background-color: #6c757d; color: white; }
            .unsubscribe-btn:hover { background-color: #545b62; }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .form-group {
                margin: 15px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #495057;
            }
            input, textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
                box-sizing: border-box;
            }
            input:focus, textarea:focus {
                outline: none;
                border-color: #80bdff;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .message-log {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 15px;
                height: 400px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            .message {
                margin: 5px 0;
                padding: 8px;
                border-radius: 4px;
                border-left: 4px solid #dee2e6;
            }
            .message.sent { background-color: #d1ecf1; border-left-color: #17a2b8; }
            .message.received { background-color: #d4edda; border-left-color: #28a745; }
            .message.error { background-color: #f8d7da; border-left-color: #dc3545; }
            .message.system { background-color: #fff3cd; border-left-color: #ffc107; }
            .connection-info {
                background-color: #e9ecef;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #dee2e6;
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }
            .stat-label {
                color: #6c757d;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Info-Guard WebSocket 테스트</h1>
            
            <div id="status" class="status disconnected">
                연결 상태: 연결 안됨
            </div>
            
            <div class="connection-info">
                <h3>연결 정보</h3>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="connectionCount">0</div>
                        <div class="stat-label">활성 연결</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="userCount">0</div>
                        <div class="stat-label">연결된 사용자</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="subscriptionCount">0</div>
                        <div class="stat-label">분석 구독</div>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <button id="connectBtn" class="connect-btn" onclick="connect()">🔌 연결</button>
                <button id="disconnectBtn" class="disconnect-btn" onclick="disconnect()" disabled>❌ 연결 해제</button>
                <button id="pingBtn" class="send-btn" onclick="sendPing()" disabled>🏓 Ping</button>
                <button id="heartbeatBtn" class="send-btn" onclick="sendHeartbeat()" disabled>💓 Heartbeat</button>
            </div>
            
            <div class="grid">
                <div>
                    <h3>📊 분석 구독</h3>
                    <div class="form-group">
                        <label for="analysisId">분석 ID:</label>
                        <input type="text" id="analysisId" placeholder="분석 ID를 입력하세요">
                    </div>
                    <div class="controls">
                        <button class="subscribe-btn" onclick="subscribeAnalysis()" disabled>구독</button>
                        <button class="unsubscribe-btn" onclick="unsubscribeAnalysis()" disabled>구독 해제</button>
                    </div>
                    
                    <h3>📝 테스트 메시지</h3>
                    <div class="form-group">
                        <label for="messageInput">JSON 메시지:</label>
                        <textarea id="messageInput" rows="4" placeholder='{"type": "custom", "data": "test"}'></textarea>
                    </div>
                    <button class="send-btn" onclick="sendCustomMessage()" disabled>전송</button>
                </div>
                
                <div>
                    <h3>📨 메시지 로그</h3>
                    <div id="messages" class="message-log"></div>
                    <div class="controls" style="margin-top: 10px;">
                        <button onclick="clearMessages()" style="background-color: #6c757d; color: white;">로그 지우기</button>
                        <button onclick="exportMessages()" style="background-color: #28a745; color: white;">로그 내보내기</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let clientId = null;
            let isConnected = false;
            
            function connect() {
                if (ws) return;
                
                clientId = 'test_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/ws/${clientId}`;
                
                addMessage(`연결 시도: ${wsUrl}`, 'system');
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    isConnected = true;
                    updateStatus(true);
                    updateButtonStates();
                    addMessage('✅ WebSocket 연결 성공', 'system');
                    addMessage(`클라이언트 ID: ${clientId}`, 'system');
                    
                    // 연결 후 상태 정보 업데이트
                    updateConnectionStats();
                };
                
                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        addMessage(`📥 수신: ${JSON.stringify(data, null, 2)}`, 'received');
                        
                        // 특정 메시지 타입에 따른 처리
                        handleReceivedMessage(data);
                    } catch (e) {
                        addMessage(`📥 수신 (텍스트): ${event.data}`, 'received');
                    }
                };
                
                ws.onclose = function(event) {
                    isConnected = false;
                    updateStatus(false);
                    updateButtonStates();
                    addMessage('❌ WebSocket 연결 해제', 'system');
                    ws = null;
                };
                
                ws.onerror = function(error) {
                    addMessage(`❌ WebSocket 오류: ${error}`, 'error');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function sendPing() {
                if (!ws || !isConnected) return;
                
                const pingMessage = {
                    type: 'ping',
                    echo: 'ping_' + Date.now(),
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(pingMessage));
                addMessage(`📤 Ping 전송: ${JSON.stringify(pingMessage)}`, 'sent');
            }
            
            function sendHeartbeat() {
                if (!ws || !isConnected) return;
                
                const heartbeatMessage = {
                    type: 'heartbeat',
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(heartbeatMessage));
                addMessage(`📤 Heartbeat 전송: ${JSON.stringify(heartbeatMessage)}`, 'sent');
            }
            
            function subscribeAnalysis() {
                if (!ws || !isConnected) return;
                
                const analysisId = document.getElementById('analysisId').value.trim();
                if (!analysisId) {
                    addMessage('❌ 분석 ID를 입력해주세요', 'error');
                    return;
                }
                
                const subscribeMessage = {
                    type: 'subscribe_analysis',
                    analysis_id: analysisId,
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(subscribeMessage));
                addMessage(`📤 구독 요청: ${JSON.stringify(subscribeMessage)}`, 'sent');
            }
            
            function unsubscribeAnalysis() {
                if (!ws || !isConnected) return;
                
                const analysisId = document.getElementById('analysisId').value.trim();
                if (!analysisId) {
                    addMessage('❌ 분석 ID를 입력해주세요', 'error');
                    return;
                }
                
                const unsubscribeMessage = {
                    type: 'unsubscribe_analysis',
                    analysis_id: analysisId,
                    timestamp: new Date().toISOString()
                };
                
                ws.send(JSON.stringify(unsubscribeMessage));
                addMessage(`📤 구독 해제 요청: ${JSON.stringify(unsubscribeMessage)}`, 'sent');
            }
            
            function sendCustomMessage() {
                if (!ws || !isConnected) return;
                
                const messageInput = document.getElementById('messageInput').value.trim();
                if (!messageInput) {
                    addMessage('❌ 메시지를 입력해주세요', 'error');
                    return;
                }
                
                try {
                    const message = JSON.parse(messageInput);
                    ws.send(JSON.stringify(message));
                    addMessage(`📤 사용자 정의 메시지 전송: ${messageInput}`, 'sent');
                } catch (e) {
                    addMessage(`❌ 잘못된 JSON 형식: ${e.message}`, 'error');
                }
            }
            
            function handleReceivedMessage(data) {
                // 특정 메시지 타입에 따른 처리
                if (data.type === 'connection_established') {
                    addMessage(`✅ 연결 확인됨: ${data.message}`, 'system');
                } else if (data.type === 'subscription_confirmed') {
                    addMessage(`✅ 구독 확인: ${data.message}`, 'system');
                } else if (data.type === 'analysis_status') {
                    addMessage(`📊 분석 상태: ${data.status} (${data.progress}%) - ${data.message}`, 'system');
                } else if (data.type === 'analysis_started') {
                    addMessage(`🚀 분석 시작: ${data.video_title}`, 'system');
                } else if (data.type === 'analysis_progress') {
                    addMessage(`📈 분석 진행: ${data.progress}% - ${data.message}`, 'system');
                } else if (data.type === 'analysis_completed') {
                    addMessage(`✅ 분석 완료: ${data.result.video_title} (신뢰도: ${data.result.overall_credibility_score})`, 'system');
                } else if (data.type === 'analysis_failed') {
                    addMessage(`❌ 분석 실패: ${data.error}`, 'error');
                } else if (data.type === 'analysis_cancelled') {
                    addMessage(`⏹️ 분석 취소됨`, 'system');
                }
            }
            
            function updateStatus(connected) {
                const statusDiv = document.getElementById('status');
                if (connected) {
                    statusDiv.className = 'status connected';
                    statusDiv.textContent = '✅ 연결 상태: 연결됨';
                } else {
                    statusDiv.className = 'status disconnected';
                    statusDiv.textContent = '❌ 연결 상태: 연결 안됨';
                }
            }
            
            function updateButtonStates() {
                const connectBtn = document.getElementById('connectBtn');
                const disconnectBtn = document.getElementById('disconnectBtn');
                const pingBtn = document.getElementById('pingBtn');
                const heartbeatBtn = document.getElementById('heartbeatBtn');
                const subscribeBtn = document.querySelector('.subscribe-btn');
                const unsubscribeBtn = document.querySelector('.unsubscribe-btn');
                const sendBtn = document.querySelector('.send-btn');
                
                if (isConnected) {
                    connectBtn.disabled = true;
                    disconnectBtn.disabled = false;
                    pingBtn.disabled = false;
                    heartbeatBtn.disabled = false;
                    subscribeBtn.disabled = false;
                    unsubscribeBtn.disabled = false;
                    sendBtn.disabled = false;
                } else {
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                    pingBtn.disabled = true;
                    heartbeatBtn.disabled = true;
                    subscribeBtn.disabled = true;
                    unsubscribeBtn.disabled = true;
                    sendBtn.disabled = true;
                }
            }
            
            function addMessage(text, type) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
            
            function exportMessages() {
                const messages = document.getElementById('messages').innerText;
                const blob = new Blob([messages], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `websocket_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
                a.click();
                URL.revokeObjectURL(url);
            }
            
            async function updateConnectionStats() {
                try {
                    const response = await fetch('/ws/connections/status');
                    const stats = await response.json();
                    
                    document.getElementById('connectionCount').textContent = stats.total_connections;
                    document.getElementById('userCount').textContent = stats.total_users;
                    document.getElementById('subscriptionCount').textContent = stats.total_analysis_subscriptions;
                } catch (error) {
                    console.error('연결 통계 업데이트 실패:', error);
                }
            }
            
            // 주기적으로 연결 통계 업데이트
            setInterval(() => {
                if (isConnected) {
                    updateConnectionStats();
                }
            }, 5000);
            
            // 페이지 로드 시 초기화
            document.addEventListener('DOMContentLoaded', function() {
                addMessage('🚀 WebSocket 테스트 페이지 로드됨', 'system');
                addMessage('🔌 "연결" 버튼을 클릭하여 WebSocket 연결을 시작하세요', 'system');
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
