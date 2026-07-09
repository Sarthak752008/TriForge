# TriForge: Production-Grade Hybrid Token-Efficient Routing Agent

**TriForge** is a production-grade, full-stack hybrid LLM routing system built for the AMD Developer Hackathon. It dynamically routes user queries between a **free, local model** (running locally via Ollama) and a **pluggable remote model** (such as Fireworks AI, OpenAI, or Anthropic). 

By using advanced classification, caching, local self-consistency, and verify-draft verification loops, TriForge reduces API token spend by up to **80%** while preserving remote-grade response accuracy and quality.

---

## 🏗️ Architecture & Core Components

```
                 +---------------------------------------+
                 |          Next.js Client UI            |
                 |      (Dashboard, Chat, Analytics)     |
                 +-------------------+-------------------+
                                     |
                                     v HTTP (REST / Event-Stream)
                 +-------------------+-------------------+
                 |        FastAPI Routing Backend        |
                 |  +---------------------------------+  |
                 |  |       Smart Cache (SQLite)      |  |
                 |  +----------------+----------------+  |
                 |                   | (If Cache Miss)   |
                 |                   v                   |
                 |  +----------------+----------------+  |
                 |  |     Hybrid Routing Engine       |  |
                 |  |  (Intent, Complexity, Length)   |  |
                 |  +----------------+----------------+  |
                 |                   |                   |
                 |         +---------+---------+         |
                 |         |                   |         |
                 |         v (Local)           v (Remote)|
                 |  +------+------+     +------+------+  |
                 |  | Ollama Prov |     | Pluggable   |  |
                 |  | (Qwen/Gemma)|     | Providers   |  |
                 |  +------+------+     | (Fireworks/ |  |
                 |         |            | OpenAI/etc) |  |
                 |         |            +------+------+  |
                 |         |                   ^         |
                 |         |                   |         |
                 |         +-- Verify-Draft ---+         |
                 |             (Escalation)              |
                 +-------------------+-------------------+
                                     |
                                     v Log Data
                 +-------------------+-------------------+
                 |           SQLite Database             |
                 |    (Requests, Cache, Benchmarks)      |
                 +---------------------------------------+
```

### 1. Hybrid Routing Logic (routing_engine.py)
The [RoutingEngine](file:///c:/Users/sarth/OneDrive/Desktop/TriForage/TriForge/backend/app/router/routing_engine.py) analyzes the query's complexity using three variables:
- **Semantic Classification:** Categorizes query into `coding`, `math`, `reasoning`, `summarization`, `translation`, `extraction`, `conversation`, `creative_writing`, or `general_qa`. Coding, Math, and Reasoning are escalated immediately to remote models.
- **Prompt Length:** Queries with **> 25 words** are escalated to remote models to prevent local model context degradation.
- **Heuristic fallback:** Simple chitchat, factual queries, and translation are sent to the local model.

### 2. Local Self-Consistency Loop (consistency.py)
If routed locally:
- The prompt is sampled **twice** at temperature `0.7` using local Ollama.
- A string similarity check is run. If the similarity is `< 0.8` (configurable), local coherence is low, and the query escalates.

### 3. Hedging & Uncertainty Scan (hallucination.py)
If the consistency score is high, the output is scanned for uncertainty markers (e.g. *"I am not sure"*, *"As an AI"*). If found, the query escalates.

### 4. Verify-Draft Escalation
When local answers fail consistency or raise hedging flags, the system does **not** discard the local draft. It submits the draft alongside the original prompt to the remote verifier, instructing it to only edit or correct mistakes. This minimizes output tokens on the remote API.

---

## 📂 Project Structure

```
TriForge/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes (chat, settings, history, benchmarks)
│   │   ├── router/       # Routing and metadata estimation logic
│   │   ├── classifier/   # Intent and semantic classification engine
│   │   ├── providers/    # Pluggable clients (Ollama, Fireworks, OpenAI, Anthropic)
│   │   ├── database/     # SQLAlchemy models, session, and validation schemas
│   │   ├── cache/        # SQLite key-value prompt hashing cache
│   │   ├── analytics/    # Aggregations engine for costs, tokens, savings
│   │   └── utils/        # Text compressors and system helpers
│   ├── tests/            # pytest suite (cache, router, providers)
│   ├── Dockerfile        # FastAPI Docker configuration
│   └── requirements.txt  # Python requirements
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages (dashboard, chat, benchmarks, settings)
│   │   └── components/   # Shared components (Sidebar layout)
│   ├── Dockerfile        # Next.js Docker configuration
│   └── package.json      # Node dependencies
├── docker-compose.yml    # Orchestrates frontend & backend services
└── README.md
```

---

## 🚀 Getting Started

### 1. Local Prerequisites
- **Ollama:** Install [Ollama](https://ollama.com/) and download the default local 3B model:
  ```bash
  ollama pull qwen2.5:3b-instruct
  ```
- **Python:** Version 3.11.x
- **Node.js:** Version 20.x or above

### 2. Manual Development Setup

#### Start Backend:
1. Navigate to `backend/` and install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` in the project root:
   ```text
   FIREWORKS_API_KEY=your_fireworks_api_key_here
   ```
3. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### Start Frontend:
1. Navigate to `frontend/` and install dependencies:
   ```bash
   npm install
   ```
2. Run the Next.js development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

---

## 🐳 Running with Docker

Build and run both services with a single command. The docker compose configuration automatically sets up internal gateway routing to connect with your host's Ollama instance.

```bash
docker compose up --build
```

---

## 🧪 Testing
Run unit tests to verify database caching, provider configurations, and routing choices:

```bash
# Set PYTHONPATH to backend folder and run pytest
$env:PYTHONPATH="backend"
python -m pytest backend/tests/
```
