import time
import logging


from models import (
    User,
    Business,
    Branch,
    BranchWorkingHours,
    UserSession,
    Service,
    BranchSlot,
    Appointment
)


from messaging import (
    build_name_confirmation_buttons,
    build_main_menu,
    build_branch_list,
    build_service_list,
    build_session_list,
    build_booking_confirmation_buttons,
    build_dynamic_slot_list,
    build_dynamic_slot_list_page,
)
    
from datetime import datetime, date, time, timedelta
from helpers import (
    extract_payload,
    paginate_items,
    has_next_page,
    has_previous_page,
    get_available_slots,
    BOOKING_SESSIONS
)
import re
import json
from config import DEFAULT_BUSINESS_ID
MENU_COMMANDS = [
    "hi",
    "hello",
    "hey",
    "hie",
    "menu",
    "reset"
]
logger = logging.getLogger("slotly")


def process_message(
    user_number,
    incoming_msg,
    db,
    webhook_data=None
):
    handler_start = time.perf_counter()
    normalized_msg = incoming_msg.lower().strip()

    interactive_payload = extract_payload(webhook_data)
    print(
        "INTERACTIVE PAYLOAD:",
        interactive_payload
    )
    effective_input = interactive_payload or normalized_msg

    # ==========================================
    # GET / CREATE SESSION
    # ==========================================
    session = (
        db.query(UserSession)
        .filter(
            UserSession.phone_number == user_number
        )
        .first()
    )

    if not session:

        session = UserSession(
            phone_number=user_number,
            step="IDLE"
        )

        db.add(session)
        db.commit()
        db.refresh(session)

    # ==========================================
    # HOME / RESET
    # ==========================================
    if effective_input in MENU_COMMANDS:

        business = (
            db.query(Business)
            .filter(
                Business.id == DEFAULT_BUSINESS_ID,
                Business.is_active == True
            )
            .first()
        )

        if not business:

            return "Business not found."
        
        # Reset current booking
        session.branch_id = None
        session.service_id = None
        session.selected_date = None
        session.branch_slot_id = None
        session.business_id = business.id

        user = (
            db.query(User)
            .filter(
                User.phone_number == user_number,
                User.business_id == business.id,
                User.is_active == True
            )
            .first()
        )

        # ======================================
        # EXISTING USER
        # ======================================
        if user:

            session.user_id = user.id
            session.step = "MAIN_MENU"

            db.commit()

            return build_main_menu(user.name)
        # ======================================
        # NEW USER
        # ======================================
        session.user_id = None
        session.step = "ASK_NAME"
        session.temp_name = None

        db.commit()

        return (
            "👋 Welcome to Hair Destination Studio!\n\n"
            "Before we begin,\n"
            "May I know your name?"
        )


    # ==========================================
    # ASK NAME
    # ==========================================
    if session.step == "ASK_NAME":

        name = " ".join(incoming_msg.strip().split())

        # Length validation
        if len(name) < 2 or len(name) > 50:

            return (
                "Please enter a valid name."
            )

        # Allow:
        # - Letters
        # - Spaces
        # - Apostrophe (')
        # - Hyphen (-)
        #
        # Examples:
        # Mitul
        # Mitul Shelatkar
        # Anne-Marie
        # D'Souza
        if not re.fullmatch(
            r"[A-Za-z]+(?:[ '-][A-Za-z]+)*",
            name
        ):

            return (
                "Please enter a valid name.\n\n"
                "Example: Mitul Shelatkar"
            )

        session.temp_name = name
        session.step = "CONFIRM_NAME"

        db.commit()

        return build_name_confirmation_buttons(
            session.temp_name
        )

    # ==========================================
    # CONFIRM NAME
    # ==========================================
    if (
        session.step == "CONFIRM_NAME"
        and effective_input == "confirm_name"
    ):

        user = User(
            business_id=session.business_id,
            phone_number=user_number,
            name=session.temp_name,
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        session.user_id = user.id
        session.temp_name = None
        session.step = "MAIN_MENU"

        db.commit()

        return build_main_menu(user.name)
    # ==========================================
    # EDIT NAME
    # ==========================================
    if (
        session.step == "CONFIRM_NAME"
        and effective_input == "edit_name"
    ):

        session.temp_name = None
        session.step = "ASK_NAME"

        db.commit()

        return (
            "No problem 😊\n\n"
            "Please enter your name again."
        )
    #

    # ==========================================
    # MY APPOINTMENTS
    # ==========================================
    if (
        session.step == "MAIN_MENU"
        and effective_input == "menu_my_appointments"
    ):

        appointments_start = time.perf_counter()
        appointments = (
            db.query(
                Appointment,
                Branch,
                Service
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
                Appointment.user_id == session.user_id,
                Appointment.business_id == session.business_id,
                Appointment.status == "booked",
                Appointment.appointment_date >= date.today()
            )
            .order_by(
                Appointment.appointment_date,
                Appointment.start_time
            )
            .all()
        )
        appointments_time = (
            time.perf_counter() - appointments_start
        ) * 1000

        logger.info(
            "[DB] My appointments query | user_id=%s | time=%.2f ms | rows=%d",
            session.user_id,
            appointments_time,
            len(appointments)
        )

        # --------------------------------------
        # No appointments
        # --------------------------------------
        if not appointments:

            return {
                "message": (
                    "📋 You don't have any upcoming appointments."
                ),
                "buttons": [
                    {
                        "title": "🏠 Main Menu",
                        "payload": "menu"
                    }
                ]
            }

        # --------------------------------------
        # Build appointment details
        # --------------------------------------
        appointment_details = []

        for index, (
            appointment,
            branch,
            service
        ) in enumerate(
            appointments,
            start=1
        ):

            date_text = (
                appointment.appointment_date
                .strftime("%d %B %Y")
            )

            start_text = (
                appointment.start_time
                .strftime("%I:%M %p")
                .lstrip("0")
            )

            end_text = (
                appointment.end_time
                .strftime("%I:%M %p")
                .lstrip("0")
            )

            appointment_details.append(
                f"{index}️⃣ {service.name}\n"
                f"📍 {branch.name}\n"
                f"📅 {date_text}\n"
                f"🕒 {start_text} - {end_text}\n"
                f"🟢 Confirmed"
            )

        # --------------------------------------
        # Return appointments
        # --------------------------------------
        return {
            "message": (
                "📋 Your Appointments\n\n"
                + "\n\n".join(
                    appointment_details
                )
            ),
            "buttons": [
                {
                    "title": "🏠 Main Menu",
                    "payload": "menu"
                }
            ]
        }
    # ==========================================
    # BRANCHES & TIMINGS
    # ==========================================
    if (
        session.step == "MAIN_MENU"
        and effective_input == "menu_branches"
    ):

        branches = (
            db.query(Branch)
            .filter(
                Branch.business_id == session.business_id,
                Branch.is_active == True
            )
            .order_by(Branch.name)
            .all()
        )

        if not branches:
            return "❌ No branches are currently available."

        branch_details = []

        for branch in branches:

            branch_info = (
                f"📍 {branch.name}\n\n"
                f"🕒 Working Hours:\n"
                f"Monday - Saturday: 10:00 AM - 8:00 PM\n\n"
            )

            if branch.address:
                branch_info += (
                    f"📌 Address:\n"
                    f"{branch.address}\n\n"
                )

            if branch.maps_url:
                branch_info += (
                    f"🗺️ Google Maps:\n"
                    f"{branch.maps_url}\n\n"
                )

            branch_details.append(branch_info)

        return {
            "message": (
                "🏢 Our Branches & Timings\n\n"
                + "\n".join(branch_details)
            ),
            "buttons": [
                {
                    "title": "🏠 Main Menu",
                    "payload": "menu"
                }
            ]
        }


    # ==========================================
    # BOOK APPOINTMENT
    # ==========================================
    if (
        session.step == "MAIN_MENU"
        and effective_input == "menu_book"
    ):

        business = (
            db.query(Business)
            .filter(
                Business.id == session.business_id,
                Business.is_active == True
            )
            .first()
        )

        branches = (
            db.query(Branch)
            .filter(
                Branch.business_id == session.business_id,
                Branch.is_active == True
            )
            .order_by(Branch.name)
            .all()
        )

        session.step = "SELECT_BRANCH"
        session.branch_id = None
        session.service_id = None

        db.commit()

        return build_branch_list(
            business,
            branches
        )
    # ==========================================
    # SELECT BRANCH
    # ==========================================
    if (
        session.step == "SELECT_BRANCH"
        and effective_input.startswith("branch_")
    ):

        branch_id = int(
            effective_input.replace("branch_", "")
        )

        branch = (
            db.query(Branch)
            .filter(
                Branch.id == branch_id,
                Branch.business_id == session.business_id,
                Branch.is_active == True
            )
            .first()
        )

        if not branch:

            return "Invalid branch selected."

        session.branch_id = branch.id
        session.step = "SELECT_SERVICE"

        db.commit()
        services = (
            db.query(Service)
            .filter(
                Service.business_id == session.business_id,
                Service.is_active == True
            )
            .order_by(Service.name)
            .all()
        )

        return build_service_list(services)
    
    # ==========================================
    # SELECT SERVICE
    # ==========================================
    if (
        session.step == "SELECT_SERVICE"
        and effective_input.startswith("service_")
    ):

        service_id = int(
            effective_input.replace("service_", "")
        )

        service = (
            db.query(Service)
            .filter(
                Service.id == service_id,
                Service.business_id == session.business_id,
                Service.is_active == True
            )
            .first()
        )

        if not service:

            return "Invalid service selected."
        #
        session.service_id = service.id
        session.step = "SELECT_DATE"

        db.commit()

        return (
            "📅 Please enter your preferred appointment date.\n\n"
            "Format: DD/MM/YYYY\n"
            "Example: 25/08/2026"
        )     

    #
    # ==========================================
    # SELECT DATE
    # ==========================================
    if session.step == "SELECT_DATE":

        # -------------------------------
        # Parse Date
        # -------------------------------
        try:
            selected_date = datetime.strptime(
                effective_input.strip(),
                "%d/%m/%Y"
            ).date()

        except ValueError:

            return (
                "❌ Invalid date format.\n\n"
                "Please enter the date as DD/MM/YYYY.\n"
                "Example: 25/08/2026"
            )

        # -------------------------------
        # Prevent Past Dates
        # -------------------------------
        if selected_date < date.today():

            return (
                "❌ You cannot select a past date.\n\n"
                "Please enter a future date."
            )

        # -------------------------------
        # Check Branch
        # -------------------------------
        branch = (
            db.query(Branch)
            .filter(
                Branch.id == session.branch_id,
                Branch.is_active == True
            )
            .first()
        )

        if not branch:
            return "Branch not found."

        # -------------------------------
        # Check Working Hours
        # -------------------------------
        weekday = selected_date.strftime("%A")

        working_hours = (
            db.query(BranchWorkingHours)
            .filter(
                BranchWorkingHours.branch_id == session.branch_id,
                BranchWorkingHours.weekday == weekday,
                BranchWorkingHours.is_active == True
            )
            .first()
        )

        if not working_hours:

            return (
                f"❌ We are closed on {weekday}.\n\n"
                "Please select another date."
            )

        if (
            working_hours.start_time is None
            or working_hours.end_time is None
        ):

            return (
                "❌ Working hours are not configured "
                "for this day."
            )

        # -------------------------------
        # Save Selected Date
        # -------------------------------
        session.selected_date = selected_date

        # -------------------------------
        # Generate Dynamic Slots
        # -------------------------------
        slot_duration = branch.slot_duration_minutes

        current_datetime = datetime.combine(
            selected_date,
            working_hours.start_time
        )

        closing_datetime = datetime.combine(
            selected_date,
            working_hours.end_time
        )

        #available_slots = []
        # --------------------------------------
        # Fetch all booked slot counts ONCE
        # --------------------------------------
        slot_query_start = time.perf_counter()
        booked_rows = (
            db.query(
                Appointment.start_time
            )
            .filter(
                Appointment.branch_id == session.branch_id,
                Appointment.appointment_date == session.selected_date,
                Appointment.status == "booked"
            )
            .all()
        )
        slot_query_time = (
            time.perf_counter() - slot_query_start
        ) * 1000

        logger.info(
            "[DB] Slot availability query | branch=%s | date=%s | time=%.2f ms | rows=%d",
            session.branch_id,
            session.selected_date,
            slot_query_time,
            len(booked_rows)
        )
        booked_count_map = {}

        for row in booked_rows:
            booked_count_map[row[0]] = (
                booked_count_map.get(row[0], 0) + 1
            )


        available_slots = []

        while current_datetime < closing_datetime:

            slot_end_datetime = (
                current_datetime
                + timedelta(minutes=slot_duration)
            )

            if slot_end_datetime > closing_datetime:
                break

            slot_start = current_datetime.time()
            slot_end = slot_end_datetime.time()

            booked_count = booked_count_map.get(
                slot_start,
                0
            )

            if booked_count < branch.capacity:

                available_slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end
                })

            current_datetime = slot_end_datetime


        # -------------------------------
        # No Available Slots
        # -------------------------------
        if not available_slots:

            return (
                "❌ Sorry, no slots are available "
                "for the selected date."
            )

        # -------------------------------
        # Find Available Sessions
        # -------------------------------
        available_sessions = []

        for booking_session in BOOKING_SESSIONS:

            session_slots = [
                slot
                for slot in available_slots
                if (
                    booking_session["start"]
                    <= slot["start_time"]
                    < booking_session["end"]
                )
            ]

            if session_slots:

                available_sessions.append(
                    booking_session
                )

        # -------------------------------
        # No Sessions
        # -------------------------------
        if not available_sessions:

            return (
                "❌ Sorry, no slots are available "
                "for the selected date."
            )

        # -------------------------------
        # Move to Session Selection
        # -------------------------------
        session.step = "SELECT_SESSION"

        db.commit()

        return build_session_list(
            available_sessions
        )             
    #
    # ==========================================
    # SELECT SESSION
    # ==========================================
    if session.step == "SELECT_SESSION":

        # --------------------------------------
        # Validate session selection
        # --------------------------------------
        selected_session = next(
            (
                booking_session
                for booking_session in BOOKING_SESSIONS
                if booking_session["id"] == effective_input
            ),
            None
        )

        if not selected_session:

            return "Invalid session selected."

        # --------------------------------------
        # Get branch
        # --------------------------------------
        branch = (
            db.query(Branch)
            .filter(
                Branch.id == session.branch_id,
                Branch.is_active == True
            )
            .first()
        )

        if not branch:
            return "Branch not found."

        # --------------------------------------
        # Get working hours
        # --------------------------------------
        weekday = session.selected_date.strftime("%A")

        working_hours = (
            db.query(BranchWorkingHours)
            .filter(
                BranchWorkingHours.branch_id == session.branch_id,
                BranchWorkingHours.weekday == weekday,
                BranchWorkingHours.is_active == True
            )
            .first()
        )

        if not working_hours:
            return (
                f"❌ We are closed on {weekday}."
            )

        # --------------------------------------
        # Generate slots dynamically
        # --------------------------------------
        slot_duration = branch.slot_duration_minutes
        current_datetime = datetime.combine(
            session.selected_date,
            working_hours.start_time
        )

        closing_datetime = datetime.combine(
            session.selected_date,
            working_hours.end_time
        )

        #available_slots = []
        # --------------------------------------
        # Fetch all booked slot counts ONCE
        # --------------------------------------
        slot_query_start = time.perf_counter()

        booked_rows = (
            db.query(
                Appointment.start_time
            )
            .filter(
                Appointment.branch_id == session.branch_id,
                Appointment.appointment_date == session.selected_date,
                Appointment.status == "booked"
            )
            .all()
        )
        slot_query_time = (
            time.perf_counter() - slot_query_start
        ) * 1000

        logger.info(
            "[DB] SELECT_SESSION booked slots | "
            "branch=%s | date=%s | time=%.2f ms | rows=%d",
            session.branch_id,
            session.selected_date,
            slot_query_time,
            len(booked_rows)
        )

        booked_count_map = {}

        for row in booked_rows:
            booked_count_map[row[0]] = (
                booked_count_map.get(row[0], 0) + 1
            )


        available_slots = []

        while current_datetime < closing_datetime:

            slot_end_datetime = (
                current_datetime
                + timedelta(minutes=slot_duration)
            )

            if slot_end_datetime > closing_datetime:
                break

            slot_start = current_datetime.time()
            slot_end = slot_end_datetime.time()

            booked_count = booked_count_map.get(
                slot_start,
                0
            )

            if booked_count < branch.capacity:

                available_slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end
                })

            current_datetime = slot_end_datetime
        
        # --------------------------------------
        # Filter slots for selected session
        # --------------------------------------
        session_slots = [
            slot
            for slot in available_slots
            if (
                selected_session["start"]
                <= slot["start_time"]
                < selected_session["end"]
            )
        ]

        # --------------------------------------
        # No slots in this session
        # --------------------------------------
        if not session_slots:

            return (
                f"❌ No slots are available in the "
                f"{selected_session['title']} session.\n\n"
                "Please select another session."
            )

        # --------------------------------------
        # Save selected session
        # --------------------------------------
        session.selected_session = selected_session["id"]

        session.step = "SELECT_SLOT"

        db.commit()

        return build_dynamic_slot_list(
            session_slots
        )    

    #
    # ==========================================
    # SELECT SLOT
    # ==========================================
    if session.step == "SELECT_SLOT":

        # --------------------------------------
        # Get Branch
        # --------------------------------------
        branch = (
            db.query(Branch)
            .filter(
                Branch.id == session.branch_id,
                Branch.is_active == True
            )
            .first()
        )

        if not branch:
            return "Branch not found."

        # --------------------------------------
        # Get Selected Session
        # --------------------------------------
        selected_session = next(
            (
                booking_session
                for booking_session in BOOKING_SESSIONS
                if booking_session["id"] == session.selected_session
            ),
            None
        )

        if not selected_session:
            return "Invalid session."

        # --------------------------------------
        # Get Working Hours
        # --------------------------------------
        weekday = session.selected_date.strftime("%A")

        working_hours = (
            db.query(BranchWorkingHours)
            .filter(
                BranchWorkingHours.branch_id == session.branch_id,
                BranchWorkingHours.weekday == weekday,
                BranchWorkingHours.is_active == True
            )
            .first()
        )

        if not working_hours:
            return (
                f"❌ We are closed on {weekday}."
            )

        # --------------------------------------
        # Generate Dynamic Slots
        # --------------------------------------
        slot_duration = branch.slot_duration_minutes
        current_datetime = datetime.combine(
            session.selected_date,
            working_hours.start_time
        )

        closing_datetime = datetime.combine(
            session.selected_date,
            working_hours.end_time
        )

        #available_slots = []
        # --------------------------------------
        # Fetch all booked slot counts ONCE
        # --------------------------------------
        slot_query_start = time.perf_counter()
        booked_rows = (
            db.query(
                Appointment.start_time
            )
            .filter(
                Appointment.branch_id == session.branch_id,
                Appointment.appointment_date == session.selected_date,
                Appointment.status == "booked"
            )
            .all()
        )
        slot_query_time = (
            time.perf_counter() - slot_query_start
        ) * 1000

        logger.info(
            "[DB] SELECT_SLOT booked slots | "
            "branch=%s | date=%s | time=%.2f ms | rows=%d",
            session.branch_id,
            session.selected_date,
            slot_query_time,
            len(booked_rows)
        )

        booked_count_map = {}

        for row in booked_rows:
            booked_count_map[row[0]] = (
                booked_count_map.get(row[0], 0) + 1
            )


        available_slots = []

        while current_datetime < closing_datetime:

            slot_end_datetime = (
                current_datetime
                + timedelta(minutes=slot_duration)
            )

            if slot_end_datetime > closing_datetime:
                break

            slot_start = current_datetime.time()
            slot_end = slot_end_datetime.time()

            booked_count = booked_count_map.get(
                slot_start,
                0
            )

            if booked_count < branch.capacity:

                available_slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end
                })

            current_datetime = slot_end_datetime
        
        # --------------------------------------
        # Filter Selected Session
        # --------------------------------------
        session_slots = [
            slot
            for slot in available_slots
            if (
                selected_session["start"]
                <= slot["start_time"]
                < selected_session["end"]
            )
        ]

        if not session_slots:
            return (
                "❌ Sorry, this session no longer "
                "has any available slots."
            )

        # ======================================
        # SLOT PAGINATION
        # ======================================
        if effective_input.startswith("slot_page_"):

            page = int(
                effective_input.replace(
                    "slot_page_",
                    ""
                )
            )

            return build_dynamic_slot_list_page(
                session_slots,
                page
            )

        # ======================================
        # SLOT SELECTED
        # ======================================
        if effective_input.startswith("slot_"):

            index = int(
                effective_input.replace(
                    "slot_",
                    ""
                )
            )

            if index < 0 or index >= len(session_slots):
                return "Invalid slot selected."

            selected_slot = session_slots[index]

            # ----------------------------------
            # Save Selected Time
            # ----------------------------------
            session.selected_start_time = (
                selected_slot["start_time"]
            )

            session.selected_end_time = (
                selected_slot["end_time"]
            )

            session.step = "CONFIRM_BOOKING"

            db.commit()

            # ----------------------------------
            # Get Service
            # ----------------------------------
            service = (
                db.query(Service)
                .filter(
                    Service.id == session.service_id
                )
                .first()
            )

            if not service:
                return "Service not found."

            return build_booking_confirmation_buttons(
                branch,
                service,
                session.selected_date,
                session.selected_start_time,
                session.selected_end_time
            )
        return "Invalid slot selection."    
    #
        
    # ==========================================
    # CONFIRM BOOKING
    # ==========================================
    if session.step == "CONFIRM_BOOKING":

        # --------------------------------------
        # RESET BOOKING
        # --------------------------------------
        if effective_input == "reset_data":

            session.branch_id = None
            session.service_id = None
            session.selected_date = None
            session.selected_start_time = None
            session.selected_end_time = None
            session.selected_session = None
            session.branch_slot_id = None
            session.step = "MAIN_MENU"

            db.commit()

            user = (
                db.query(User)
                .filter(
                    User.id == session.user_id
                )
                .first()
            )

            return build_main_menu(
                user.name
            )

        # --------------------------------------
        # CONFIRM BOOKING
        # --------------------------------------
        if effective_input == "booking_confirm":

            # ----------------------------------
            # Fetch Branch
            # ----------------------------------
            branch = (
                db.query(Branch)
                .filter(
                    Branch.id == session.branch_id,
                    Branch.is_active == True
                )
                .first()
            )

            if not branch:
                return "❌ Branch not found."

            # ----------------------------------
            # Fetch Service
            # ----------------------------------
            service = (
                db.query(Service)
                .filter(
                    Service.id == session.service_id,
                    Service.is_active == True
                )
                .first()
            )

            if not service:
                return "❌ Service not found."

            # ----------------------------------
            # Validate Selected Date / Time
            # ----------------------------------
            if (
                not session.selected_date
                or not session.selected_start_time
                or not session.selected_end_time
            ):
                return (
                    "❌ Your booking session has expired.\n\n"
                    "Please start the booking again."
                )

            # ----------------------------------
            # FINAL CAPACITY CHECK
            # ----------------------------------
            booked_count = (
                db.query(Appointment)
                .filter(
                    Appointment.branch_id == session.branch_id,
                    Appointment.appointment_date == session.selected_date,
                    Appointment.start_time == session.selected_start_time,
                    Appointment.status == "booked"
                )
                .count()
            )

            # ----------------------------------
            # Slot Became Full
            # ----------------------------------
            if booked_count >= branch.capacity:

                return (
                    "❌ Sorry, this slot was just booked "
                    "by another customer.\n\n"
                    "Please select another slot."
                )

            # ----------------------------------
            # Create Appointment
            # ----------------------------------
            appointment = Appointment(
                user_id=session.user_id,
                business_id=session.business_id,
                branch_id=session.branch_id,
                service_id=session.service_id,
                appointment_date=session.selected_date,
                start_time=session.selected_start_time,
                end_time=session.selected_end_time,
                status="booked"
            )

            db.add(appointment)

            db.commit()

            # ----------------------------------
            # Store Details Before Reset
            # ----------------------------------
            appointment_date = session.selected_date
            start_time = session.selected_start_time
            end_time = session.selected_end_time

            branch_name = branch.name
            branch_address = branch.address
            maps_url = branch.maps_url

            service_name = service.name

            # ----------------------------------
            # Reset Booking Session
            # ----------------------------------
            session.branch_id = None
            session.service_id = None
            session.selected_date = None
            session.selected_start_time = None
            session.selected_end_time = None
            session.selected_session = None
            session.branch_slot_id = None
            session.step = "MAIN_MENU"

            db.commit()

            # ----------------------------------
            # Build Location Text
            # ----------------------------------
            location_text = ""

            if branch_address:
                location_text += (
                    f"📍 Address: {branch_address}\n"
                )

            if maps_url:
                location_text += (
                    f"🗺️ Google Maps: {maps_url}\n"
                )

            # ----------------------------------
            # Booking Confirmation
            # ----------------------------------
            return {
                "message": (
                    "🎉 Appointment Confirmed!\n\n"

                    f"📍 Branch: {branch_name}\n"
                    f"💇 Service: {service_name}\n"
                    f"📅 Date: "
                    f"{appointment_date.strftime('%d/%m/%Y')}\n"
                    f"⏰ Time: "
                    f"{start_time.strftime('%I:%M %p')} - "
                    f"{end_time.strftime('%I:%M %p')}\n\n"

                    f"{location_text}\n"

                    "Thank you for booking with "
                    "Hair Destination! 💙"
                ),

                "buttons": [
                    {
                        "title": "🏠 Main Menu",
                        "payload": "menu"
                    }
                ]
            }

        return "Invalid booking option."
        
    handler_time = (
        time.perf_counter() - handler_start
    ) * 1000

    logger.info(
        "[HANDLER] Completed | step=%s | time=%.2f ms",
        session.step,
        handler_time
    )
    # ==========================================
    # UNKNOWN MESSAGE
    # ==========================================
    return "Sorry, I didn't understand that."