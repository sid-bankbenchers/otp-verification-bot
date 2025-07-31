from fastapi import FastAPI, Request
from pydantic import BaseModel
import random
import time
import requests
import os

app = FastAPI()

# In-memory OTP store: {phone: (otp, expiry_time)
otp_store = {}

# D7 credentials (store these in environment variables ideally)
D7_API_KEY = "YOUR_D7_API_KEY"
D7_URL = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoLWJhY2tlbmQ6YXBwIiwic3ViIjoiNjlkMGE3OWYtNTE1Ni00Y2YwLWEwMGEtZjgxZTNlMDg3ZmUzIn0.Yl5Ers65atUJjSmEhubqexnBngTVL7z7uaKQNg_ggPI"
D7_ORIGINATOR = "SignOTP"

# === Helpers ===

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_via_sms(phone_number: str, otp: str):
    payload = {
        "messages": [
            {
                "channel": "sms",
                "recipients": [f"+91{phone_number}"],
                "content": f"Your OTP is {otp}. Do not share it with anyone.",
                "msg_type": "text",
                "data_coding": "text"
            }
        ],
        "message_globals": {
            "originator": D7_ORIGINATOR
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {D7_API_KEY}"
    }

    response = requests.post(D7_URL, json=payload, headers=headers)
    return response.status_code, response.text

# === Webhook Model ===

class DialogflowRequest(BaseModel):
    queryResult: dict

@app.post("/webhook")
async def webhook_handler(req: Request):
    body = await req.json()
    df = DialogflowRequest(**body)

    intent = df.queryResult.get("intent", {}).get("displayName")
    parameters = df.queryResult.get("parameters", {})

    phone = parameters.get("phone")
    user_otp = parameters.get("otp")

    if intent == "number":
        otp = generate_otp()
        otp_store[phone] = (otp, time.time() + 300)  # 5-minute expiry
        status, msg = send_otp_via_sms(phone, otp)

        if status == 200:
            return {"fulfillmentText": f"✅ OTP sent to {phone}. Please enter the OTP to verify."}
        else:
            return {"fulfillmentText": f"❌ Failed to send OTP. D7 API responded with {status}: {msg}"}

    elif intent == "otp":
        stored = otp_store.get(phone)
        if not stored:
            return {"fulfillmentText": "⚠️ No OTP was requested for this number. Please try again."}
        
        otp, expiry = stored
        if time.time() > expiry:
            return {"fulfillmentText": "⚠️ OTP expired. Please request a new one."}
        
        if user_otp == otp:
            del otp_store[phone]  # clear used OTP
            return {"fulfillmentText": "✅ OTP verified successfully!"}
        else:
            return {"fulfillmentText": "❌ Incorrect OTP. Please try again."}

    else:
        return {"fulfillmentText": "⚠️ Unrecognized intent."}
