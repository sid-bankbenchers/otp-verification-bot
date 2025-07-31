from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)
otp_store = {}  # Temporary in-memory store for OTPs

# === Replace with your D7 settings ===
D7_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoLWJhY2tlbmQ6YXBwIiwic3ViIjoiMzQ2MTJhMjUtYzgzMS00ZjIyLWEwODktODIyMDE0MTU0NzdmIn0.fuGbHVdcHH6JAO5rPyG4ErAG59fVwU8bQtSWI0Ls49w"
D7_SENDER_ID = "SMSInfo"  # Must be approved by D7 (e.g., "SMSInfo")
D7_URL = "https://api.d7networks.com/messages/v1/send"  # D7 base URL

# === Step 1: Send OTP ===
@app.route('/send_otp', methods=['POST'])
def send_otp():
    req = request.get_json()
    try:
        phone_number = req['queryResult']['parameters']['phone-number']
        otp = str(random.randint(100000, 999999))
        otp_store[phone_number] = otp

        message = f"Your OTP for verification is: {otp}"
        payload = {
            "to": f"+91{phone_number}",
            "content": message,
            "from": D7_SENDER_ID,
            "dlr": "yes",
            "dlr-url": "https://yourdomain.com/otp-status",  # Optional
            "sms_type": "plain",
            "api-key": D7_API_KEY
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(D7_URL, json=payload, headers=headers)

        if response.status_code == 200:
            reply = f"OTP sent to {phone_number}. Please enter the OTP to verify."
        else:
            reply = "Failed to send OTP. Please try again."

    except Exception as e:
        reply = "Error processing the request."

    return jsonify({"fulfillmentText": reply})

# === Step 2: Verify OTP ===
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    req = request.get_json()
    try:
        phone_number = req['queryResult']['parameters']['phone-number']
        user_otp = req['queryResult']['parameters']['otp']

        correct_otp = otp_store.get(phone_number)

        if correct_otp and str(user_otp) == correct_otp:
            reply = "✅ OTP Verified successfully!"
            del otp_store[phone_number]
        else:
            reply = "❌ Invalid OTP. Please try again."

    except Exception as e:
        reply = "Error verifying OTP."

    return jsonify({"fulfillmentText": reply})

# === Run locally ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
