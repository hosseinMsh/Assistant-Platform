# UI Backend

FastAPI-based backend. Manages sessions, runs the LLM agent, handles confirmations, and routes tool calls through MCP Gateway.

## Run locally

```bash
cp .env.example .env
# edit .env with your LLM key, DB, Redis URLs
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Run migrations

```bash
alembic upgrade head
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| POST | /api/v1/auth/session | Submit access token, get session cookie |
| POST | /api/v1/auth/logout | Invalidate session |
| POST | /api/v1/chat | Send message, get reply or confirmation |
| POST | /api/v1/chat/confirm | Confirm pending tool execution |
| POST | /api/v1/chat/cancel | Cancel pending tool execution |
| GET | /api/v1/conversations | List conversations |
| GET | /api/v1/conversations/{id} | Get conversation with messages |

## Security notes

- Access token stored server-side in Redis only (never in browser)
- HttpOnly session cookie
- Token never logged
- Confirmation ownership verified before execution
- Confirmations expire after 5 minutes
