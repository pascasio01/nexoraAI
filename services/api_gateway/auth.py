import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Header, HTTPException, status

from .database import get_db

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "14"))

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt_hex, digest_hex = password_hash.split(":", maxsplit=1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 120000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=ACCESS_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> tuple[str, str]:
    exp = datetime.now(UTC) + timedelta(days=REFRESH_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), exp.isoformat()


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def get_current_user_id(authorization: str = Header(..., alias="Authorization")) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.replace("Bearer ", "", 1)
    payload = decode_token(token, "access")
    return int(payload["sub"])


def create_session(user_id: int, device_id: int | None = None) -> tuple[str, str]:
    refresh_token, expires_at = create_refresh_token(user_id)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, device_id, refresh_token, expires_at, revoked) VALUES (?, ?, ?, ?, 0)",
            (user_id, device_id, refresh_token, expires_at),
        )
    return create_access_token(user_id), refresh_token


def revoke_refresh_token(token: str) -> None:
    with get_db() as conn:
        conn.execute("UPDATE sessions SET revoked = 1 WHERE refresh_token = ?", (token,))


def validate_refresh_token(token: str) -> int:
    payload = decode_token(token, "refresh")
    user_id = int(payload["sub"])
    with get_db() as conn:
        row = conn.execute("SELECT id FROM sessions WHERE refresh_token = ? AND revoked = 0", (token,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    return user_id
