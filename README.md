# Assistant Platform

<div align="center">

![Private](https://img.shields.io/badge/repo-private-red)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Next.js](https://img.shields.io/badge/next.js-16-black)
![License](https://img.shields.io/badge/license-private-lightgrey)

سیستم چت هوشمند با قابلیت ارسال اعلان از طریق Agent و MCP

</div>

---

## معماری

```
Browser
  │  HTTPS + Session Cookie (HttpOnly)
  ▼
┌─────────────────────┐
│   UI  (Next.js :3000)│  RTL · IRANSans · WebSocket
└─────────┬───────────┘
          │ HTTPS
          ▼
┌─────────────────────┐
│  UI Backend  (:8000) │  FastAPI · Agent/LLM · Redis · PostgreSQL
└─────────┬───────────┘
          │ Bearer Token (forwarded)
          ▼
┌─────────────────────┐
│   MCP Gateway       │  Routing only — no auth logic
└─────────┬───────────┘
          │ Bearer Token (forwarded)
          ▼
┌─────────────────────┐
│   MCP Notify        │  Notify API adapter
└─────────┬───────────┘
          │ Bearer Token (forwarded)
          ▼
    Notify API  (external)
```

## سرویس‌ها

| سرویس | Port | توضیح |
|-------|------|-------|
| `ui` | 3000 | Next.js · RTL · IRANSans · WebSocket |
| `ui-backend` | 8000 | FastAPI · Agent · Session · Confirmation |
| `mcp-gateway` | internal | Routing بین MCP serverها |
| `mcp-notify` | internal | Notify API adapter |
| `postgres` | internal | Conversations · Messages · ToolExecutions |
| `redis` | internal | Sessions · Confirmations (atomic) |

## ویژگی‌های کلیدی

- **Token Normalization** — `Bearer eyJ...` یا `eyJ...` هر دو قبول می‌شوند
- **WebSocket Real-time** — state واقعی backend، reconnect خودکار
- **Atomic Confirmation** — Lua script در Redis، double-execution غیرممکن
- **State Machine** — `pending → confirmed → executing → success/failed`
- **Structured Logging** — `request_id` در همه سرویس‌ها، token هرگز لاگ نمی‌شود
- **RTL + IRANSans** — فونت و layout کامل فارسی

## راه‌اندازی سریع

```bash
# ۱. کپی env فایل‌ها
cp .env.example .env
cp mcps/notify/.env.example mcps/notify/.env
cp mcps/gateway/.env.example mcps/gateway/.env
cp ui-backend/.env.example ui-backend/.env
cp ui/.env.example ui/.env

# ۲. تنظیمات ضروری در ui-backend/.env:
#    LLM_API_KEY=sk-...
#    SECRET_KEY=<random-32-char-string>

# ۳. تنظیمات ضروری در mcps/notify/.env:
#    NOTIFY_BASE_URL=https://notify.yourdomain.ir

# ۴. اجرا
docker compose up --build
```

- UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

## اضافه کردن MCP جدید

فقط ۴ قدم — بدون تغییر در کد اصلی:

```bash
# ۱. کپی template
cp -r mcps/notify mcps/<name>
# ویرایش mcps/<name>/app/ برای API جدید

# ۲. docker-compose.yml — اضافه کردن سرویس (کپی از mcp-notify)

# ۳. depends_on گیت‌وی — اضافه کردن mcp-<name>

# ۴. servers.yml — ثبت آدرس سرویس جدید
```

راهنمای کامل: [`mcps/ADDING_NEW_MCP.md`](mcps/ADDING_NEW_MCP.md)

## تست

```bash
# Backend
cd ui-backend && pytest tests/ -v

# MCP Notify
cd mcps/notify && pytest tests/ -v

# MCP Gateway
cd mcps/gateway && pytest tests/ -v

# Frontend
cd ui && npm test
```

## ساختار پروژه

```
assistant-platform/
├── ui/                        ← Next.js frontend
│   ├── app/                   ← Pages (RTL layout)
│   ├── components/            ← UI components
│   ├── hooks/                 ← useChat · useWebSocket
│   ├── lib/api-client.ts      ← Centralized HTTP + WS client
│   └── types/index.ts         ← TypeScript types
│
├── ui-backend/                ← FastAPI backend
│   ├── app/
│   │   ├── agent/             ← LLM agent (OpenAI-compatible)
│   │   ├── auth/session.py    ← Redis sessions + atomic confirmations
│   │   ├── chat/service.py    ← State machine + WS events
│   │   ├── core/token.py      ← Token normalization
│   │   ├── ws/                ← WebSocket manager + events
│   │   └── models/            ← SQLAlchemy models
│   ├── alembic/               ← DB migrations
│   └── tests/                 ← 31 tests
│
├── mcps/                      ← All MCP servers
│   ├── shared-requirements.txt← Shared dependencies
│   ├── base.Dockerfile        ← Shared base image
│   ├── gateway/               ← MCP Gateway (routing only)
│   │   └── config/servers.yml ← ← Registry (edit to add MCPs)
│   ├── notify/                ← Notify MCP adapter
│   └── ADDING_NEW_MCP.md      ← Step-by-step guide
│
├── .github/
│   ├── workflows/ci.yml       ← Tests + Docker build
│   └── workflows/pr-checks.yml← Lint + secret scan
│
└── docker-compose.yml
```

## Production

```env
COOKIE_SECURE=true
SECRET_KEY=<strong-random-key>
API_BASE_URL=https://api.yourdomain.com
```

پشت Nginx/Caddy با HTTPS اجرا کنید.

## Branches

| Branch | توضیح |
|--------|-------|
| `main` | Production-ready |
| `develop` | Integration branch |
| `feat/*` | Feature branches |
