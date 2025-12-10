"""
Diagnostic script to test audio flow in real-time
Run this during a live call to see where audio stops
"""
import asyncio
import logging
from services.live_session import LiveSession

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)

class DiagnosticWebSocket:
    """Mock WebSocket that provides diagnostic output"""
    def __init__(self):
        self.audio_received_count = 0
        self.audio_sent_count = 0
        self.messages = []
        self._setup_messages()
        
    def _setup_messages(self):
        """Prepare all messages"""
        import json
        import base64
        
        # Start event
        self.messages.append(json.dumps({
            "event": "start",
            "start": {
                "streamSid": "DIAGNOSTIC_SID",
                "customParameters": {"customer_id": "test_user_1"}
            }
        }))
        
        # Send 100 audio chunks (5 seconds of audio)
        sample_audio = b'\xff' * 160
        for i in range(100):
            self.messages.append(json.dumps({
                "event": "media",
                "media": {"payload": base64.b64encode(sample_audio).decode()}
            }))
        
        # Stop event
        self.messages.append(json.dumps({"event": "stop"}))
    
    async def receive_text(self):
        """Get next message"""
        if self.messages:
            await asyncio.sleep(0.02)
            return self.messages.pop(0)
        await asyncio.sleep(0.1)
        return json.dumps({"event": "stop"})
    
    async def iter_text(self):
        """Iterate through messages"""
        import json
        for msg in self.messages[:]:
            await asyncio.sleep(0.02)
            yield msg
        yield json.dumps({"event": "stop"})
    
    async def send_text(self, data):
        """Track outgoing audio"""
        import json
        msg = json.loads(data)
        if msg.get('event') == 'media':
            self.audio_sent_count += 1
            if self.audio_sent_count % 10 == 0:
                print(f"📢 Audio sent to user: {self.audio_sent_count} chunks")
    
    async def close(self):
        pass

async def run_diagnostic():
    print("\n" + "="*60)
    print("🔍 AUDIO FLOW DIAGNOSTIC")
    print("="*60 + "\n")
    
    ws = DiagnosticWebSocket()
    session = LiveSession(ws)
    
    # Patch Customer lookup
    from unittest.mock import patch
    with patch('services.live_session.Customer.find_by_id') as mock_find:
        mock_find.return_value = {
            'name': 'Test User',
            'bank_details': {'pending_emi_amount': 15000}
        }
        
        print("Starting session...\n")
        await session.connect_and_stream()
    
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC RESULTS")
    print("="*60)
    print(f"Audio received from user: {ws.audio_received_count} chunks")
    print(f"Audio sent to user: {ws.audio_sent_count} chunks")
    print("\n")
    
    if ws.audio_sent_count == 0:
        print("❌ ISSUE: No audio returned to user")
        print("   → Gemini is not generating audio responses")
    elif ws.audio_received_count == 0:
        print("⚠️  WARNING: Audio received but not tracked")
        print("   → Check audio input processing")
    else:
        print("✅ Audio flow appears normal")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())