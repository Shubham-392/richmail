from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from src.api.auth.utils import error_response
from src.api.routers.security import getCurrentPayload
from src.api.routers.schemas import EmailResponse

from src.api.conf.db import pool

router = APIRouter()

@router.get("/inbox/", response_model=EmailResponse , tags=["list of the users income emails"])
async def getInbox(
    user: dict = Depends(getCurrentPayload)
):
    try:
        user_id = user['user_id']
        async with pool.get_db_connection() as cnx:
            async with await cnx.cursor(dictionary=True) as curr:
                query = (
                    "SELECT "
                    "inbox_id AS message_id, "
                    "sender AS sender_email, "
                    "subject, "
                    "LEFT(body, 100) AS message_snippet, "
                    "is_readed "
                    "FROM inbox_emails "
                    "WHERE user_id = %s "
                    "ORDER BY received_at DESC"
                )
                await curr.execute(query, (user_id, ))
                results = await curr.fetchall()

        
        response = {
            "success": True,
            "emails":results
        }
        
        response = jsonable_encoder(response)
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
            
            
    except Exception as e:
        return error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message="Internal Server held it's not your fault.",
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    