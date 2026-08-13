from sqlalchemy import func
from models import (
    Branch,
    BranchSlot,
    Appointment
)
from datetime import time


BOOKING_SESSIONS = [
    {
        "id": "morning",
        "title": "🌅 Morning",
        "start": time(10, 30),
        "end": time(12, 30),
        "time": "10:30 AM - 12:30 PM"
    },
    {
        "id": "afternoon",
        "title": "☀️ Afternoon",
        "start": time(12, 30),
        "end": time(16, 30),
        "time": "12:30 PM - 04:30 PM"
    },
    {
        "id": "evening",
        "title": "🌆 Evening",
        "start": time(16, 30),
        "end": time(20, 30),
        "time": "04:30 PM - 08:30 PM"
    }
]
def extract_payload(webhook_data):
    if not webhook_data:
        return None

    metadata = webhook_data.get("metadata", {})

    return metadata.get("interactiveId")



PAGE_SIZE = 8


def paginate_items(
    items,
    page=0
):
    start = page * PAGE_SIZE

    end = start + PAGE_SIZE

    return items[start:end]


def has_next_page(
    items,
    page=0
):
    return (
        (page + 1) * PAGE_SIZE
    ) < len(items)


def has_previous_page(
    page=0
):
    return page > 0

def get_available_slots(
    db,
    branch_id,
    slot_date
):

    branch = (
        db.query(Branch)
        .filter(
            Branch.id == branch_id
        )
        .first()
    )

    if not branch:
        return []

    results = (
        db.query(
            BranchSlot,
            func.count(
                Appointment.id
            ).label(
                "booked_count"
            )
        )
        .outerjoin(
            Appointment,
            (
                Appointment.branch_slot_id
                == BranchSlot.id
            )
            &
            (
                Appointment.status == "booked"
            )
        )
        .filter(
            BranchSlot.branch_id == branch_id,
            BranchSlot.slot_date == slot_date,
            BranchSlot.status == "available"
        )
        .group_by(
            BranchSlot.id,
            BranchSlot.branch_id,
            BranchSlot.slot_date,
            BranchSlot.start_time,
            BranchSlot.end_time,
            BranchSlot.status
        )
        .order_by(
            BranchSlot.start_time
        )
        .all()
    )

    available_slots = []

    for slot, booked_count in results:

        remaining = (
            branch.capacity
            - booked_count
        )

        if remaining <= 0:
            continue

        available_slots.append(
            {
                "slot": slot,
                "remaining": remaining
            }
        )

    return available_slots