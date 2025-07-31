from flask import Flask, request, jsonify
import requests
import random
import os

app = Flask(__name__)
otp_store = {}  # Temporary in-memory store for OTPs

# === D7 API Settings ===
D7_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoLWJhY2tlbmQ6YXBwIiwic3ViIjoiNjlkMGE3OWYtNTE1Ni00Y2YwLWEwMGEtZjgxZTNlMDg3ZmUzIn0.Yl5Ers65atUJjSmEhubqexnBngTVL7z7uaKQNg_ggPI"  # REPLACE THIS with your latest D7 key
D7_SENDER_ID = "SMSInfo"  # Must be pre-approved by D7
D7_URL = "https://api.d7networks.com/messages/v1/send"

# === Send OTP Handler ===
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
            "dlr-url": "https://yourdomain.com/otp-status",
            "sms_type": "plain"
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {D7_API_KEY}'
        }

        response = requests.post(D7_URL, json=payload, headers=headers)

        if response.status_code == 200:
            reply = f"✅ OTP sent to {phone_number}. Please enter the OTP to verify."
        else:
            print("D7 ERROR:", response.status_code, response.text)
            reply = f"❌ Failed to send OTP. D7 API responded with {response.status_code}: {response.text}"

    except Exception as e:
        print("Exception in send_otp:", e)
        reply = "⚠️ Error processing the OTP request."

    return jsonify({"fulfillmentText": reply})



# === Verify OTP Handler ===
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
        print("Exception in verify_otp:", e)
        reply = "⚠️ Error verifying the OTP."

    return jsonify({"fulfillmentText": reply})


# === Dispatcher for Dialogflow ===
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json()
    intent = req['queryResult']['intent']['displayName'].lower()

    if intent == 'number':
        return send_otp()
    elif intent == 'otp':
        return verify_otp()
    else:
        return jsonify({"fulfillmentText": "❓ I didn't understand that request."})


# === Run the Flask app ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
