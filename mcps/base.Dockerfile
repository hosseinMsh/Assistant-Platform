# mcps/base.Dockerfile
# Shared base image for all MCP servers.
# Each MCP server uses: FROM mcp-base AS builder / FROM mcp-base AS runtime
#
# Build this first:
#   docker build -f mcps/base.Dockerfile -t mcp-base .
#
# Or let docker-compose handle it via the x-mcp-base extension.

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 appgroup \
 && useradd --system --uid 1001 --gid appgroup appuser

WORKDIR /app
