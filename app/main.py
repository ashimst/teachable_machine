from contextlib import asynccontextmanager
from fastapi import FastAPI,File, UploadFile, Form
from typing import List, Dict
from app.database import initialize_db,client
from app.routers import auth,projects
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_db()
    yield
    client.close()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)

@app.get('/')
def root():
    return {"message":"working"}

