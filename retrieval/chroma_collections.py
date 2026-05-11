import os
import chromadb
import json
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import yaml

load_dotenv()

if not os.getenv("GEMINI_API_KEY") and os.getenv("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

client = chromadb.Client()


def _load_embedding_config():
    try:
        with open("./config/agents.yaml", "r") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    return config.get("embeddings", {}) or {}


def _build_records(docs):
    records = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        doc_id = doc.get("id")
        title = doc.get("title")
        content = doc.get("content")
        if not doc_id or not title or not content:
            continue
        tags = doc.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        records.append(
            (
                str(doc_id),
                f"{title}\n\n{content}",
                {
                    "title": title,
                    "category": doc.get("category", ""),
                    "last_updated": doc.get("last_updated", ""),
                    "tags": ",".join([str(tag) for tag in tags])
                }
            )
        )
    return records


def get_collection():
    embedding_config = _load_embedding_config()
    gemini_model = embedding_config.get("model")
    dimension = embedding_config.get("dimension")
    if isinstance(dimension, str) and dimension.isdigit():
        dimension = int(dimension)
    if not isinstance(dimension, int):
        dimension = None
    task_type = embedding_config.get("task_type")
    embedding_function = embedding_functions.GoogleGeminiEmbeddingFunction(
        model_name=gemini_model,
        dimension=dimension,
        task_type=task_type
    )
    collection = client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=embedding_function
    )
    with open("./knowledge_base/knowledge_base.json", "r") as f:
        docs = json.load(f)
    records = _build_records(docs)
    if not records:
        return collection
    ids, documents, metadatas = zip(*records)
    collection.upsert(
        ids=list(ids),
        documents=list(documents),
        metadatas=list(metadatas)
    )
    return collection
