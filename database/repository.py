from datetime import datetime
from .connection import sessions_collection

def create_session(user_id, resume_text, job, role):
    data = {
        "_id": user_id,
        "resume_text": resume_text,
        "job_description": job,
        "role": role,
        "status": "waiting",
        "created_at": datetime.utcnow()
    }
    # Use replace_one with upsert to create or updates
    sessions_collection.replace_one({"_id": user_id}, data, upsert=True)

def get_session_by_id(user_id):
    return sessions_collection.find_one({"_id": user_id})

def update_status(user_id, status):
    sessions_collection.update_one(
        {"_id": user_id}, 
        {"$set": {"status": status}}
    )