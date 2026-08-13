import requests

r = requests.post(
    "https://clinic-booking-chatbot.onrender.com/webhook/zernio",
    json={
        "event": "message.received",
        "message": {
            "text": "hi",
            "conversationId": "6a1ddd6f9956549faece8ae0",
            "sender": {
                "phoneNumber": "+919833851621"
            }
        },
        "account": {
            "id": "6a180a034c7f364ffded3c9c"
        }
    }
)
print(r.status_code, r.text)