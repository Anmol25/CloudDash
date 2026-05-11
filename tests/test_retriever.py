import pytest

from langchain_core.documents import Document
from retrieval.retriever import CustomChromaRetriever, get_retriever_tool


class FakeCollection:
    def __init__(self, raise_error=False):
        self.raise_error = raise_error

    def query(self, query_texts, n_results):
        if self.raise_error:
            raise RuntimeError("boom")
        return {
            "documents": [["Doc A", "Doc B"]],
            "metadatas": [[{"title": "A", "category": "cat", "last_updated": "2020", "tags": "t"},
                           {"title": "B", "category": "cat", "last_updated": "2021", "tags": "t2"}]],
            "ids": [["id-a", "id-b"]],
        }


def test_custom_retriever_builds_documents():
    retriever = CustomChromaRetriever(collection=FakeCollection(), k=2)
    docs = retriever._get_relevant_documents("query")
    assert len(docs) == 2
    assert docs[0].metadata["id"] == "id-a"
    assert docs[0].page_content == "Doc A"


def test_custom_retriever_returns_empty_on_error():
    retriever = CustomChromaRetriever(
        collection=FakeCollection(raise_error=True), k=2)
    docs = retriever._get_relevant_documents("query")
    assert docs == []


def test_retriever_tool_formats_output(monkeypatch):
    def fake_invoke(self, query):
        return [
            Document(page_content="Hello", metadata={
                     "id": "1", "title": "T", "category": "C", "last_updated": "2022", "tags": "x"})
        ]

    monkeypatch.setattr(CustomChromaRetriever, "invoke", fake_invoke)
    tool_fn = get_retriever_tool(collection=object())
    result = tool_fn.invoke({"query": "query"})
    assert "ID: 1" in result
    assert "TITLE: T" in result
    assert "CONTENT:" in result


def test_retriever_tool_handles_failure(monkeypatch):
    def fake_invoke(self, query):
        raise RuntimeError("fail")

    monkeypatch.setattr(CustomChromaRetriever, "invoke", fake_invoke)
    tool_fn = get_retriever_tool(collection=object())
    result = tool_fn.invoke({"query": "query"})
    assert "retrieval failed" in result.lower()
