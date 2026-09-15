# MCP Gateway

Stateless HTTP gateway for routing tool calls to the correct MCP server.
No auth/permission logic — forwards token as-is to upstream.

## Architecture

```
UI Backend
    │ Authorization: Bearer <token>
    ▼
MCP Gateway  ← this service
    │ Authorization: Bearer <token>  (forwarded unchanged)
    ▼
MCP Notify (or other MCP servers)
```

## Run locally

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Gateway health |
| GET | /health/servers | Per-server health |
| GET | /v1/servers | List registered MCP servers |
| GET | /v1/tools | Aggregated tool catalog |
| POST | /v1/tools/call | Route and execute a tool |

## Adding a new MCP server

Edit `config/servers.yml`:

```yaml
servers:
  notify:
    base_url: "http://mcp-notify:8080"
  hr:
    base_url: "http://mcp-hr:8080"
```

No code changes needed.

## Tests

```bash
pytest tests/ -v
```
