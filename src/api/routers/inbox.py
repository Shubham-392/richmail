from fastapi import APIRouter, Depends, status
from src.api.auth.utils import error_response
from src.api.routers.security import getCurrentPayload

from src.api.conf.db import pool

router = APIRouter()

@router.post("/inbox/", tags=["list of the users income emails"])
async def getInbox(
    user: dict = Depends(getCurrentPayload)
):
    try:
        ...
            
            
    except Exception as e:
        return error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="Internal Server held it's not your fault.",
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    