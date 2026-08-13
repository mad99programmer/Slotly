from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from models import Admin
from database import SessionLocal


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)



SECRET_KEY = "30543bd93ab0934a339278d8f7f5b7db0005e21b41378f00e43b096d1dd0905b"
ALGORITHM = "HS256"



pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )

def create_access_token(data: dict):

    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(hours=24)

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_token(token: str):
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )


def get_current_admin(
    token: str = Depends(oauth2_scheme)
):

    try:
        payload = verify_token(token)

        admin_id = payload.get("admin_id")

        if not admin_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        db = SessionLocal()

        admin = db.query(Admin).filter(
            Admin.id == admin_id
        ).first()

        db.close()

        if not admin:
            raise HTTPException(
                status_code=401,
                detail="Admin not found"
            )

        return admin

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )