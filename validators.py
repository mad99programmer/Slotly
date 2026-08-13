import re


# =========================
# NAME VALIDATION
# =========================
def is_valid_name(name: str) -> bool:

    name = name.strip()

    if len(name) < 2 or len(name) > 60:
        return False

    if not re.match(r"^[A-Za-z\s.\-']+$", name):
        return False

    return True


# =========================
# EMAIL VALIDATION
# =========================
def is_valid_email(email: str) -> bool:

    return bool(
        re.match(
            r"^[\w\.-]+@[\w\.-]+\.\w{2,}$",
            email.strip()
        )
    )

# =========================
# AGE VALIDATION
# =========================
def is_valid_age(age_str: str) -> bool:
 
    if not age_str.strip().isdigit():
        return False
 
    age = int(age_str.strip())
 
    return 1 <= age <= 120