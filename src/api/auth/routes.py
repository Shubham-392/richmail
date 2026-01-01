from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from src.api.auth.schemas import UserModel, TokenRefreshRequest
from src.api.auth.utils import checkUser, decode_token, error_response, generate_access_token, generate_refresh_token
from src.api.conf.db import pool

router = APIRouter()

@router.post("/getTokens/",tags=["Authentication"])
async def getTokens(request: Request, payload:UserModel):
    try:
        userPassword = payload.password
        userEmail = payload.email
        
        user = await checkUser(password=userPassword, email=userEmail)
        if user is None:
            return error_response(
                "USER_NOT_FOUND", 
                "You are not registered with us!", 
                status.HTTP_404_NOT_FOUND
            )
            
        user_id = user.get('user_id')
        email = user.get('email')
        
        accessToken = generate_access_token(user_id=user_id,email=email)
        refreshToken = generate_refresh_token(user_id=user_id, email=email)
            
            
        return JSONResponse(
            content={
                "success":True,
                "accessToken":accessToken,
                "refreshToken":refreshToken
            },
            status_code=220
        )
        
    except Exception as e:
        error_content = {
            "success": False,
            "message": "An internal server error occurred",
            "error_details": str(e),
        }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_content
        )
        
        
@router.post("/getTokens/refresh/",tags=["Regenerate Access Token"])
async def token_refresh(payload: TokenRefreshRequest):
    try:
        token_payload = decode_token(payload.refresh_token)
        if not token_payload or token_payload.get('type') != 'refresh':
            return error_response(
                error_code="REFRESH_TOKEN_INVALID",
                message="Invalid or expired refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
        user_id = token_payload.get('user_id')
        email = token_payload.get('email')
        
        if (not user_id ) or (not email):
            return error_response(
                error_code="TOKEN_MISSING_FIELDS",
                message="Token missing information",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            
            
        accessToken = generate_access_token(user_id=user_id,email=email)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "access_token": accessToken,
            }
        )
        
    except Exception as e:
        return error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="Something went wrong on our end. Please try again later.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
            
        