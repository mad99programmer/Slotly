from fastapi import FastAPI, Form, Depends, Request
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base
from handlers import process_message
from messaging import send_reply
from fastapi.staticfiles import StaticFiles
from admin_routes import router as admin_router
from auth_routes import router as auth_router
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.responses import FileResponse
print("Server datetime :", datetime.now())
print("UTC datetime    :", datetime.utcnow())
print("IST datetime    :", datetime.now(ZoneInfo("Asia/Kolkata")))



# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(bind=engine)





#handling double message from zernio 
from collections import OrderedDict
import time

_processed_messages = OrderedDict()
_DEDUPE_TTL_SECONDS = 300  # 5 min

def is_duplicate(message_id: str) -> bool:
    now = time.time()
    expired = [mid for mid, ts in _processed_messages.items() if now - ts > _DEDUPE_TTL_SECONDS]
    for mid in expired:
        _processed_messages.pop(mid, None)
    if message_id in _processed_messages:
        return True
    _processed_messages[message_id] = now
    return False


#temporary admin creation


from models import Admin
from security import hash_password

db = SessionLocal()

try:
    admin = db.query(Admin).filter(
        Admin.username == "admin"
    ).first()

    if not admin:
        admin = Admin(
            username="admin",
            password_hash=hash_password("Admin@123")
        )

        db.add(admin)
        db.commit()

finally:
    db.close()

app = FastAPI()
# ==========================================================
# ADMIN FRONTEND PAGES
# ==========================================================

@app.get("/admin/login/")
async def admin_login_page():
    return FileResponse("admin/login.html")


@app.get("/admin/dashboard/")
async def admin_dashboard_page():
    return FileResponse("admin/dashboard.html")


@app.get("/admin/appointments/")
async def admin_appointments_page():
    return FileResponse("admin/appointments.html")
app.include_router(admin_router)
app.include_router(auth_router)
app.mount("/admin", StaticFiles(directory="admin", html=True), name="admin")
# =========================
# DATABASE SESSION
# =========================
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
async def health_check():

    return {
        "status": "Slotly says,'I am alive'"
    }

# =========================
# Zernio WEBHOOK
# =========================
@app.post("/webhook/zernio")
async def webhook_zernio(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    print("RAW PAYLOAD:")
    print(
        json.dumps(
            payload,
            indent=4,
            ensure_ascii=False
        )
    )

    if payload.get("event") == "message.received":
        message = payload.get("message", {})
        account = payload.get("account", {})
        message_id = message.get("id")
        #if message_id and is_duplicate(message_id):
        #    return {"status": "duplicate, skipped"}

        user_number = message.get("sender", {}).get("phoneNumber")
        incoming_msg = message.get("text", "").strip()
        conversation_id = message.get("conversationId")
        account_id = account.get("id")

        reply = process_message(user_number, incoming_msg, db,webhook_data=payload)
        send_reply(conversation_id, account_id, reply)

    return {"status": "ok"}

    


    return {"status": "ok"}


'''
# =========================
# LOCAL TEST ENDPOINT
# =========================
@app.get("/test")
async def test_chat(
    msg: str,
    user: str = "9999999999",
    db: Session = Depends(get_db)
):

    reply = process_message(
        user,
        msg,
        db
    )

    return {
        "user_message": msg,
        "bot_reply": reply
    }

@app.get("/run-slot-generator")
def run_slot_generator():
    from slot_generator import generate_slots_for_next_7_days
    generate_slots_for_next_7_days()
    return {"status": "slots generated"}

'''

