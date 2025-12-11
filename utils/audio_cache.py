import time
import threading

class AudioCache:
    """
    Thread-safe in-memory cache for audio data with TTL (Time To Live).
    Replaces disk I/O for temporary TTS files.
    """
    _storage = {}
    _lock = threading.Lock()
    _ttl = 300  # 5 minutes retention
    
    @classmethod
    def set(cls, key: str, data: bytes):
        """Store audio bytes in memory"""
        with cls._lock:
            # Run cleanup occasionally (simple probability or on every write)
            cls._cleanup()
            cls._storage[key] = {
                'data': data,
                'timestamp': time.time()
            }
            
    @classmethod
    def get(cls, key: str) -> bytes:
        """Retrieve audio bytes"""
        with cls._lock:
            item = cls._storage.get(key)
            if item:
                return item['data']
            return None
            
    @classmethod
    def _cleanup(cls):
        """Remove old items to prevent memory leaks"""
        now = time.time()
        # Create list of keys to delete to avoid modifying dict while iterating
        keys_to_delete = [
            k for k, v in cls._storage.items() 
            if now - v['timestamp'] > cls._ttl
        ]
        for k in keys_to_delete:
            del cls._storage[k]

    @classmethod
    def exists(cls, key: str) -> bool:
        with cls._lock:
            return key in cls._storage