from fastapi import FastAPI
from routes import voice
# [FIX 1] Import the call logic router
# (Ensure call_routes.py is inside the 'routes' folder, or adjust import to 'import call_routes' if it's in the root)
from routes import call_routes 
import logging
import uvicorn

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger("MAIN")

app = FastAPI(title="Twilio Gemini Interviewer")

# Include the voice router (handles Twilio streams)
app.include_router(voice.router)

# [FIX 2] Include the call router (handles /api/call/initiate)
app.include_router(call_routes.router)

@app.get("/")
def health_check():
    return {"status": "running", "service": "twilio-gemini-interviewer"}

if __name__ == "__main__":
    # Run the server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)