from fastapi import APIRouter, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.conf.db import pool

router = APIRouter()


@router.post("/inbox/", tags=["JWT Token"])
async def getInbox(
    request:Request
):
    ...
    