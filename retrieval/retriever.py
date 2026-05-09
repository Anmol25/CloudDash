from langchain_core.retrievers import BaseRetriever
from typing import List
from langchain_core.documents import Document
from langchain_core.tools import tool


class CustomChromaRetriever(BaseRetriever):
    collection: any
    k: int = 3

    def _get_relevant_documents(
        self,
        query: str
    ) -> List[Document]:
        results = self.collection.query(
            query_texts=[query],
            n_results=self.k
        )

        documents = []

        for doc, metadata, doc_id in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["ids"][0]
        ):

            documents.append(
                Document(
                    page_content=doc,
                    metadata={
                        "id": doc_id,
                        **metadata
                    }
                )
            )

        return documents


def get_retriever_tool(collection):
    retriever = CustomChromaRetriever(
        collection=collection,
        k=3
    )

    @tool
    def knowledge_base_retriever(query: str) -> str:
        """
        Retrieve articles from knowledge base.
        """

        docs = retriever.invoke(query)

        formatted = []

        for doc in docs:
            formatted.append(
                f"""
ID: {doc.metadata.get("id")}
TITLE: {doc.metadata.get("title")}
CATEGORY: {doc.metadata.get("category")}
LAST UPDATED: {doc.metadata.get("last_updated")}
TAGS: {doc.metadata.get("tags")}

CONTENT:
{doc.page_content}
"""
            )

        return "\n\n====================\n\n".join(formatted)

    return knowledge_base_retriever
