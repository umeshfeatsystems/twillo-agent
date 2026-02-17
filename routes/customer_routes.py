"""
Customer Management & Call History API Routes
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.db import db_instance

logger = logging.getLogger("CustomerRoutes")
router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str
    phone: str
    amount: float
    loan_type: str = "Personal Loan"
    due_date: str = ""
    days_overdue: int = 0
    bank_name: str = "HDFC Bank"


class PromptUpdate(BaseModel):
    system_prompt: str
    initial_greeting: str
    tone: str = "professional"


# ─── Customer CRUD ───

@router.get("")
async def list_customers():
    """List all customers"""
    db = db_instance.get_db()
    customers = list(db["customers"].find().sort("created_at", -1))
    for c in customers:
        c["_id"] = str(c["_id"])
    return {"customers": customers}


@router.post("")
async def add_customer(customer: CustomerCreate):
    """Add a new customer"""
    db = db_instance.get_db()
    doc = customer.dict()
    doc["created_at"] = datetime.utcnow()
    doc["last_called"] = None
    doc["call_count"] = 0
    result = db["customers"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {"success": True, "customer": doc}


@router.delete("/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete a customer"""
    db = db_instance.get_db()
    result = db["customers"].delete_one({"_id": ObjectId(customer_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True}


@router.put("/{customer_id}/called")
async def mark_customer_called(customer_id: str):
    """Mark customer as called (updates last_called timestamp)"""
    db = db_instance.get_db()
    db["customers"].update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"last_called": datetime.utcnow()}, "$inc": {"call_count": 1}}
    )
    return {"success": True}


# ─── Call History ───

@router.get("/call-history")
async def get_call_history():
    """Get recent call history from sessions"""
    db = db_instance.get_db()
    sessions = list(
        db["call_sessions"]
        .find({}, {"session_id": 1, "phone": 1, "call_details": 1, "created_at": 1, "call_sid": 1})
        .sort("created_at", -1)
        .limit(20)
    )
    for s in sessions:
        s["_id"] = str(s["_id"])
    return {"history": sessions}


# ─── Prompt Management ───

prompt_router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@prompt_router.get("/emi")
async def get_emi_prompt():
    """Get current EMI prompt (from DB or default)"""
    db = db_instance.get_db()
    saved = db["prompt_templates"].find_one({"type": "emi_reminder"})
    
    if saved:
        saved["_id"] = str(saved["_id"])
        return {"prompt": saved}
    
    # Return default from file
    from prompts.emi_prompt import EMI_REMINDER_PROMPT
    return {
        "prompt": {
            "type": "emi_reminder",
            "system_prompt": EMI_REMINDER_PROMPT["system_prompt"],
            "initial_greeting": EMI_REMINDER_PROMPT["initial_greeting"],
            "tone": "professional",
            "is_default": True
        }
    }


@prompt_router.put("/emi")
async def update_emi_prompt(update: PromptUpdate):
    """Save custom EMI prompt"""
    db = db_instance.get_db()
    db["prompt_templates"].update_one(
        {"type": "emi_reminder"},
        {"$set": {
            "type": "emi_reminder",
            "system_prompt": update.system_prompt,
            "initial_greeting": update.initial_greeting,
            "tone": update.tone,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    return {"success": True}


@prompt_router.delete("/emi")
async def reset_emi_prompt():
    """Reset to default prompt"""
    db = db_instance.get_db()
    db["prompt_templates"].delete_one({"type": "emi_reminder"})
    return {"success": True}


TONE_PRESETS = {
    "professional": {
        "name": "Professional",
        "description": "Formal, business-like tone",
        "instruction": "TONE: Be formal, professional, and business-like. Use proper language and maintain a courteous demeanor."
    },
    "friendly": {
        "name": "Friendly",
        "description": "Warm, approachable, conversational",
        "instruction": "TONE: Be warm, friendly, and approachable. Speak like a helpful friend who genuinely cares. Use casual but respectful language."
    },
    "empathetic": {
        "name": "Empathetic",
        "description": "Understanding, patient, supportive",
        "instruction": "TONE: Be deeply empathetic and understanding. Acknowledge the customer's feelings. Be patient and supportive. Show genuine concern for their situation."
    },
    "firm": {
        "name": "Firm",
        "description": "Direct, clear, assertive but polite",
        "instruction": "TONE: Be direct, clear, and assertive while remaining polite. Get to the point quickly. Emphasize the importance of timely payment."
    },
    "gentle": {
        "name": "Gentle",
        "description": "Soft-spoken, very patient, encouraging",
        "instruction": "TONE: Be very gentle and soft-spoken. Use encouraging words. Be extremely patient. Make the customer feel comfortable and not pressured."
    }
}


@prompt_router.get("/tones")
async def get_tone_presets():
    """List available tone presets"""
    return {"tones": TONE_PRESETS}
