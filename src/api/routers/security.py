from fastapi import status, HTTPException
from pydantic import ValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from fastapi import Security
from src.api.auth.utils import decode_token



bearer_scheme = HTTPBearer(auto_error=False)

async def getCurrentPayload(
    credentials: Optional[HTTPAuthorizationCredentials]= Security(bearer_scheme)
):
    """
    Extracts and validates user information from JWT token.
    Now manually handles missing tokens to return proper 401 errors.
    """
    # Handle missing token - this should return 401, not 403
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    # Handle empty token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
            
        return payload
            
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required fields or contains invalid values",
        )
        
        
    