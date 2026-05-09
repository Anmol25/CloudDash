import chromadb
import json

client = chromadb.Client()


def get_collection():
    collection = client.get_or_create_collection(
        name="knowledge_base"
    )
    with open("./knowledge_base/knowledge_base.json", "r") as f:
        docs = json.load(f)
    ids = [doc["id"] for doc in docs]

    documents = [
        f"{doc['title']}\n\n{doc['content']}"
        for doc in docs
    ]

    metadatas = [
        {
            "title": doc["title"],
            "category": doc["category"],
            "last_updated": doc["last_updated"],
            "tags": ",".join(doc["tags"])
        }
        for doc in docs
    ]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    return collection
