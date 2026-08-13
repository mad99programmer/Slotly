# branch_slot_generator.py

from datetime import datetime, timedelta, date

from database import SessionLocal

from models import (
    Branch,
    BranchWorkingHours,
    BranchSlot
)

# ==========================================================
# DATABASE SESSION
# ==========================================================
db = SessionLocal()


# ==========================================================
# GENERATE BRANCH SLOTS
# ==========================================================
def generate_branch_slots(days=7):

    today = date.today()

    for day_offset in range(days):

        current_date = today + timedelta(days=day_offset)

        current_weekday = current_date.strftime("%A")

        print(f"\nGenerating slots for {current_date} ({current_weekday})")

        # --------------------------------------------------
        # Fetch active branches working on current weekday
        # --------------------------------------------------
        working_hours = (
            db.query(
                BranchWorkingHours,
                Branch
            )
            .join(
                Branch,
                Branch.id == BranchWorkingHours.branch_id
            )
            .filter(
                BranchWorkingHours.weekday == current_weekday,
                BranchWorkingHours.is_active == True,
                Branch.is_active == True
            )
            .all()
        )

        for working_hour, branch in working_hours:

            print(f"  Branch : {branch.name}")

            slot_duration = branch.slot_duration_minutes

            start_datetime = datetime.combine(
                current_date,
                working_hour.start_time
            )

            end_datetime = datetime.combine(
                current_date,
                working_hour.end_time
            )

            current_slot = start_datetime

            while current_slot < end_datetime:

                next_slot = current_slot + timedelta(
                    minutes=slot_duration
                )

                if next_slot > end_datetime:
                    break

                # ------------------------------------------
                # Avoid duplicate slots
                # ------------------------------------------
                existing = (
                    db.query(BranchSlot)
                    .filter(
                        BranchSlot.branch_id == branch.id,
                        BranchSlot.slot_date == current_date,
                        BranchSlot.start_time == current_slot.time()
                    )
                    .first()
                )

                if not existing:

                    db.add(
                        BranchSlot(
                            branch_id=branch.id,
                            slot_date=current_date,
                            start_time=current_slot.time(),
                            end_time=next_slot.time(),
                            status="available"
                        )
                    )

                current_slot = next_slot

    db.commit()

    total_slots = db.query(BranchSlot).count()

    print("\n========================================")
    print("Branch slot generation completed.")
    print(f"Total Slots : {total_slots}")
    print("========================================")


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":

    generate_branch_slots(days=7)