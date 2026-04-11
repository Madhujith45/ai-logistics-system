from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value


SECRET_KEY = _required_env("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(username: str, password: str):
    """
    Authenticate any user (admin or customer) by username.
    Looks up the user in the database.
    """
    from app.database import get_user_by_username
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {"username": user["username"], "role": user["role"], "user_id": user["id"]}


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# -----------------------------------
# Multi-user Authentication
# -----------------------------------

def authenticate_customer(email: str, password: str):
    """Authenticate a customer user from the database."""
    from app.database import get_user_by_email
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def create_user_token(user: dict):
    """Create a JWT token for a customer user."""
    return create_access_token(
        data={
            "sub": user["email"],
            "user_id": user["id"],
            "name": user["name"],
            "role": user["role"],
        }
    )


def get_current_user(token: str):
    """Decode token and return user info. Works for both admin and customer."""
    payload = decode_token(token)
    if not payload:
        return None
    return payload

