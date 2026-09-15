# Assistant Platform

سیستم چت هوشمند با قابلیت ارسال اعلان از طریق Agent و MCP.

## ساختار پروژه

```
assistant-platform/
├── ui/                        ← Next.js frontend
├── ui-backend/                ← FastAPI + Agent + Redis + PostgreSQL
├── mcps/                      ← همه MCP serverها اینجا هستند
│   ├── base.Dockerfile        ← base image مشترک
│   ├── shared-requirements.txt← dependencies مشترک
│   ├── ADDING_NEW_MCP.md      ← راهنمای افزودن MCP جدید
│   ├── gateway/               ← MCP Gateway (routing)
│   │   └── config/
│   │       └── servers.yml    ← ← ← فقط این فایل برای MCP جدید ویرایش میشه
│   └── notify/                ← MCP Notify (Notify API adapter)
├── .env.example               ← env variables برای docker-compose
└── docker-compose.yml
```

## معماری

```
Browser
  │ HTTPS + Session Cookie
  ▼
UI (Next.js :3000)
  │
  ▼
UI Backend (FastAPI :8000)
  │ Bearer Token
  ▼
MCP Gateway (internal)
  │ Bearer Token (forwarded)
  ├──► MCP Notify (internal)
  │      │ Bearer Token (forwarded)
  │      ▼
  │    Notify API (external)
  └──► MCP HR / Finance / ... (آینده)
```

## راه‌اندازی سریع

```bash
# 1. کپی و ویرایش env فایل‌ها
cp .env.example .env
cp mcps/notify/.env.example mcps/notify/.env
cp mcps/gateway/.env.example mcps/gateway/.env
cp ui-backend/.env.example ui-backend/.env
cp ui/.env.example ui/.env

# 2. ویرایش مهم در ui-backend/.env:
#    LLM_API_KEY=sk-...
#    SECRET_KEY=<random string>

# 3. ویرایش مهم در mcps/notify/.env:
#    NOTIFY_BASE_URL=https://notify.yourdomain.ir

# 4. اجرا
docker compose up --build
```

- UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

## افزودن MCP جدید

فقط ۴ قدم — بدون تغییر در کد:

1. پوشه `mcps/<name>/` بساز (الگو در `mcps/ADDING_NEW_MCP.md`)
2. سرویس را به `docker-compose.yml` اضافه کن (کپی از `mcp-notify`)
3. سرویس را به `depends_on` گیت‌وی اضافه کن
4. آدرس را در `mcps/gateway/config/servers.yml` اضافه کن

## تنظیمات

### LLM (در ui-backend/.env)
```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
```
برای Ollama:
```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3
```

### Production
```env
COOKIE_SECURE=true
SECRET_KEY=<strong-random-key>
API_BASE_URL=https://api.yourdomain.com
```

## تست

```bash
cd mcps/notify && pytest tests/ -v
cd mcps/gateway && pytest tests/ -v
cd ui-backend   && pytest tests/ -v
cd ui           && npm test
```
