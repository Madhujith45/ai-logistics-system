from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "supersecretkey"  # change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Hardcoded admin for demonstration
ADMIN_USER = {
    "username": "admin",
    "password_hash": "$2b$12$aVncWNccbvHaE6yAXR166.P.I4DfGtXXx7DKKtH5TON0yNSABRcoy",
    "role": "admin"
}

def authenticate_user(username, password):
    if username == ADMIN_USER["username"] and verify_password(password, ADMIN_USER["password_hash"]):
        return ADMIN_USER
    return None

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
# Multi-user Authentication (Appended)
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
