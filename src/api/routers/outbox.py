from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.conf.db import pool
from src.api.routers.model import UserMailModel

router = APIRouter()


@router.post("/outbox", tags=["outbox"])
async def read_outbox(payload: UserMailModel):
    try:
        async with pool.get_db_connection() as cnx:
            async with await cnx.cursor(dictionary=True) as curr:
                query = (
                    "SELECT "
                    "id, receiver, data, sent_at "
                    "FROM "
                    "setu_outbox "
                    "WHERE "
                    "sender = %s"
                )
                await curr.execute(query, (payload.email,))
                results = await curr.fetchall()

        results = jsonable_encoder(results)
        response = {
            "success": True,
            "message": "Successfully retrieved outbox mailing list",
            "data": results,
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)

    except Exception as e:
        error_content = {
            "success": False,
            "message": "An internal server error occurred",
            "error_details": str(e),
        }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_content
        )
