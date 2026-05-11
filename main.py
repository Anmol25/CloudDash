import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from retrieval.chroma_collections import get_collection
from dotenv import load_dotenv
from api.api import router as api_router
from logger import configure_logging

load_dotenv()
configure_logging()


def lifespan(app: FastAPI):
    collection = get_collection()
    app.state.collection = collection
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

# Configure CORS for cloud deployments. Use CORS_ORIGINS env var (comma-separated) or allow all.
cors_origins_env = os.getenv("CORS_ORIGINS", "*")
cors_origins = [origin.strip()
                for origin in cors_origins_env.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def index():
    return {"Welcome To CloudDash api"}
