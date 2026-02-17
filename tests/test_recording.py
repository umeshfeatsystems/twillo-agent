import asyncio
import websockets
import json
import base64
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

async def test_recording():
    uri = "ws://localhost:8000/api/call/stream"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Send start event
            start_event = {
                "event": "start",
                "start": {
                    "streamSid": "test_stream_123",
                    "customParameters": {
                        "session_id": "test_session_recording"
                    }
                }
            }
            await websocket.send(json.dumps(start_event))
            print("Sent start event")
            
            # Send some mock audio data (silence or noise)
            # 1 second of silence in mulaw is 8000 bytes
            mock_audio = bytes([0xFF] * 8000) 
            encoded_audio = base64.b64encode(mock_audio).decode("utf-8")
            
            media_event = {
                "event": "media",
                "streamSid": "test_stream_123",
                "media": {
                    "payload": encoded_audio
                }
            }
            
            # Send 3 chunks
            for _ in range(3):
                await websocket.send(json.dumps(media_event))
                await asyncio.sleep(0.1)
                
            print("Sent 3 chunks of audio")
            
            # Send stop event
            stop_event = {
                "event": "stop",
                "stop": {
                    "streamSid": "test_stream_123"
                }
            }
            await websocket.send(json.dumps(stop_event))
            print("Sent stop event")
            
            # Wait a bit for server to process and close
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    # Ensure uvicorn is running separately
    print("Ensure server is running at localhost:8000")
    asyncio.run(test_recording())
