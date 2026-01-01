import time
import threading

class AudioCache:
    """
    Thread-safe in-memory cache with blocking retrieval.
    Allows serving audio before it is fully generated.
    """
    _storage = {}
    _events = {}
    _lock = threading.Lock()
    _ttl = 300
    
    @classmethod
    def reserve_key(cls, key: str):
        """Reserve a key and create a wait event for it"""
        with cls._lock:
            print(f"[CACHE] Reserved key: {key}")
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
                print(f"[CACHE] Waking up waiter for: {key}")
                cls._events[key].set()
                del cls._events[key]
            else:
                print(f"[CACHE] Stored data for: {key} (No waiters)")
            
    @classmethod
    def get_with_wait(cls, key: str, timeout: int = 10) -> bytes:
        """
        Wait up to 10 seconds (increased from 5) for audio.
        """
        start_time = time.time()
        
        # 1. Check if already exists
        data = cls.get(key)
        if data:
            print(f"[CACHE] Immediate hit: {key}")
            return data

        # 2. Get the event to wait on
        event = None
        with cls._lock:
            event = cls._events.get(key)
        
        # 3. Wait if an event exists
        if event:
            print(f"[CACHE] Waiting for {key} (Timeout: {timeout}s)...")
            flag = event.wait(timeout=timeout)
            if flag:
                elapsed = time.time() - start_time
                print(f"[CACHE] Data arrived for {key} after {elapsed:.2f}s")
                return cls.get(key)
            else:
                print(f"[CACHE] TIMEOUT waiting for {key}")
        else:
            print(f"[CACHE] Key not reserved/found: {key}")
        
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