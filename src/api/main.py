from fastapi import FastAPI
from src.api.routers.outbox import router as outbox_router
from src.api.routers.inbox import router as inbox_router
from src.api.auth.routes import router as auth

app = FastAPI(root_path = "/setxapi")
# register the routers for different endpoints

app.include_router(outbox_router)

app.include_router(inbox_router)

app.include_router(auth)

#-------------------------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=['root'])
async def root():
    return {"message": "Welcome to Setu Mailing Application!"}
