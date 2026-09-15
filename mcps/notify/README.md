# MCP Notify Server

HTTP-based MCP server that adapts `notify.send_one` tool calls into real Notify API requests.

## Run locally

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Run with Docker

```bash
docker build -t mcp-notify .
docker run -p 8080:8080 --env-file .env mcp-notify
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /v1/tools | List available tools |
| POST | /v1/tools/call | Execute a tool |

## curl examples

```bash
# Health
curl http://localhost:8080/health

# Tool discovery
curl http://localhost:8080/v1/tools

# Send notification
curl -X POST http://localhost:8080/v1/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "tool": "notify.send_one",
    "arguments": {
      "message": "جلسه فردا ساعت ۱۰ است",
      "subject": "جلسه",
      "priority": 1,
      "providerType": 1,
      "userName": "1234567890"
    }
  }'
```

## providerType mapping

| Value | Channel |
|-------|---------|
| 1 | SMS |
| 2 | Bale |
| 3 | Email |

## Tests

```bash
pytest tests/ -v
```

## Security notes

- Authorization header is forwarded as-is to Notify API
- Token is never logged
- No retry on POST (prevents duplicate notifications)
