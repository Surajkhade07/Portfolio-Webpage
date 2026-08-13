from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# Configure your Email
YOUR_EMAIL = "khadesuraj80@gmail.com"        # your email
YOUR_PASSWORD = ""  # gmail app password (not your real password)
RECEIVER_EMAIL = "khadesuraj80@gmail.com"    # where message should arrive

@app.route("/contact", methods=["POST"])
def contact():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    try:
        # email content
        msg = MIMEText(f"Name: {name}\nEmail: {email}\nMessage:\n{message}")
        msg["Subject"] = "New Contact Form Message"
        msg["From"] = YOUR_EMAIL
        msg["To"] = RECEIVER_EMAIL

        # send mail using Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(YOUR_EMAIL, YOUR_PASSWORD)
            server.sendmail(YOUR_EMAIL, RECEIVER_EMAIL, msg.as_string())

        return jsonify({"success": True, "message": "Message sent!"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
