from fastapi import FastAPI
from .api.routes import health, tools

app = FastAPI(title="MCP Knowledge Server", version="1.0.0")
app.include_router(health.router)
app.include_router(tools.router)

@app.get("/")
def root():
    return {"service": "mcp-knowledge", "status": "running"}
