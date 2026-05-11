CloudDash Customer Support Bot
==============================

Overview
--------
CloudDash is a multi-agent customer support service built on FastAPI, LangGraph, and Gemini models. It triages user requests, routes them to specialized agents (billing, technical, escalation), retrieves knowledge base context from ChromaDB, and streams the final response back to the client.

Key Features
------------
- Multi-agent orchestration with LangGraph
- Triage and routing by intent (billing, technical, escalation)
- Knowledge base retrieval tool backed by ChromaDB
- Streaming NDJSON responses for responsive UI updates
- Structured handover logging for audit and analytics

Agent Flow
----------
![Architecture](images/Architecture.png)

Architecture
------------
The system is a LangGraph workflow assembled at runtime from config/agents.yaml. A single request moves through these stages:

1. API + Orchestrator: The FastAPI endpoint creates a thread_id, loads the Chroma collection, and constructs the LangGraph state machine with tool nodes and routing rules.
2. Triage Agent: Parses the user message into structured tasks, each with intent, priority context, and entities.
3. Dispatcher: Reads the pending task list and routes to the correct specialist by intent (billing, technical, escalation), with a safe fallback when intent is unknown.
4. Specialist Agents:
	- Billing Agent: Handles billing tasks and can call the knowledge base retriever.
	- Technical Agent: Handles technical tasks and can call the knowledge base retriever.
5. Escalation Path: Escalation Agent packages context for a human; Human Agent generates a human-style response for escalated issues.
6. Finalizer: Aggregates outputs from specialist agents into a single response when no human handoff is required.

Operational Notes
- Tool calls are executed via LangGraph ToolNode; tool responses re-enter the same agent for completion.
- Handovers between agents are logged for audit and analytics.
- Responses stream back as NDJSON events so clients can render partial output.

Configuration
-------------
- Agent models, prompts, tools, and routing are defined in config/agents.yaml.
- System prompts live in config/prompts/.
- Agent state schema is defined in config/schema.py.

Project Structure
-----------------
```
CloudDash/
├── .venv
├── main.py
├── README.md
├── requirements.txt
├── agents/
├── api/
├── config/
├── knowledge_base/
├── logger/
├── retrieval/
└── tests/
```

Installation
------------
1. Create and activate a virtual environment.
2. Install dependencies.

Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment Variables
---------------------
Set these before running the API:

- GEMINI_API_KEY or GOOGLE_API_KEY: required for Gemini embeddings and chat models.
- CORS_ORIGINS: optional, comma-separated list of allowed origins (defaults to *).
- HANDOVER_LOG_PATH: optional custom path for handover logs.

For Using Langsmith Observability Tool:
- LANGSMITH_TRACING="true"
- LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
- LANGCHAIN_API_KEY="lsv2_***************************"
- LANGCHAIN_PROJECT="CloudDash"

Running the API
---------------
```
uvicorn main:app --host 0.0.0.0 --port 8000
```

API Usage
---------
POST /agent

Request body:
```
{
	"message": "My billing invoice looks wrong.",
	"thread_id": "optional-existing-thread-id"
}
```

Response:
- Streaming NDJSON with events like `thread_id` and `message`.

Notes
-----
- The knowledge base is loaded from knowledge_base/knowledge_base.json at startup.
- Each request reuses the configured Chroma collection and embeds documents with Gemini embeddings.

Testing
-------
```
pytest
```


