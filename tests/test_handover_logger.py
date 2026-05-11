import json
import os

from logger.handover_logger import log_handover


def test_log_handover_writes_json_line(tmp_path, monkeypatch):
    log_path = tmp_path / "handovers.json"
    monkeypatch.setenv("HANDOVER_LOG_PATH", str(log_path))

    event = {"thread_id": "t1", "source_agent": "triage",
             "target_agent": "billing"}
    log_handover(event)

    content = log_path.read_text(encoding="utf-8").strip()
    assert content
    data = json.loads(content)
    assert data["thread_id"] == "t1"
    assert data["source_agent"] == "triage"
    assert data["target_agent"] == "billing"
    assert "timestamp" in data
