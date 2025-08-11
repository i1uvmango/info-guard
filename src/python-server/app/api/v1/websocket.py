"""
WebSocket API 모듈
실시간 분석 진행 상황 및 결과를 전송합니다.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from fastapi.responses import HTMLResponse

from app.core.logging import get_logger
from app.services.analysis import analysis_service

router = APIRouter()
logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket 연결을 관리하는 클래스"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.analysis_subscriptions: Dict[str, List[str]] = {}  # analysis_id -> [connection_id]
        self.connection_analyses: Dict[str, List[str]] = {}     # connection_id -> [analysis_id]
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """새로운 WebSocket 연결을 추가합니다."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_analyses[connection_id] = []
        logger.info(f"WebSocket 연결 추가: {connection_id}")
    
    def disconnect(self, connection_id: str):
        """WebSocket 연결을 제거합니다."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 구독 정보 정리
        if connection_id in self.connection_analyses:
            for analysis_id in self.connection_analyses[connection_id]:
                if analysis_id in self.analysis_subscriptions:
                    if connection_id in self.analysis_subscriptions[analysis_id]:
                        self.analysis_subscriptions[analysis_id].remove(connection_id)
                    if not self.analysis_subscriptions[analysis_id]:
                        del self.analysis_subscriptions[analysis_id]
            del self.connection_analyses[connection_id]
        
        logger.info(f"WebSocket 연결 제거: {connection_id}")
    
    async def subscribe_to_analysis(self, connection_id: str, analysis_id: str):
        """특정 분석에 대한 구독을 추가합니다."""
        if connection_id not in self.active_connections:
            return False
        
        # 구독 정보 추가
        if analysis_id not in self.analysis_subscriptions:
            self.analysis_subscriptions[analysis_id] = []
        if connection_id not in self.analysis_subscriptions[analysis_id]:
            self.analysis_subscriptions[analysis_id].append(connection_id)
        
        if connection_id not in self.connection_analyses:
            self.connection_analyses[connection_id] = []
        if analysis_id not in self.connection_analyses[connection_id]:
            self.connection_analyses[connection_id].append(analysis_id)
        
        logger.info(f"분석 구독 추가: {connection_id} -> {analysis_id}")
        return True
    
    async def unsubscribe_from_analysis(self, connection_id: str, analysis_id: str):
        """특정 분석에 대한 구독을 제거합니다."""
        if analysis_id in self.analysis_subscriptions:
            if connection_id in self.analysis_subscriptions[analysis_id]:
                self.analysis_subscriptions[analysis_id].remove(connection_id)
                if not self.analysis_subscriptions[analysis_id]:
                    del self.analysis_subscriptions[analysis_id]
        
        if connection_id in self.connection_analyses:
            if analysis_id in self.connection_analyses[connection_id]:
                self.connection_analyses[connection_id].remove(analysis_id)
        
        logger.info(f"분석 구독 제거: {connection_id} -> {analysis_id}")
    
    async def send_personal_message(self, message: str, connection_id: str):
        """특정 연결에 개인 메시지를 전송합니다."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"개인 메시지 전송 실패: {connection_id} - {e}")
                return False
        return False
    
    async def broadcast_to_analysis(self, message: str, analysis_id: str):
        """특정 분석을 구독하는 모든 연결에 메시지를 브로드캐스트합니다."""
        if analysis_id not in self.analysis_subscriptions:
            return 0
        
        sent_count = 0
        failed_connections = []
        
        for connection_id in self.analysis_subscriptions[analysis_id]:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
            else:
                failed_connections.append(connection_id)
        
        # 실패한 연결 정리
        for connection_id in failed_connections:
            if analysis_id in self.analysis_subscriptions:
                if connection_id in self.analysis_subscriptions[analysis_id]:
                    self.analysis_subscriptions[analysis_id].remove(connection_id)
        
        logger.debug(f"분석 브로드캐스트: {analysis_id} -> {sent_count}개 연결")
        return sent_count
    
    async def broadcast_to_all(self, message: str):
        """모든 활성 연결에 메시지를 브로드캐스트합니다."""
        sent_count = 0
        failed_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"브로드캐스트 메시지 전송 실패: {connection_id} - {e}")
                failed_connections.append(connection_id)
        
        # 실패한 연결 정리
        for connection_id in failed_connections:
            self.disconnect(connection_id)
        
        logger.debug(f"전체 브로드캐스트: {sent_count}개 연결")
        return sent_count
    
    def get_connection_info(self) -> Dict[str, Any]:
        """연결 정보를 반환합니다."""
        return {
            "active_connections": len(self.active_connections),
            "analysis_subscriptions": len(self.analysis_subscriptions),
            "total_subscriptions": sum(len(subs) for subs in self.analysis_subscriptions.values())
        }


# 전역 연결 관리자
manager = ConnectionManager()


@router.get("/ws/test")
async def get_websocket_test_page():
    """WebSocket 테스트 페이지를 반환합니다."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Info-Guard WebSocket 테스트</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background-color: #d4edda; color: #155724; }
            .disconnected { background-color: #f8d7da; color: #721c24; }
            .message { background-color: #e2e3e5; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .input-group { margin: 10px 0; }
            input, button { padding: 8px; margin: 2px; }
            button { background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            button:disabled { background-color: #6c757d; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Info-Guard WebSocket 테스트</h1>
            <p style="color: #6c757d; margin-bottom: 20px;">
                이 페이지는 WebSocket을 통한 실시간 분석 진행 상황 모니터링을 테스트합니다.
                YouTube URL을 입력하고 분석을 시작하면 실시간으로 진행 상황을 확인할 수 있습니다.
            </p>
            
            <div class="input-group">
                <button id="connectBtn" onclick="connect()">연결</button>
                <button id="disconnectBtn" onclick="disconnect()" disabled>연결 해제</button>
            </div>
            
            <div id="status" class="status disconnected">연결되지 않음</div>
            
            <div class="input-group">
                <input type="text" id="analysisId" placeholder="분석 ID" />
                <button onclick="subscribe()">구독</button>
                <button onclick="unsubscribe()">구독 해제</button>
            </div>
            
            <div class="input-group">
                <input type="text" id="videoUrl" placeholder="YouTube URL" />
                <button onclick="startAnalysis()">분석 시작</button>
            </div>
            
            <div class="input-group">
                <button onclick="getStats()">서비스 통계 조회</button>
                <button onclick="getActiveAnalyses()">활성 분석 목록</button>
            </div>
            
            <h3>수신된 메시지:</h3>
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            let connectionId = null;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/analysis`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function(event) {
                    document.getElementById('status').textContent = '연결됨';
                    document.getElementById('status').className = 'status connected';
                    document.getElementById('connectBtn').disabled = true;
                    document.getElementById('disconnectBtn').disabled = false;
                    
                    // 연결 ID 생성
                    connectionId = 'test-' + Date.now();
                    addMessage('시스템', `연결됨 (ID: ${connectionId})`);
                    
                    // 연결 ID를 서버에 전송
                    ws.send(JSON.stringify({
                        type: 'set_connection_id',
                        connection_id: connectionId
                    }));
                };
                
                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    } catch (e) {
                        addMessage('메시지', event.data);
                    }
                };
                
                ws.onclose = function(event) {
                    document.getElementById('status').textContent = '연결 해제됨';
                    document.getElementById('status').className = 'status disconnected';
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('disconnectBtn').disabled = true;
                    addMessage('시스템', '연결이 해제되었습니다.');
                };
                
                ws.onerror = function(error) {
                    addMessage('오류', 'WebSocket 오류가 발생했습니다.');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                    connectionId = null;
                }
            }
            
            function subscribe() {
                const analysisId = document.getElementById('analysisId').value;
                if (!analysisId || !ws) return;
                
                const message = {
                    type: 'subscribe',
                    analysis_id: analysisId,
                    connection_id: connectionId
                };
                
                ws.send(JSON.stringify(message));
                addMessage('구독 요청', `분석 ID: ${analysisId}`);
            }
            
            function unsubscribe() {
                const analysisId = document.getElementById('analysisId').value;
                if (!analysisId || !ws) return;
                
                const message = {
                    type: 'unsubscribe',
                    analysis_id: analysisId,
                    connection_id: connectionId
                };
                
                ws.send(JSON.stringify(message));
                addMessage('구독 해제 요청', `분석 ID: ${analysisId}`);
            }
            
            function getStats() {
                if (!ws) return;
                
                const message = {
                    type: 'get_stats',
                    connection_id: connectionId
                };
                
                ws.send(JSON.stringify(message));
                addMessage('요청', '서비스 통계 조회');
            }
            
            function startAnalysis() {
                const videoUrl = document.getElementById('videoUrl').value;
                if (!videoUrl || !ws) return;
                
                const message = {
                    type: 'start_analysis',
                    video_url: videoUrl,
                    analysis_types: ['bias', 'credibility', 'sentiment'],
                    priority: 'normal',
                    connection_id: connectionId
                };
                
                ws.send(JSON.stringify(message));
                addMessage('요청', `분석 시작: ${videoUrl}`);
            }
            
            function getActiveAnalyses() {
                if (!ws) return;
                
                const message = {
                    type: 'get_active_analyses',
                    connection_id: connectionId
                };
                
                ws.send(JSON.stringify(message));
                addMessage('요청', '활성 분석 목록 조회');
            }
            
            function handleWebSocketMessage(data) {
                const messageType = data.type;
                
                switch (messageType) {
                    case 'analysis_update':
                        handleAnalysisUpdate(data);
                        break;
                    case 'analysis_started':
                        handleAnalysisStarted(data);
                        break;
                    case 'connection_established':
                    case 'subscription_success':
                    case 'unsubscription_success':
                        addMessage('시스템', data.message, 'success');
                        break;
                    case 'error':
                        addMessage('오류', data.message, 'error');
                        break;
                    case 'service_stats':
                    case 'active_analyses':
                        addMessage(data.type, JSON.stringify(data, null, 2));
                        break;
                    default:
                        addMessage(messageType || '메시지', JSON.stringify(data, null, 2));
                }
            }
            
            function handleAnalysisStarted(data) {
                const analysisId = data.analysis_id;
                const videoUrl = data.video_url;
                
                // 분석 카드 생성
                const analysisCard = createAnalysisCard(analysisId);
                
                // 초기 상태 설정
                updateAnalysisCard(analysisCard, {
                    status: 'pending',
                    progress: 0,
                    message: '분석이 시작되었습니다...'
                });
                
                addMessage('분석 시작', `분석 ${analysisId}가 시작되었습니다: ${videoUrl}`, 'success');
            }
            
            function handleAnalysisUpdate(data) {
                const analysisId = data.analysis_id;
                const updateData = data.data;
                
                // 분석 카드 생성 또는 업데이트
                let analysisCard = document.getElementById(`analysis-${analysisId}`);
                if (!analysisCard) {
                    analysisCard = createAnalysisCard(analysisId);
                }
                
                updateAnalysisCard(analysisCard, updateData);
                addMessage('분석 업데이트', `분석 ${analysisId}: ${updateData.message}`, 'analysis-update');
            }
            
            function createAnalysisCard(analysisId) {
                const messagesDiv = document.getElementById('messages');
                const card = document.createElement('div');
                card.id = `analysis-${analysisId}`;
                card.className = 'analysis-card';
                card.innerHTML = `
                    <div class="analysis-header">
                        <span class="analysis-id">${analysisId}</span>
                        <span class="analysis-status status-pending">대기 중</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="analysis-message">분석이 시작되었습니다...</div>
                `;
                messagesDiv.appendChild(card);
                return card;
            }
            
            function updateAnalysisCard(card, data) {
                const statusSpan = card.querySelector('.analysis-status');
                const progressFill = card.querySelector('.progress-fill');
                const messageDiv = card.querySelector('.analysis-message');
                
                // 상태 업데이트
                if (data.status) {
                    statusSpan.textContent = getStatusText(data.status);
                    statusSpan.className = `analysis-status status-${data.status}`;
                }
                
                // 진행률 업데이트
                if (data.progress !== undefined) {
                    progressFill.style.width = `${data.progress}%`;
                }
                
                // 메시지 업데이트
                if (data.message) {
                    messageDiv.textContent = data.message;
                }
            }
            
            function getStatusText(status) {
                const statusMap = {
                    'pending': '대기 중',
                    'processing': '처리 중',
                    'completed': '완료',
                    'failed': '실패'
                };
                return statusMap[status] || status;
            }
            
            function addMessage(type, content, className = '') {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${className}`;
                messageDiv.innerHTML = `<strong>${type}:</strong> ${content}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.websocket("/ws/analysis")
async def websocket_endpoint(websocket: WebSocket):
    """분석 진행 상황을 실시간으로 전송하는 WebSocket 엔드포인트"""
    connection_id = str(uuid4())
    
    try:
        await manager.connect(websocket, connection_id)
        
        # 연결 성공 메시지 전송
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "WebSocket 연결이 성공적으로 설정되었습니다."
            }),
            connection_id
        )
        
        # 메시지 수신 대기
        while True:
            try:
                data = await websocket.receive_text()
                await handle_websocket_message(connection_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 오류: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": f"메시지 처리 오류: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    connection_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 해제: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 연결 오류: {connection_id} - {e}")
    finally:
        manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: str):
    """WebSocket 메시지를 처리합니다."""
    try:
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "subscribe":
            await handle_subscribe(connection_id, data)
        elif message_type == "unsubscribe":
            await handle_unsubscribe(connection_id, data)
        elif message_type == "start_analysis":
            await handle_start_analysis(connection_id, data)
        elif message_type == "get_stats":
            await handle_get_stats(connection_id)
        elif message_type == "get_active_analyses":
            await handle_get_active_analyses(connection_id)
        else:
            await manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": f"지원하지 않는 메시지 타입: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                connection_id
            )
    
    except json.JSONDecodeError:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "잘못된 JSON 형식입니다.",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )
    except Exception as e:
        logger.error(f"WebSocket 메시지 처리 실패: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"메시지 처리 실패: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )


async def handle_subscribe(connection_id: str, data: Dict[str, Any]):
    """분석 구독을 처리합니다."""
    analysis_id = data.get("analysis_id")
    if not analysis_id:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "분석 ID가 필요합니다.",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )
        return
    
    # 구독 추가
    success = await manager.subscribe_to_analysis(connection_id, analysis_id)
    
    if success:
        await manager.send_personal_message(
            json.dumps({
                "type": "subscription_success",
                "analysis_id": analysis_id,
                "message": f"분석 {analysis_id}에 대한 구독이 성공적으로 설정되었습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )
        
        # 현재 분석 상태 전송
        analysis_data = await analysis_service.get_analysis_status(analysis_id)
        if analysis_data:
            await manager.send_personal_message(
                json.dumps({
                    "type": "analysis_status",
                    "analysis_id": analysis_id,
                    "data": analysis_data,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                connection_id
            )
    else:
        await manager.send_personal_message(
            json.dumps({
                "type": "subscription_failed",
                "analysis_id": analysis_id,
                "message": "구독 설정에 실패했습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )


async def handle_unsubscribe(connection_id: str, data: Dict[str, Any]):
    """분석 구독 해제를 처리합니다."""
    analysis_id = data.get("analysis_id")
    if not analysis_id:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": "분석 ID가 필요합니다.",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )
        return
    
    # 구독 해제
    await manager.unsubscribe_from_analysis(connection_id, analysis_id)
    
    await manager.send_personal_message(
        json.dumps({
            "type": "unsubscription_success",
            "analysis_id": analysis_id,
            "message": f"분석 {analysis_id}에 대한 구독이 해제되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }),
        connection_id
    )


async def handle_get_stats(connection_id: str):
    """서비스 통계를 조회합니다."""
    try:
        stats = await analysis_service.get_service_stats()
        connection_info = manager.get_connection_info()
        
        response = {
            "type": "service_stats",
            "analysis_stats": stats,
            "connection_stats": connection_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(json.dumps(response), connection_id)
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"통계 조회 실패: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )


async def handle_start_analysis(connection_id: str, data: Dict[str, Any]):
    """분석 시작을 처리합니다."""
    try:
        video_url = data.get("video_url")
        analysis_types = data.get("analysis_types", ["bias", "credibility", "sentiment"])
        priority = data.get("priority", "normal")
        
        if not video_url:
            await manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": "YouTube URL이 필요합니다.",
                    "timestamp": datetime.utcnow().isoformat()
                }),
                connection_id
            )
            return
        
        # 분석 시작
        analysis_id = await analysis_service.start_analysis(video_url, analysis_types, priority)
        
        # 성공 응답 전송
        await manager.send_personal_message(
            json.dumps({
                "type": "analysis_started",
                "analysis_id": analysis_id,
                "video_url": video_url,
                "message": f"분석이 시작되었습니다. ID: {analysis_id}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )
        
        # 자동으로 해당 분석을 구독
        await manager.subscribe_to_analysis(connection_id, analysis_id)
        
        logger.info(f"WebSocket을 통한 분석 시작: {analysis_id} - {video_url}")
        
    except Exception as e:
        logger.error(f"분석 시작 실패: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"분석 시작 실패: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )


async def handle_get_active_analyses(connection_id: str):
    """활성 분석 목록을 조회합니다."""
    try:
        analyses = await analysis_service.get_active_analyses()
        
        response = {
            "type": "active_analyses",
            "analyses": analyses,
            "count": len(analyses),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.send_personal_message(json.dumps(response), connection_id)
        
    except Exception as e:
        logger.error(f"활성 분석 목록 조회 실패: {e}")
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"활성 분석 목록 조회 실패: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }),
            connection_id
        )


# 분석 서비스에 WebSocket 업데이트 기능 추가
async def setup_websocket_integration():
    """WebSocket과 분석 서비스를 연동합니다."""
    try:
        # 분석 서비스에 WebSocket 매니저 설정
        analysis_service.set_websocket_manager(manager)
        logger.info("WebSocket과 분석 서비스 연동 완료")
        
    except Exception as e:
        logger.error(f"WebSocket 연동 설정 실패: {e}")


# 서비스 시작 시 WebSocket 연동 설정
# 모듈 레벨에서 직접 호출하지 않고, FastAPI 앱 시작 시점에 호출되도록 수정
# asyncio.create_task(setup_websocket_integration())
