from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.conf.db import pool


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield
    # Shutdown event / Close all connections in the pool
    await pool.close()


# FastAPI application using lifespan context manager
app = FastAPI(lifespan=lifespan)


