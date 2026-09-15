# New MCP Server Template
# Copy this folder to mcps/<name>/ and follow the steps below.

## Steps to add a new MCP server

### 1. Create the service folder
```
mcps/
└── <name>/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── api/
    │   │   └── routes/
    │   │       ├── __init__.py
    │   │       ├── health.py       ← GET /health → {"status": "ok"}
    │   │       └── tools.py        ← GET /v1/tools, POST /v1/tools/call
    │   ├── tools/
    │   │   └── <tool_name>.py     ← TOOL_SCHEMA + execute()
    │   ├── schemas/
    │   │   └── <name>.py
    │   ├── clients/
    │   │   └── <name>_client.py   ← httpx client for downstream API
    │   └── core/
    │       └── config.py
    ├── tests/
    ├── Dockerfile                  ← Copy from mcps/notify/Dockerfile, change name
    ├── requirements.txt            ← Start with: -r ../shared-requirements.txt
    ├── .env.example
    └── README.md
```

### 2. Dockerfile pattern (copy from mcps/notify/Dockerfile, change paths)
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY mcps/shared-requirements.txt ./shared-requirements.txt
COPY mcps/<name>/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
# ... (same as notify)
COPY mcps/<name>/app/ ./app/
```

### 3. Add to docker-compose.yml
```yaml
  mcp-<name>:
    <<: [*mcp-defaults, *mcp-healthcheck, *logging]
    build:
      context: .
      dockerfile: mcps/<name>/Dockerfile
    env_file: mcps/<name>/.env
    expose:
      - "8080"
```

### 4. Add to mcp-gateway depends_on
```yaml
  mcp-gateway:
    depends_on:
      mcp-notify:
        condition: service_healthy
      mcp-<name>:          # ← add this
        condition: service_healthy
```

### 5. Register in gateway
Edit `mcps/gateway/config/servers.yml`:
```yaml
servers:
  notify:
    base_url: "http://mcp-notify:8080"
  <name>:
    base_url: "http://mcp-<name>:8080"
```

That's it. No other files need changing.
