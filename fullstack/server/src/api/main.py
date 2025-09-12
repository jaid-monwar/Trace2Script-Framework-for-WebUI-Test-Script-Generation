import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(".")

from src.api.config import API_PREFIX
from src.api.routers import auth, hello, results, tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FastAPI Auth",
    description="FastAPI authentication system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(tasks.router, prefix=API_PREFIX)
app.include_router(results.router, prefix=API_PREFIX)





@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Auth API. Go to /docs for documentation."}