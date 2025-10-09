import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image
import io
import math
import imagehash
from openai import OpenAI
from dotenv import load_dotenv
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from twilio.rest import Client as TwilioClient
import ast
import re

load_dotenv("api.env")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_FROM = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = OpenAI(api_key=OPENAI_KEY)
_twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

# ---------- Notifications ----------
def send_notification(to_number: str, body: str, channels=["sms","whatsapp","call"]):
    results = {}

    # --- SMS ---
    if "sms" in channels:
        try:
            print(f"Trying to send SMS to {to_number} from {TWILIO_SMS_FROM}")
            sms = _twilio_client.messages.create(
                body=body,
                from_=TWILIO_SMS_FROM,
                to=to_number
            )
            results["sms"] = f"✅ SMS sent (SID: {sms.sid})"
            print(f"SMS sent successfully! SID: {sms.sid}")
        except Exception as e:
            results["sms"] = f"❌ SMS failed: {e}"
            print(f"SMS failed: {e}")

    # --- WhatsApp ---
    if "whatsapp" in channels:
        try:
            print(f"Trying to send WhatsApp to {to_number} from {TWILIO_WHATSAPP_FROM}")
            whatsapp = _twilio_client.messages.create(
                body=body,
                from_=f"whatsapp:{TWILIO_WHATSAPP_FROM}",
                to=f"whatsapp:{to_number}"
            )
            results["whatsapp"] = f"✅ WhatsApp sent (SID: {whatsapp.sid})"
            print(f"WhatsApp sent successfully! SID: {whatsapp.sid}")
        except Exception as e:
            results["whatsapp"] = f"❌ WhatsApp failed: {e}"
            print(f"WhatsApp failed: {e}")

    # --- Voice Call ---
    if "call" in channels:
        try:
            print(f"Trying to make a call to {to_number} from {TWILIO_SMS_FROM}")
            call = _twilio_client.calls.create(
                twiml=f'<Response><Say voice="alice">{body}</Say></Response>',
                from_=TWILIO_SMS_FROM,
                to=to_number
            )
            results["call"] = f"✅ Call initiated (SID: {call.sid})"
            print(f"Call initiated successfully! SID: {call.sid}")
        except Exception as e:
            results["call"] = f"❌ Call failed: {e}"
            print(f"Call failed: {e}")

    return results

# ---------- Utils ----------
def compute_image_phash(img: Image.Image) -> str:
    return str(imagehash.phash(img))

def get_text_embedding(text: str) -> list:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp.data[0].embedding

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(y*y for y in b))
    if norm_a==0 or norm_b==0: return 0.0
    return dot / (norm_a*norm_b)

def phash_hamming(ph1: str, ph2: str) -> int:
    return bin(int(ph1, 16) ^ int(ph2, 16)).count('1')

# ---------- Database ----------
DB_PATH = "lostfound.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        title TEXT,
        description TEXT,
        owner_contact TEXT,
        image_phash TEXT,
        embedding_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def insert_item(item: Dict[str, Any]) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO items 
        (type, title, description, owner_contact, image_phash, embedding_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (item["type"], item["title"], item["description"],
         item.get("owner_contact"), item.get("image_phash"),
         json.dumps(item.get("embedding", [])), datetime.utcnow().isoformat()))
    conn.commit()
    item_id = c.lastrowid
    conn.close()
    return item_id

def fetch_all_items() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, type, title, description, owner_contact, image_phash, embedding_json, created_at FROM items")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "type": r[1],
            "title": r[2],
            "description": r[3],
            "owner_contact": r[4],
            "image_phash": r[5],
            "embedding": json.loads(r[6]) if r[6] else [],
            "created_at": r[7]
        } for r in rows
    ]

# ---------- AI Agents ----------
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    model_config_dict=ChatGPTConfig(temperature=0).as_dict(),
)

embed_agent = ChatAgent(
    system_message="You are EmbedAgent. Return a JSON array of floats ONLY for embedding, no explanation.",
    model=model
)

matcher_agent = ChatAgent(
    system_message="""You are MatcherAgent. Return JSON array of matching items with fields:
id, title, description, score, reasons, owner_contact. NO extra text.""",
    model=model
)

privacy_agent = ChatAgent(
    system_message="You are PrivacyAgent. Take a contact string and return an anonymized version ONLY.",
    model=model
)

notifier_agent = ChatAgent(
    system_message="You are NotifierAgent. Send SMS, WhatsApp & Calls via Twilio. Return JSON with success/failure info ONLY.",
    model=model
)

# ---------- Coordinator ----------
class Coordinator:
    def __init__(self):
        init_db()

    def _safe_parse(self, text: str):
        try:
            return json.loads(text)
        except:
            try:
                return ast.literal_eval(text)
            except:
                m = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(1))
                    except:
                        try:
                            return ast.literal_eval(m.group(1))
                        except:
                            return []
                return []

    def run_pipeline(self, image_bytes: bytes, title: str, description: str, item_type: str, contact: str):
        try:
            
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            phash = str(imagehash.phash(img))
            print(f"[DEBUG] Computed PHASH: {phash}")

           
            emb_resp = embed_agent.step(f"Generate embedding for title: {title}, description: {description}")
            embedding = self._safe_parse(emb_resp.msg.content)

            
            item_id = insert_item({
                "type": item_type,
                "title": title,
                "description": description,
                "owner_contact": contact,
                "image_phash": phash,
                "embedding": embedding
            })

            if contact and item_type.lower() == "lost":
                friendly_msg = (
                    f"Sorry to hear that 😔, your item '{title}' has been safely recorded. "
                    "I will notify you immediately if a match is found! 📦"
                )
                send_notification(contact, friendly_msg, channels=["sms","whatsapp","call"])

            if item_type.lower() == "found":
                all_lost_items = [item for item in fetch_all_items() if item['type'].lower() == 'lost']
                for lost_item in all_lost_items:
                    phash_diff = phash_hamming(phash, lost_item['image_phash'])
                    sim = cosine_similarity(embedding, lost_item['embedding'])
                    print(f"[DEBUG] Comparing with lost item {lost_item['title']} | diff={phash_diff}, sim={sim}")

                    if phash_diff < 20 or sim > 0.6:
                        print(f"[MATCH FOUND] Lost item {lost_item['title']} → diff={phash_diff}, sim={sim}")
                        notify_msg = (
                            f"🎉 Good news! Your lost item '{lost_item['title']}' might have been found by someone. "
                            f"Contact info of finder: {contact}"
                        )
                        send_notification(lost_item['owner_contact'], notify_msg, channels=["sms","whatsapp","call"])


            match_resp = matcher_agent.step(f"Find matches for type {item_type}, PHASH {phash}, embedding {embedding}")
            matches = self._safe_parse(match_resp.msg.content)

            results = []
            for m in matches[:3]:
                masked_contact_resp = privacy_agent.step(f"Anonymize contact: {m.get('owner_contact','')}")
                masked = masked_contact_resp.msg.content.strip()
                notif_status = {}
                if m.get("owner_contact"):
                    notif_status = send_notification(
                        m['owner_contact'],
                        f"Possible match for {title}. Contact of reporter: {contact}",
                        channels=["sms","whatsapp","call"]
                    )
                results.append({"match": m, "masked_contact": masked, "notif_status": notif_status})

            return {"item_id": item_id, "matches": results}

        except Exception as e:
            return {"error": f"Pipeline failed: {e}"}

coordinator = Coordinator()
