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

    # ======================================================
    # BASE QUERY
    # ======================================================

    query = (
        db.query(
            Appointment,
            User,
            Branch,
            Service
        )
        .join(
            User,
            User.id == Appointment.user_id
        )
        .join(
            Branch,
            Branch.id == Appointment.branch_id
        )
        .join(
            Service,
            Service.id == Appointment.service_id
        )
        .filter(
            Appointment.status != "deleted"
        )
    )


    # ======================================================
    # STATUS FILTER
    # ======================================================

    if status:

        query = query.filter(
            Appointment.status == status
        )


    # ======================================================
    # BRANCH FILTER
    # ======================================================

    if branch_id:

        query = query.filter(
            Appointment.branch_id == branch_id
        )


    # ======================================================
    # SERVICE FILTER
    # ======================================================

    if service_id:

        query = query.filter(
            Appointment.service_id == service_id
        )


    # ======================================================
    # FROM DATE FILTER
    # ======================================================

    if from_date:

        query = query.filter(
            Appointment.appointment_date >= from_date
        )


    # ======================================================
    # TO DATE FILTER
    # ======================================================

    if to_date:

        query = query.filter(
            Appointment.appointment_date <= to_date
        )


    # ======================================================
    # ORDER
    # ======================================================

    appointments = (
        query
        .order_by(
            Appointment.appointment_date,
            Appointment.start_time
        )
        .all()
    )


    # ======================================================
    # BUILD RESPONSE
    # ======================================================

    result = []

    for appointment, user, branch, service in appointments:

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
                    str(
                        appointment.appointment_date
                    )
                ),

                "time": (
                    f"{appointment.start_time.strftime('%I:%M %p')}"
                    f" - "
                    f"{appointment.end_time.strftime('%I:%M %p')}"
                ),

                "status": appointment.status
            }
        )


    # ======================================================
    # RETURN
    # ======================================================

    return result