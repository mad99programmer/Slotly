import os
from twilio.rest import Client
from dotenv import load_dotenv
 
load_dotenv()
TEST_MODE=False
# =========================
# Business config CONFIG
# =========================
DEFAULT_BUSINESS_ID = int(os.getenv("BUSINESS_ID", "1"))
# =========================
# ZERNIO CONFIG
# =========================
ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY")


# =========================
# ZERNIO ACCOUNT_ID (change karna padega when we purchase a number)
# =========================

ACCOUNT_ID=os.getenv("ACCOUNT_ID")
