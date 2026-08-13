from models import (User,Business, Branch, UserSession,
                    Service,BranchSlot,Appointment)
from messaging import (
    build_name_confirmation_buttons,
    build_main_menu,
    build_branch_list,
    build_service_list,
    build_date_list_page,
    build_session_list,
    build_slot_list_page,
    build_booking_confirmation_buttons
)
from datetime import time
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

def process_message(
    user_number,
    incoming_msg,
    db,
    webhook_data=None
):

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

        session.service_id = service.id
        date_rows = (
            db.query(BranchSlot.slot_date)
            .filter(
                BranchSlot.branch_id == session.branch_id,
                BranchSlot.status == "available"
            )
            .distinct()
            .order_by(BranchSlot.slot_date)
            .all()
        )
        available_dates = [
            row[0]
            for row in date_rows
        ]
        if not available_dates:

            return (
                "Sorry, no dates are available "
                "for this branch."
            )        

        session.step = "SELECT_DATE"

        db.commit()

        
        return build_date_list_page(
            available_dates
        )

    # ==========================================
    # SELECT DATE
    # ==========================================
    if (
        session.step == "SELECT_DATE"
    ):

        # -------------------------------
        # Pagination
        # -------------------------------
        if effective_input.startswith("date_page_"):

            page = int(
                effective_input.replace(
                    "date_page_",
                    ""
                )
            )

            date_rows = (
                db.query(BranchSlot.slot_date)
                .filter(
                    BranchSlot.branch_id == session.branch_id,
                    BranchSlot.status == "available"
                )
                .distinct()
                .order_by(BranchSlot.slot_date)
                .all()
            )

            available_dates = [
                row[0]
                for row in date_rows
            ]

            return build_date_list_page(
                available_dates,
                page
            )

        # -------------------------------
        # Date Selected
        # -------------------------------
        if effective_input.startswith("date_"):

            index = int(
                effective_input.replace(
                    "date_",
                    ""
                )
            )

            date_rows = (
                db.query(BranchSlot.slot_date)
                .filter(
                    BranchSlot.branch_id == session.branch_id,
                    BranchSlot.status == "available"
                )
                .distinct()
                .order_by(BranchSlot.slot_date)
                .all()
            )

            available_dates = [
                row[0]
                for row in date_rows
            ]

            if index >= len(available_dates):

                return "Invalid date selected."
            
            selected_date = available_dates[index]

            session.selected_date = selected_date

            available_slots = get_available_slots(
                db,
                session.branch_id,
                selected_date
            )

            available_sessions = []

            for booking_session in BOOKING_SESSIONS:

                session_slots = [
                    item
                    for item in available_slots
                    if (
                        booking_session["start"]
                        <= item["slot"].start_time
                        < booking_session["end"]
                    )
                ]

                if session_slots:
                    available_sessions.append(
                        booking_session
                    )            
            if not available_sessions:

                return (
                    "Sorry, no slots are available "
                    "for the selected date."
                )

            session.step = "SELECT_SESSION"

            db.commit()

            return build_session_list(
                available_sessions
            )         

    # ==========================================
    # SELECT SESSION
    # ==========================================
    if session.step == "SELECT_SESSION":

        if effective_input in [
            "morning",
            "afternoon",
            "evening"
        ]:

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

            available_slots = get_available_slots(
                db,
                session.branch_id,
                session.selected_date
            )

            # --------------------------------------
            # Keep only selected session slots
            # --------------------------------------
            available_slots = [
                item
                for item in available_slots
                if (
                    selected_session["start"]
                    <= item["slot"].start_time
                    < selected_session["end"]
                )
            ]

            # --------------------------------------
            # No slots in this session
            # --------------------------------------
            if not available_slots:

                return (
                    "Sorry, no slots are available "
                    "for this session."
                )

            session.selected_session = (
                selected_session["id"]
            )

            session.step = "SELECT_SLOT"

            db.commit()

            return build_slot_list_page(
                available_slots
            )


    # ==========================================
    # SELECT SLOT
    # ==========================================
    if (
        session.step == "SELECT_SLOT"
    ):

        # --------------------------------------
        # SLOT PAGINATION
        # --------------------------------------
        if effective_input.startswith("slot_page_"):

            page = int(
                effective_input.replace(
                    "slot_page_",
                    ""
                )
            )

            slots = get_available_slots(
                db,
                session.branch_id,
                session.selected_date
            )

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

            slots = [
                item
                for item in slots
                if (
                    selected_session["start"]
                    <= item["slot"].start_time
                    < selected_session["end"]
                )
            ]

            return build_slot_list_page(
                slots,
                page
            )            

        # --------------------------------------
        # SLOT SELECTED
        # --------------------------------------
        if effective_input.startswith("slot_"):

            slot_id = int(
                effective_input.replace(
                    "slot_",
                    ""
                )
            )
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

            slot = (
                db.query(BranchSlot)
                .filter(
                    BranchSlot.id == slot_id,
                    BranchSlot.branch_id == session.branch_id,
                    BranchSlot.status == "available",
                    BranchSlot.start_time >= selected_session["start"],
                    BranchSlot.start_time < selected_session["end"]
                )
                .first()
            )

            if not slot:

                return "Invalid slot selected."

            session.branch_slot_id = slot.id
            session.step = "CONFIRM_BOOKING"

            db.commit()

            branch = (
                db.query(Branch)
                .filter(
                    Branch.id == session.branch_id
                )
                .first()
            )

            service = (
                db.query(Service)
                .filter(
                    Service.id == session.service_id
                )
                .first()
            )

            return build_booking_confirmation_buttons(
                branch,
                service,
                slot
            )
        
    # ==========================================
    # CONFIRM BOOKING
    # ==========================================
    if (
        session.step == "CONFIRM_BOOKING"
    ):

        # --------------------------------------
        # RESET BOOKING
        # --------------------------------------
        if effective_input == "reset_data":

            session.branch_id = None
            session.service_id = None
            session.selected_date = None
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

            # Fetch Branch
            branch = (
                db.query(Branch)
                .filter(
                    Branch.id == session.branch_id
                )
                .first()
             )

            # Count existing bookings
            booked_count = (
                db.query(Appointment)
                .filter(
                    Appointment.branch_slot_id == session.branch_slot_id,
                    Appointment.status == "booked"
                )
                .count()
            )

            remaining = (
                branch.capacity - booked_count
            )

            if remaining <= 0:

                return (
                    "❌ Sorry, this slot is full.\n\n"
                    "Please select another slot."
                )

            appointment = Appointment(
                user_id=session.user_id,
                business_id=session.business_id,
                branch_id=session.branch_id,
                service_id=session.service_id,
                branch_slot_id=session.branch_slot_id,
                status="booked"
            )

            db.add(appointment)

            db.commit()

            session.branch_id = None
            session.service_id = None
            session.selected_date = None
            session.selected_session = None
            session.branch_slot_id = None
            session.step = "MAIN_MENU"

            db.commit()

            return {
                "message": (
                    "🎉 Your appointment has been booked successfully!"
                ),
                "buttons": [
                    {
                        "title": "🏠 Main Menu",
                        "payload": "menu"
                    }
                ]
            }
        
    
    # ==========================================
    # UNKNOWN MESSAGE
    # ==========================================
    return "Sorry, I didn't understand that."