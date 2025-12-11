import time
import threading

class AudioCache:
    """
    Thread-safe in-memory cache with blocking retrieval.
    Allows serving audio before it is fully generated.
    """
    _storage = {}
    _events = {}  # Stores threading.Event() for waiting
    _lock = threading.Lock()
    _ttl = 300
    
    @classmethod
    def reserve_key(cls, key: str):
        """Reserve a key and create a wait event for it"""
        with cls._lock:
            cls._events[key] = threading.Event()

    @classmethod
    def set(cls, key: str, data: bytes):
        """Store audio and notify waiting threads"""
        with cls._lock:
            cls._cleanup()
            cls._storage[key] = {
                'data': data,
                'timestamp': time.time()
            }
            # Wake up anyone waiting for this key
            if key in cls._events:
                cls._events[key].set()
                # Clean up event
                del cls._events[key]
            
    @classmethod
    def get_with_wait(cls, key: str, timeout: int = 5) -> bytes:
        """
        Wait for audio data to appear in cache.
        """
        # 1. Check if already exists
        data = cls.get(key)
        if data:
            return data

        # 2. Get the event to wait on
        event = None
        with cls._lock:
            event = cls._events.get(key)
        
        # 3. Wait if an event exists
        if event:
            flag = event.wait(timeout=timeout)
            if flag:
                return cls.get(key)
        
        return None

    @classmethod
    def get(cls, key: str) -> bytes:
        with cls._lock:
            item = cls._storage.get(key)
            if item:
                return item['data']
            return None

    @classmethod
    def _cleanup(cls):
        now = time.time()
        keys_to_delete = [k for k, v in cls._storage.items() if now - v['timestamp'] > cls._ttl]
        for k in keys_to_delete:
            del cls._storage[k]