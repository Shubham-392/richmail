from fastapi import FastAPI
from .routers.outbox import router as outbox_router

app = FastAPI()
app.include_router(outbox_router)


@app.get("/setxapi/", tags=['root'])
async def root():
    return {"message": "Welcome to Setu Mailing Application!"}
