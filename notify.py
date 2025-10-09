from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load env
load_dotenv("api.env")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_SMS_FROM = os.getenv("TWILIO_FROM")          # normal SMS number
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP") # whatsapp sender number

client = Client(TWILIO_SID, TWILIO_TOKEN)

def send_notification(to_number: str, body: str, channels=["sms", "whatsapp"]):
    results = {}
    
    if "sms" in channels:
        try:
            sms = client.messages.create(
                body=body,
                from_=TWILIO_SMS_FROM,
                to=to_number
            )
            results["sms"] = f"✅ SMS sent (SID: {sms.sid})"
        except Exception as e:
            results["sms"] = f"❌ SMS failed: {e}"
    
    if "whatsapp" in channels:
        try:
            whatsapp = client.messages.create(
                body=body,
                from_=f"whatsapp:{TWILIO_WHATSAPP_FROM}",
                to=f"whatsapp:{to_number}"
            )
            results["whatsapp"] = f"✅ WhatsApp sent (SID: {whatsapp.sid})"
        except Exception as e:
            results["whatsapp"] = f"❌ WhatsApp failed: {e}"
    
    return results

