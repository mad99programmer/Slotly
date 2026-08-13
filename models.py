from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Numeric,
    Time,
    UniqueConstraint,
    Date
)

from sqlalchemy.sql import func
from database import Base


# ==========================================================
# ADMIN
# ==========================================================
class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ==========================================================
# BUSINESS
# ==========================================================
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)

    phone = Column(String(20))

    email = Column(String(100))

    website = Column(String(255))

    description = Column(String(1000))

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# ==========================================================
# BRANCH
# ==========================================================
class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    address = Column(
        String(500)
    )

    phone = Column(
        String(20)
    )

    email = Column(
        String(100)
    )

    # Slot duration (in minutes)
    slot_duration_minutes = Column(
        Integer,
        nullable=False,
        default=30
    )

    capacity = Column(
        Integer,
        nullable=False,
        default=1
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# ==========================================================
# BRANCH WORKING HOURS
# ==========================================================
class BranchWorkingHours(Base):
    __tablename__ = "branch_working_hours"

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "weekday",
            name="uq_branch_weekday"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    branch_id = Column(
        Integer,
        ForeignKey("branches.id"),
        nullable=False
    )

    weekday = Column(
        String(10),
        nullable=False
    )

    start_time = Column(Time)

    end_time = Column(Time)

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

# ==========================================================
# BRANCH SLOT
# ==========================================================
class BranchSlot(Base):
    __tablename__ = "branch_slots"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    branch_id = Column(
        Integer,
        ForeignKey("branches.id"),
        nullable=False
    )

    slot_date = Column(
        Date,
        nullable=False
    )

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="available"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "slot_date",
            "start_time",
            name="uq_branch_slot"
        ),
    )
# ==========================================================
# SERVICE
# ==========================================================
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False
    )

    name = Column(String(100), nullable=False)

    description = Column(String(500))

    duration_minutes = Column(Integer)

    price = Column(Numeric(10, 2))

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ==========================================================
# USER
# ==========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False
    )

    phone_number = Column(
        String(20),
        unique=True,
        nullable=False
    )

    name = Column(
        String(100),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


# ==========================================================
# USER SESSION
# ==========================================================
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    phone_number = Column(
        String(20),
        unique=True,
        nullable=False
    )

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=True
    )

    branch_id = Column(
        Integer,
        ForeignKey("branches.id"),
        nullable=True
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=True
    )

    step = Column(
        String(50),
        nullable=False,
        default="IDLE"
    )

    temp_name = Column(
        String(100),
        nullable=True
    )
    selected_date = Column(Date, nullable=True)
    selected_session = Column(
        String(20),
        nullable=True
    )
    branch_slot_id = Column(
        Integer,
        ForeignKey("branch_slots.id"),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False
    )

    branch_id = Column(
        Integer,
        ForeignKey("branches.id"),
        nullable=False
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False
    )

    branch_slot_id = Column(
        Integer,
        ForeignKey("branch_slots.id"),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="booked"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )