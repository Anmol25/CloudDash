from types import SimpleNamespace

import agents.triage_agent as triage_agent


class FakeModel:
    def __init__(self, *args, **kwargs):
        pass

    def with_structured_output(self, _schema):
        return self

    def invoke(self, _messages):
        raise RuntimeError("boom")


def test_triage_agent_fallback(monkeypatch):
    monkeypatch.setattr(triage_agent, "ChatGoogleGenerativeAI", FakeModel)
    state = {"messages": [SimpleNamespace(content="hello")]}
    result = triage_agent.triageAgent(state)
    assert result["tasks"][0]["intent"] == "escalation"
    assert result["tasks"][0]["status"] == "pending"
    assert result["tasks"][0]["summary"] == "hello"
