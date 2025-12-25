from fastapi import FastAPI
from .routers.outbox import router as outbox_router

app = FastAPI(root_path = "/setxapi")
app.include_router(outbox_router, prefix="/setxapi")


@app.get("/", tags=['root'])
async def root():
    return {"message": "Welcome to Setu Mailing Application!"}
