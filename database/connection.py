from pymongo import MongoClient
import sys
import os

# Use environment variable or default local
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "gemini_interviewer"

class Database:
    client: MongoClient = None
    db = None

    @classmethod
    def connect(cls):
        try:
            cls.client = MongoClient(MONGO_URI)
            cls.db = cls.client[DB_NAME]
            print("✅ Connected to MongoDB.")
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            # Don't exit here, just print error so server doesn't crash immediately
            pass

    @classmethod
    def get_collection(cls, name):
        if cls.db is None:
            cls.connect()
        return cls.db[name]

# Initialize
Database.connect()
sessions_collection = Database.get_collection("sessions")