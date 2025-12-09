from fastapi import APIRouter, WebSocket, Request, Response
# [FIX 1] Import the correct class name 'LiveSession'
from services.live_session import LiveSession
import config
import logging

router = APIRouter()
logger = logging.getLogger("VOICE_ROUTER")

@router.post("/voice/incoming")
async def handle_incoming_call(request: Request, user_id: str = None):
    """
    Simplified Webhook.
    """
    host = request.headers.get("host")
    
    # Determine which User/Customer Profile to load
    target_user = user_id if user_id else config.DEFAULT_USER_ID
    
    logger.info(f"📞 Incoming Call. Loading Profile: {target_user}")
    
    ws_url = f"wss://{host}/voice/stream"
    
    # [FIX 2] Changed parameter name from 'user_id' to 'customer_id' 
    # to match what LiveSession expects in _build_system_instruction
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>Connecting to the AI interviewer.</Say>
        <Connect>
            <Stream url="{ws_url}">
                <Parameter name="customer_id" value="{target_user}" />
            </Stream>
        </Connect>
        <Pause length="1"/>
        <Say>The connection was lost.</Say>
    </Response>
    """
    return Response(content=xml_response, media_type="application/xml")

@router.websocket("/voice/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # [FIX 3] Use LiveSession class
    session = LiveSession(websocket)
    # [FIX 4] Use the correct method 'connect_and_stream' instead of 'start'
    await session.connect_and_stream()