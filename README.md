# RuralBiz AI 🌾

> **AI-Driven Hyper-Local Business Advisory & Financial Structuring Assistant for Rural Micro-Entrepreneurs in India**

[![Tests](https://img.shields.io/badge/tests-628%20passing-brightgreen)](./backend/app/tests)
[![TypeScript](https://img.shields.io/badge/TypeScript-zero%20errors-blue)](./frontend)
[![Python](https://img.shields.io/badge/Python-3.12-yellow)](./backend)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## Problem

Over **100 million rural micro-entrepreneurs** in India lack access to quality business advisory, financial planning tools, and government scheme guidance. They face:

- **No personalized guidance** — generic advice doesn't fit their capital, skills, or location
- **Language barriers** — most tools are English-only
- **Digital divide** — complex interfaces and technical jargon are inaccessible
- **Scheme blindness** — millions miss out on PMEGP, MUDRA, and other support schemes

---

## Solution

**RuralBiz AI** is a full-stack AI advisory platform that provides:

- 🤖 **Multi-agent AI advice** — tailored business plans in plain language
- 📊 **Real financial analysis** — ROI, break-even, cash flow projections
- 🗺️ **Hyper-local intelligence** — real competitor data from OpenStreetMap
- 🏛️ **Scheme matching** — automated eligibility scoring for 25+ government schemes
- 🌐 **Multilingual** — English, Hindi, Telugu with voice input and TTS
- 🔌 **Works offline** — full deterministic fallback mode without any API key

---

## Key Features

| Phase | Feature | Technology |
|-------|---------|------------|
| 1 | JWT Authentication & User Profiles | FastAPI, bcrypt |
| 2 | Personalized Business Recommendations | Weighted scoring engine |
| 3 | Financial Intelligence | ROI, break-even, cash flow |
| 4 | Investment Optimizer | Google OR-Tools (ILP) |
| 5 | Hyper-Local Market Intelligence | OpenStreetMap + Overpass API |
| 6 | Government Scheme Matching | 25+ schemes, eligibility scoring |
| 7 | Multi-Agent AI Advisor | LangGraph + Gemini 1.5 Flash |
| 8 | Semantic Personalization | Saved businesses, action items |
| 9 | Entrepreneur Analytics | Goals, milestones, progress tracking |
| 10 | Multilingual + Voice | en/hi/te, Web Speech API, TTS |
| 11 | Production Readiness | Docker, rate limiting, security headers |

---

## Architecture

```
Frontend (React + TypeScript + Vite)
         ↕ HTTPS / REST API
FastAPI Backend + JWT Auth
         ↕
┌──────────────────────────────────────────────┐
│         Internal RuralBiz AI Services        │
│  Recommendation Engine  │  Financial Calc    │
│  OR-Tools Optimizer     │  Market Intel      │
│  Scheme Matcher         │  Analytics Engine  │
│  Translation Service    │  LangGraph AI      │
└──────────────────────────────────────────────┘
         ↕
SQLite (dev) / PostgreSQL (prod)
         ↕ (optional)
External: Gemini API | OpenStreetMap | Overpass API
```

---

## Tech Stack

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, react-i18next, Web Speech API, React Router v6

**Backend:** FastAPI, SQLAlchemy (async), Pydantic, JWT (python-jose)

**AI:** Google Gemini 1.5 Flash (optional), LangGraph multi-agent orchestration

**Optimization:** Google OR-Tools (integer linear programming)

**Maps:** OpenStreetMap, Overpass API

**Database:** SQLite (development), PostgreSQL (production)

**DevOps:** Docker, Docker Compose, slowapi rate limiting

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git

### 1. Clone & Setup Backend

```bash
cd backend
# Use the repository's Python 3.12 virtual environment (created by Phase 11)
py -3.12 -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (cmd):
.\.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Variables

```bash
# backend/.env (create this file)
ENVIRONMENT=development
DEBUG=true
JWT_SECRET_KEY=any-random-string-for-development
GEMINI_API_KEY=          # Optional — app works without it
DEMO_MODE=false
```

### 3. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000  
API Docs: http://localhost:8000/docs

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:5173

---

## Demo Mode

Enable demo mode for hackathon demonstrations:

```env
DEMO_MODE=true
```

Demo endpoints:
- `GET /demo/status` — check demo mode
- `GET /demo/profiles` — 3 sample entrepreneur profiles
- `GET /demo/scenarios` — 6 guided demo scenarios

Frontend demo dashboard: http://localhost:5173/demo

### Quick Judge Demo (one-command)

On Windows you can use the included helper to start both backend and frontend in new terminals:

```powershell
.\run_demo.ps1 -OpenBrowser
```

This will open the frontend demo at `http://localhost:5173/demo` and start the backend at `http://localhost:8000`.

---

## Docker

### Quick Start (SQLite, no external DB needed)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### With PostgreSQL

```bash
POSTGRES_PASSWORD=yourpassword docker compose --profile postgres up --build
```

Set `DATABASE_URL=postgresql+asyncpg://ruralbiz:yourpassword@db:5432/ruralbiz` in your `.env`.

---

## Environment Setup (Production)

Copy `.env.production.example` to `.env` and set:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/ruralbiz
JWT_SECRET_KEY=<random 32+ char string>
GEMINI_API_KEY=<your key>           # optional
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

Generate a secure JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Testing

```bash
cd backend

# All tests
python -m pytest app/tests/ -v

# Specific phase
python -m pytest app/tests/test_phase10.py -v
python -m pytest app/tests/test_phase11.py -v

# With coverage
python -m pytest app/tests/ --cov=app --cov-report=term-missing
```

**Current status: 628 tests passed (0 failed) — backend verified on Python 3.12 venv**

### Frontend TypeScript Check

```bash
cd frontend
npx tsc --noEmit
```

**Run TypeScript checks after building (see next steps).**

---

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic health check (backward compatible) |
| `GET /health/live` | Liveness probe — is process alive? |
| `GET /health/ready` | Readiness — is DB connected? |
| `GET /health/details` | Full diagnostics (no secrets exposed) |

---

## Limitations

> These limitations are by design and documented for transparency.

- **AI advice is informational only** — not professional financial or legal advice
- **Financial figures are estimates** — based on aggregated benchmarks, not real market data
- **Government scheme eligibility must be verified** — check official portals before applying
- **Map data depends on OpenStreetMap** — rural areas may have incomplete coverage
- **Gemini AI is optional** — full deterministic fallback mode always available without API key
- **Voice features depend on browser support** — requires Chrome/Edge for Web Speech API
- **Translation is dictionary-based** in fallback mode — Gemini provides better quality when available

---

## Project Structure

```
myproject/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph multi-agent system (Phase 7)
│   │   ├── api/             # FastAPI route handlers
│   │   ├── core/            # Config, logging, exceptions (Phase 11)
│   │   ├── database/        # SQLAlchemy engine + session
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic services
│   │   └── tests/           # 574+ test cases
│   ├── Dockerfile
│   ├── .env.production.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── context/         # React context (Auth)
│   │   ├── i18n/            # Translations (en/hi/te)
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client services
│   │   └── types/           # TypeScript types
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Contributing

This project was built for a hackathon. For issues or contributions, please open a GitHub issue.

---

## License

MIT License — see LICENSE file for details.
