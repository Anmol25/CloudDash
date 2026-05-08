from langchain_core.retrievers import BaseRetriever
from typing import List
from langchain_core.documents import Document
from langchain_core.tools.retriever import create_retriever_tool


class CustomChromaRetriever(BaseRetriever):
    collection: any
    k: int = 5

    def _get_relevant_documents(
        self,
        query: str
    ) -> List[Document]:
        results = self.collection.query(
            query_texts=[query],
            n_results=self.k
        )

        formatted = list(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0]
        ))
        return formatted


def get_retriever_tool(collection):
    retriever = CustomChromaRetriever(
        collection=collection,
        k=5
    )

    return create_retriever_tool(
        name="knowledge_base_retriever",
        retriever=retriever,
        description=(
            "Tool to retrieve articles from knowledge base "
            "to answer customer queries."
        )
    )
