import pytest

from agents.dispatcher import dispatcher, _intent_to_agent, _fallback_node


def _make_task(intent, status="pending"):
    return {
        "intent": intent,
        "task": "do it",
        "summary": "summary",
        "status": status,
        "entities": [],
    }


def test_dispatcher_routes_known_intent():
    state = {"tasks": [_make_task("billing")]}
    result = dispatcher(state)
    assert result == _intent_to_agent["billing"]


def test_dispatcher_routes_unknown_intent_to_fallback():
    state = {"tasks": [_make_task("unknown")]}
    result = dispatcher(state)
    assert result == _fallback_node


def test_dispatcher_routes_no_pending_to_fallback():
    state = {"tasks": [_make_task("billing", status="completed")]}
    result = dispatcher(state)
    assert result == _fallback_node


def test_dispatcher_exception_routes_to_fallback():
    result = dispatcher({})
    assert result == _fallback_node
