from fastapi import APIRouter, WebSocket
from services.live_session import LiveSession

router = APIRouter(prefix="/voice", tags=["Voice Stream"])

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.
    """
    await websocket.accept()
    session = LiveSession(websocket)
    await session.connect_and_stream()