from fastapi import FastAPI
from routes import voice
# Ensure call_routes is imported correctly
try:
    from routes import call_routes
except ImportError:
    import call_routes

import logging
import uvicorn
import sys

# --- PROFESSIONAL LOGGING SETUP ---
class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

# Remove default handlers
root_logger = logging.getLogger()
if root_logger.handlers:
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

# Add our custom handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColoredFormatter())
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

# Suppress noisy libraries
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("twilio.http_client").setLevel(logging.WARNING)

logger = logging.getLogger("MAIN")

app = FastAPI(title="Twilio Gemini Interviewer")

# Include Routers
app.include_router(voice.router)
app.include_router(call_routes.router)

@app.get("/")
def health_check():
    return {"status": "running", "service": "twilio-gemini-interviewer"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   🚀 EMI CALL AGENT STARTED - LISTENING ON PORT 8000")
    print("="*60 + "\n")
    # Run the server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="warning")