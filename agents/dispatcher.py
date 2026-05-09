from config.schema import AgentState


def dispatcher_node(state: AgentState):
    return state


def dispatcher(state: AgentState):
    tasks = state["tasks"]
    pending_tasks = [t for t in tasks if t["status"] == "pending"]

    if not pending_tasks:
        return "finalizer"

    next_task = pending_tasks[0]

    if next_task["intent"] == "technical":
        return "technicalAgent"
    elif next_task["intent"] == "billing":
        return "billingAgent"
    else:
        raise ValueError(f"Unknown intent: {next_task['intent']}")
