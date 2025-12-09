from pymongo import MongoClient
from config import Config

class Database:
    _instance = None
    _client = None
    _db = None
    
    def connect(self):
        # 1. Initialize Client if not exists
        if self._client is None:
            self._client = MongoClient(Config.MONGODB_URI)
            
        # 2. Select Database (Fix for "No default database" error)
        if self._db is None:
            # Try to get DB_NAME from Config, otherwise default to 'gemini_live_db'
            db_name = getattr(Config, 'DB_NAME', 'gemini_live_db')
            self._db = self._client[db_name]
            print(f"✓ MongoDB Connected to database: {db_name}")

db_instance = Database()