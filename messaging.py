from config import TEST_MODE, ZERNIO_API_KEY
import requests
from helpers import (
    extract_payload,
    paginate_items,
    has_next_page,
    has_previous_page,
    get_available_slots
)
from datetime import date
import time
import requests




def build_main_menu(user_name):

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": (
                    f"👋 Welcome {user_name}!\n\n"
                    "How can we help you today?"
                )
            },
            "action": {
                "button": "Select Option",
                "sections": [
                    {
                        "title": "Main Menu",
                        "rows": [
                            {
                                "id": "menu_book",
                                "title": "📅 Book Appointment"
                            },
                            {
                                "id": "menu_my_appointments",
                                "title": "📋 My Appointments"
                            },
                            {
                                "id": "menu_cancel",
                                "title": "❌ Cancel Appointment"
                            },
                            {
                                "id": "menu_branches",
                                "title": "🕒 Branches & Timings"
                            }
                        ]
                    }
                ]
            }
        }
    }

# =========================
# SEND WHATSAPP MESSAGE using ZERNIO
# =========================
def send_reply(
    conversation_id: str,
    account_id: str,
    message
):
    if TEST_MODE:
        print("\nBOT REPLY:")
        print(message)
        return True

    # -------------------------
    # Build request body
    # -------------------------
    if isinstance(message, str):

        body = {
            "accountId": account_id,
            "message": message
        }

    else:

        body = {
            "accountId": account_id
        }

        if "message" in message:
            body["message"] = message["message"]

        if "buttons" in message:
            body["buttons"] = message["buttons"]

        if "interactive" in message:
            body["interactive"] = message["interactive"]

    print("=" * 80)
    print("OUTGOING BODY")
    print("=" * 80)
    print(body)

    url = (
        f"https://zernio.com/api/v1/inbox/conversations/"
        f"{conversation_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ZERNIO_API_KEY}",
        "Content-Type": "application/json"
    }

    max_retries = 3

    for attempt in range(max_retries):

        try:

            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )

            print(
                f"Attempt {attempt + 1} "
                f"Status : {response.status_code}"
            )

            print(response.text)

            # Success
            if response.status_code in [200, 201]:
                return True

            # Retry only for transient server errors
            if response.status_code in [500, 502, 503, 504]:

                if attempt < max_retries - 1:

                    wait = 2 ** attempt

                    print(
                        f"Transient error."
                        f" Retrying in {wait} seconds..."
                    )

                    time.sleep(wait)

                    continue

            # Client errors (400,401,403...)
            return False

        except requests.exceptions.Timeout:

            print("Request timed out.")

        except requests.exceptions.ConnectionError:

            print("Unable to connect to Zernio.")

        except requests.exceptions.RequestException as e:

            print(e)

        if attempt < max_retries - 1:

            wait = 2 ** attempt

            print(
                f"Retrying in {wait} seconds..."
            )

            time.sleep(wait)

    print("Failed to send message after all retries.")

    return False


def build_name_confirmation_buttons(name):

    return {
        "message": (
            "Please confirm your name.\n\n"
            f"👤 {name}"
        ),
        "buttons": [
            {
                "title": "✅ Confirm",
                "payload": "confirm_name"
            },
            {
                "title": "✏️ Edit",
                "payload": "edit_name"
            }
        ]
    }
def build_branch_list(
    business,
    branches
):

    rows = []

    for branch in branches:

        rows.append(
            {
                "id": f"branch_{branch.id}",
                "title": branch.name
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": (
                    f"👋 Welcome to {business.name}!\n\n"
                    "Please select your preferred location."
                )
            },
            "action": {
                "button": "Select Location",
                "sections": [
                    {
                        "title": "Our Locations",
                        "rows": rows
                    }
                ]
            }
        }
    }

def build_service_list(services):

    rows = []

    for service in services:

        rows.append(
            {
                "id": f"service_{service.id}",
                "title": service.name
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please select a service."
            },
            "action": {
                "button": "Select Service",
                "sections": [
                    {
                        "title": "Available Services",
                        "rows": rows
                    }
                ]
            }
        }
    }


# ==========================================================
# BUILD DATE LIST
# ==========================================================
def build_date_list_page(
    available_dates,
    page=0
):

    page_dates = paginate_items(
        available_dates,
        page
    )

    rows = []

    start_index = page * 8

    for index, slot_date in enumerate(page_dates):

        rows.append(
            {
                "id": f"date_{start_index + index}",
                "title": slot_date.strftime(
                    "%d %B %Y"
                ),
                "description": slot_date.strftime(
                    "%A"
                )
            }
        )

    if has_previous_page(page):

        rows.append(
            {
                "id": f"date_page_{page - 1}",
                "title": "⬅ Previous Dates"
            }
        )

    if has_next_page(
        available_dates,
        page
    ):

        rows.append(
            {
                "id": f"date_page_{page + 1}",
                "title": "➡ More Dates"
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "📅 Please select your preferred appointment date."
            },
            "action": {
                "button": "Select Date",
                "sections": [
                    {
                        "title": "Available Dates",
                        "rows": rows
                    }
                ]
            }
        }
    }

def build_session_list(sessions):

    rows = []

    for session in sessions:

        rows.append(
            {
                "id": session["id"],
                "title": session["title"],
                "description": session["time"]
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please select a time session:"
            },
            "action": {
                "button": "Select Session",
                "sections": [
                    {
                        "title": "Available Sessions",
                        "rows": rows
                    }
                ]
            }
        }
    }
def build_booking_confirmation_buttons(
    branch,
    service,
    slot
):

    return {
        "message": (
            "✨ Please review your appointment details.\n\n"

            f"📍 Branch : {branch.name}\n"
            f"✂ Service : {service.name}\n"
            f"📅 Date : {slot.slot_date.strftime('%d %B %Y')}\n"
            f"🕒 Time : {slot.start_time.strftime('%I:%M %p')}\n\n"

            "Would you like to confirm this booking?"
        ),
        "buttons": [
            {
                "title": "✅ Confirm",
                "payload": "booking_confirm"
            },
            {
                "title": "🔄 Start Over",
                "payload": "reset_data"
            }
        ]
    }
def build_slot_list_page(
    slots,
    page=0
):

    page_slots = paginate_items(
        slots,
        page
    )

    rows = []

    for item in page_slots:

        slot = item["slot"]

        remaining = item["remaining"]

        if remaining == 1:

            description = "🔴 Last spot"

        elif remaining <= 2:

            description = (
                f"🟡 {remaining} spots left"
            )

        else:

            description = (
                f"🟢 Available"
            )

        rows.append(
            {
                "id": f"slot_{slot.id}",
                "title": slot.start_time.strftime(
                    "%I:%M %p"
                ),
                "description": description
            }
        )

    if has_previous_page(page):

        rows.append(
            {
                "id": f"slot_page_{page - 1}",
                "title": "⬅ Previous Slots"
            }
        )

    if has_next_page(
        slots,
        page
    ):

        rows.append(
            {
                "id": f"slot_page_{page + 1}",
                "title": "➡ More Slots"
            }
        )

    return {
        "interactive": {
            "type": "list",
            "body": {
                "text": (
                    "🕒 Please select your preferred time slot."
                )
            },
            "action": {
                "button": "Select Slot",
                "sections": [
                    {
                        "title": "Available Slots",
                        "rows": rows
                    }
                ]
            }
        }
    }