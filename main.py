from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from retrieval.chroma_collections import get_collection
from dotenv import load_dotenv
from api.api import router as api_router

load_dotenv()


def lifespan(app: FastAPI):
    collection = get_collection()
    app.state.collection = collection
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)


@app.get('/')
def index():
    return {"Welcome To CloudDash api"}
