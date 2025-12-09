from fastapi import APIRouter, Request, Response, Form
from fastapi.responses import JSONResponse
from services.twilio_service import TwilioService
from models.customer import Customer
from datetime import datetime
from pydantic import BaseModel
from config import Config
import logging

logger = logging.getLogger("CALL_ROUTES")

router = APIRouter(prefix="/api/call", tags=["Call Logic"])
twilio_service = TwilioService()

class InitiateCallRequest(BaseModel):
    customer_id: str

@router.post('/initiate')
async def initiate_call(request: InitiateCallRequest):
    customer = Customer.find_by_id(request.customer_id)
    if not customer:
        return JSONResponse({'error': 'Customer not found'}, status_code=404)
    
    result = twilio_service.initiate_call(customer['phone'], request.customer_id)
    return result

@router.post('/handle-answer')
async def handle_answer(
    customer_id: str, 
    CallSid: str = Form(...), 
    # We default to 'human' because we disabled detection
    AnsweredBy: str = Form('human') 
):
    """
    Twilio Webhook: Triggered INSTANTLY when the phone is picked up.
    """
    logger.info(f"📞 Call Answered by {customer_id}. Connecting to stream immediately...")

    # 1. Update DB
    Customer.update_call_history(customer_id, {
        'call_id': CallSid,
        'status': 'live_stream_active',
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # 2. Connect to the Gemini Live Stream IMMEDIATELY
    # No machine checks. Direct connection.
    twiml = twilio_service.generate_stream_twiml(customer_id)
    return Response(content=twiml, media_type="application/xml")