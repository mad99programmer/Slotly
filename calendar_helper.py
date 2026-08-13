from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import uuid4

from icalendar import Calendar, Event, Alarm


def generate_appointment_ics(
    doctor_name,
    appointment_date,
    start_time,
):
    ist = ZoneInfo("Asia/Kolkata")

    start_datetime = datetime.combine(
        appointment_date,
        start_time,
        tzinfo=ist
    )

    cal = Calendar()

    cal.add(
        "prodid",
        "-//Clinic Appointment//EN"
    )

    cal.add(
        "version",
        "2.0"
    )

    event = Event()

    event.add(
        "uid",
        str(uuid4())
    )

    event.add(
        "dtstamp",
        datetime.now(ist)
    )

    event.add(
        "summary",
        f"Appointment with Dr. {doctor_name}"
    )

    event.add(
        "dtstart",
        start_datetime
    )
    event.add(
        "dtend",
        start_datetime + timedelta(minutes=30)
    )
    alarm = Alarm()

    alarm.add(
        "action",
        "DISPLAY"
    )

    alarm.add(
        "description",
        "Appointment Reminder"
    )

    alarm.add(
        "trigger",
        timedelta(hours=-1)
    )

    event.add_component(
        alarm
    )

    cal.add_component(
        event
    )

    filename = (
        f"appointment_{uuid4().hex}.ics"
    )

    with open(
        filename,
        "wb"
    ) as file:

        file.write(
            cal.to_ical()
        )

    return filename


from datetime import date, time

generate_appointment_ics(
    doctor_name="Pranam",
    appointment_date=date(2026, 6, 30),
    start_time=time(10, 0),
)