from fastapi.responses import JSONResponse
from fastapi import status
from typing import Optional, Any
from datetime import datetime, timedelta, timezone
from src.api.auth.security import JWT_ACCESS_TOKEN_LIFETIME, JWT_REFRESH_TOKEN_LIFETIME, JWT_SECRET_KEY, hasher

from src.api.conf.db import pool

import jwt

def error_response(error_code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False, 
            "error_code": error_code, 
            "error": message 
        }
    )

def success_response(message: str, data: Any = None, status_code: int = status.HTTP_200_OK):
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return JSONResponse(status_code=status_code, content=response)


ALGORITHM = "HS256"

def _build_payload(
    token_type: str,
    user_id: int,
    email:str,
    expires_delta: timedelta,
    extra_payload: Optional[dict] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "email": email,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_payload:
        payload.update(extra_payload)
    return payload


def generate_access_token(user_id:str, email:str, extra_payload: Optional[dict] = None) -> str:
    payload = _build_payload(
        token_type="access",
        user_id=user_id,
        email=email,
        expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME),
        extra_payload=extra_payload
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)



async def checkUser(password: str, email: str):
    async with pool.get_db_connection() as cnx:
        async with await cnx.cursor(dictionary=True) as curr:
            # 1. Only look up by email
            query = "SELECT user_id, email, password FROM users WHERE email=%s"
            await curr.execute(query, (email,))
            result = await curr.fetchone()
            
            # 2. If no user found, return None
            if not result:
                return None

            try:
                is_valid = hasher.verify(result['password'], password)
            except Exception:
                
                return None

            if is_valid:
                return result
            
            return None
            
            
def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    

def generate_refresh_token(user_id: int, email:str, extra_payload: Optional[dict] = None) -> str:
    payload = _build_payload(
        token_type="refresh",
        user_id=user_id,
        email=email,
        expires_delta=timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME),
        extra_payload=extra_payload
    )
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
                
