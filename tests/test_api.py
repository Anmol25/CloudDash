import importlib

from fastapi.responses import StreamingResponse


def test_call_agent_returns_streaming_response(monkeypatch):
    import retrieval.chroma_collections as chroma
    monkeypatch.setattr(chroma, "get_collection", lambda: object())

    import api.api as api_module
    importlib.reload(api_module)

    class FakeOrchestrator:
        def __init__(self, collection, thread_id, checkpointer):
            self.collection = collection
            self.thread_id = thread_id
            self.checkpointer = checkpointer

        def run(self, _msg):
            yield b"{\"type\": \"message\", \"content\": \"ok\"}\n"

    monkeypatch.setattr(api_module, "AgentOrchestrator", FakeOrchestrator)
    api_module.collection = object()

    request = api_module.AgentRequest(message="hi")
    response = api_module.call_agent(request)
    assert isinstance(response, StreamingResponse)
