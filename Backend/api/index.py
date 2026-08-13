from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import json
import smtplib
from email.mime.text import MIMEText
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portfolio-backend")

app = FastAPI(title="Suraj Portfolio Backend", version="1.0.0")

# CORS middleware for local testing and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FeedbackRequest(BaseModel):
    name: str
    email: str
    message: str

# Email Configuration from environment variables
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
except ValueError:
    SMTP_PORT = 465
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SMTP_USER)

IS_VERCEL = "VERCEL" in os.environ

def save_feedback_locally(name: str, email: str, message: str):
    feedback_data = {
        "name": name,
        "email": email,
        "message": message,
        "timestamp": os.environ.get("VERCEL_DEPLOYMENT_ID", "local")
    }
    
    # On Vercel, the filesystem is read-only except /tmp
    file_path = "/tmp/feedback.json" if IS_VERCEL else "feedback.json"
    
    try:
        data = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        
        data.append(feedback_data)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Feedback saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save feedback locally: {str(e)}")
        return False

def send_feedback_email(name: str, email: str, message: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.info("SMTP credentials not configured. Skipping email notification.")
        return False
        
    try:
        msg = MIMEText(f"You received a new message from your portfolio contact form:\n\n"
                       f"Name: {name}\n"
                       f"Email: {email}\n"
                       f"Message:\n{message}")
        msg["Subject"] = f"New Portfolio Message from {name}"
        msg["From"] = SMTP_USER
        msg["To"] = RECEIVER_EMAIL
        
        # Determine whether to use SSL or STARTTLS
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())
        
        logger.info("Feedback email sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "environment": "vercel" if IS_VERCEL else "local"}

@app.post("/api/feedback")
async def receive_feedback(feedback: FeedbackRequest):
    # Validation checks
    name = feedback.name.strip()
    email = feedback.email.strip()
    message = feedback.message.strip()
    
    if not name or not email or not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name, email, and message fields cannot be empty."
        )
        
    # Save feedback locally (handling serverless vs local)
    saved_local = save_feedback_locally(name, email, message)
    
    # Try sending email notification if credentials are set
    sent_email = send_feedback_email(name, email, message)
    
    # Determine the response message
    if sent_email:
        return {"success": True, "message": "Feedback received and notification email sent!"}
    elif saved_local:
        if SMTP_USER:
            return {
                "success": True, 
                "message": "Feedback saved. (Note: Email notification failed, check server logs)."
            }
        else:
            return {
                "success": True,
                "message": "Feedback received successfully! (Running in local/offline mode)."
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback. Please try again later."
        )

# Mount static files for local running
if not IS_VERCEL:
    from fastapi.staticfiles import StaticFiles
    # Mount root directory so index.html, style.css, script.js, and images are served on http://127.0.0.1:8000
    app.mount("/", StaticFiles(directory=".", html=True), name="static")
