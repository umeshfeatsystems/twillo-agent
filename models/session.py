from datetime import datetime
from utils.db import db_instance
import uuid

class CallSession:
    collection_name = 'call_sessions'

    @staticmethod
    def get_collection():
        return db_instance.get_db()[CallSession.collection_name]

    @staticmethod
    def create(phone, system_prompt, initial_greeting, call_details=None):
        session_id = str(uuid.uuid4())
        session_data = {
            'session_id': session_id,
            'phone': phone,
            'system_prompt': system_prompt,     # <--- The formatted string is stored here
            'initial_greeting': initial_greeting,
            'call_details': call_details or {},
            'conversation_history': [],
            'created_at': datetime.utcnow()
        }
        CallSession.get_collection().insert_one(session_data)
        return session_id

    @staticmethod
    def find_by_session_id(sid):
        return CallSession.get_collection().find_one({'session_id': sid})
    
    @staticmethod
    def update_call_sid(sid, call_sid):
        CallSession.get_collection().update_one({'session_id': sid}, {'$set': {'call_sid': call_sid}})

    @staticmethod
    def append_history(sid, turn):
        # turn = {"role": "user"|"assistant", "content": "text"}
        CallSession.get_collection().update_one({'session_id': sid}, {'$push': {'conversation_history': turn}})