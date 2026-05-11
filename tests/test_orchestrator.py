import pytest

from agents.orchestrator import AgentOrchestrator


def test_import_handler_missing_raises():
    orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
    with pytest.raises(ImportError):
        orchestrator._import_handler("agents.triage_agent", "missingHandler")
