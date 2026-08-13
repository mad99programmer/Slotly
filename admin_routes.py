# ==========================================================
# admin_routes.py
# ==========================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from database import SessionLocal
from models import (
    User,
    Branch,
    Service,
    BranchSlot,
    Appointment
)
from security import get_current_admin


router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


# ==========================================================
# DATABASE SESSION
# ==========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================================
# ALL APPOINTMENTS
# ==========================================================

@router.get("/appointments")
def get_appointments(
    status: str = None,
    branch_id: int = None,
    service_id: int = None,
    from_date: date = None,
    to_date: date = None,

    current_admin=Depends(
        get_current_admin
    ),

    db: Session = Depends(get_db)
):

    query = (
        db.query(Appointment)
        .join(
            BranchSlot,
            Appointment.branch_slot_id
            == BranchSlot.id
        )
        .filter(
            Appointment.status != "deleted"
        )
    )

    # --------------------------------------
    # STATUS FILTER
    # --------------------------------------

    if status:

        query = query.filter(
            Appointment.status == status
        )

    # --------------------------------------
    # BRANCH FILTER
    # --------------------------------------

    if branch_id:

        query = query.filter(
            Appointment.branch_id == branch_id
        )

    # --------------------------------------
    # SERVICE FILTER
    # --------------------------------------

    if service_id:

        query = query.filter(
            Appointment.service_id == service_id
        )

    # --------------------------------------
    # FROM DATE
    # --------------------------------------

    if from_date:

        query = query.filter(
            BranchSlot.slot_date >= from_date
        )

    # --------------------------------------
    # TO DATE
    # --------------------------------------

    if to_date:

        query = query.filter(
            BranchSlot.slot_date <= to_date
        )

    # --------------------------------------
    # ORDER
    # --------------------------------------

    appointments = (
        query
        .order_by(
            BranchSlot.slot_date,
            BranchSlot.start_time
        )
        .all()
    )

    result = []

    # ======================================
    # BUILD RESPONSE
    # ======================================

    for appointment in appointments:

        # ----------------------------------
        # Customer
        # ----------------------------------

        user = (
            db.query(User)
            .filter(
                User.id == appointment.user_id
            )
            .first()
        )

        # ----------------------------------
        # Branch
        # ----------------------------------

        branch = (
            db.query(Branch)
            .filter(
                Branch.id == appointment.branch_id
            )
            .first()
        )

        # ----------------------------------
        # Service
        # ----------------------------------

        service = (
            db.query(Service)
            .filter(
                Service.id == appointment.service_id
            )
            .first()
        )

        # ----------------------------------
        # Slot
        # ----------------------------------

        slot = (
            db.query(BranchSlot)
            .filter(
                BranchSlot.id
                == appointment.branch_slot_id
            )
            .first()
        )

        result.append(
            {
                "id": appointment.id,

                "customer_name": (
                    user.name
                    if user
                    else "Unknown"
                ),

                "customer_phone": (
                    user.phone_number
                    if user
                    else ""
                ),

                "branch_name": (
                    branch.name
                    if branch
                    else "Unknown"
                ),

                "service_name": (
                    service.name
                    if service
                    else "Unknown"
                ),

                "date": (
                    str(slot.slot_date)
                    if slot
                    else ""
                ),

                "time": (
                    slot.start_time.strftime(
                        "%I:%M %p"
                    )
                    if slot
                    else ""
                ),

                "status": appointment.status
            }
        )

    return result