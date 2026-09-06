from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portfolio-backend")

app = FastAPI(title="Suraj Portfolio Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactRequest(BaseModel):
    name: str
    email: str
    message: str

# ── Email Configuration (set these in Vercel Environment Variables) ──────────
SMTP_SERVER   = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER     = os.environ.get("SMTP_USER", "")        # your Gmail address
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")    # Gmail App Password
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", SMTP_USER)  # where to receive mails


def send_contact_email(name: str, sender_email: str, message: str) -> bool:
    """Send contact form message to portfolio owner's Gmail."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email send.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📬 New Portfolio Message from {name}"
        msg["From"]    = SMTP_USER
        msg["To"]      = RECEIVER_EMAIL
        msg["Reply-To"] = sender_email   # so you can reply directly to the sender

        # Plain text fallback
        plain = (
            f"You received a new message from your portfolio contact form.\n\n"
            f"Name   : {name}\n"
            f"Email  : {sender_email}\n"
            f"Message:\n{message}\n\n"
            f"---\nSent from your portfolio contact form."
        )

        # Rich HTML version
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto;">
            <div style="background: linear-gradient(135deg,#6c63ff,#3ecfcf); padding: 20px; border-radius: 8px 8px 0 0;">
              <h2 style="color:#fff; margin:0;">📬 New Portfolio Message</h2>
            </div>
            <div style="border: 1px solid #ddd; border-top:none; padding: 24px; border-radius: 0 0 8px 8px;">
              <p><strong>Name:</strong> {name}</p>
              <p><strong>Email:</strong> <a href="mailto:{sender_email}">{sender_email}</a></p>
              <p><strong>Message:</strong></p>
              <blockquote style="border-left:4px solid #6c63ff; margin:0; padding: 10px 16px; background:#f9f9ff; border-radius:4px;">
                {message.replace(chr(10), '<br>')}
              </blockquote>
              <hr style="margin-top:24px; border:none; border-top:1px solid #eee;">
              <p style="color:#999; font-size:12px;">Sent from your portfolio contact form at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, RECEIVER_EMAIL, msg.as_string())

        logger.info(f"Email sent successfully for contact from {sender_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed — check SMTP_USER and SMTP_PASSWORD (use Gmail App Password, not your real password).")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


@app.get("/api/health")
async def health_check():
    smtp_configured = bool(SMTP_USER and SMTP_PASSWORD)
    return {
        "status": "ok",
        "smtp_configured": smtp_configured,
        "receiver": RECEIVER_EMAIL if smtp_configured else "not set"
    }


@app.post("/api/feedback")
async def receive_feedback(contact: ContactRequest):
    name    = contact.name.strip()
    email   = contact.email.strip()
    message = contact.message.strip()

    if not name or not email or not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name, email, and message fields cannot be empty."
        )

    email_sent = send_contact_email(name, email, message)

    if email_sent:
        return {
            "success": True,
            "message": "Your message was sent successfully! I'll get back to you soon. 🎉"
        }
    elif not SMTP_USER or not SMTP_PASSWORD:
        # SMTP not configured on server — tell owner to set env vars
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Contact form is not configured yet. Please set SMTP_USER and SMTP_PASSWORD in Vercel environment variables."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send your message. Please try again or email me directly at khadesuraj80@gmail.com"
        )
