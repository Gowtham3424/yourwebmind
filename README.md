# SEARCHMIND

> "An SEO agent that remembers what happened, learns what worked, and gets smarter over time."

SEARCHMIND is an SEO intelligence agent powered by **Vectorize Hindsight** persistent memory. Instead of stateless, one-off analysis, SearchMind retains observations, optimization decisions, experiments, and measurable outcomes to synthesize evidence-backed recommendations through continuous learning.

---

## Technical Foundation & Architecture

### Biomimetic Memory Loop
```text
CURRENT SEO DATA + HISTORICAL SEO MEMORY
                     │
                     ▼
             RECALL (Hindsight)
                     │
                     ▼
            HISTORICAL EVIDENCE
                     │
                     ▼
            REFLECT (Hindsight)
                     │
                     ▼
       CONTEXT-AWARE RECOMMENDATION
                     │
                     ▼
              HUMAN APPROVAL
                     │
                     ▼
              SEO EXPERIMENT
                     │
                     ▼
             MEASURE OUTCOME
                     │
                     ▼
            RETAIN (Hindsight)
                     │
                     ▼
         FUTURE RECOMMENDATIONS IMPROVE
```

### Core Architecture Components
* **Backend:** FastAPI + Pydantic v2 + Python 3.12
* **Persistent Memory:** Vectorize Hindsight (`hindsight-all` 0.10.1)
* **Embedded Storage:** Embedded PostgreSQL (`pg0`) bundled within `hindsight-all` — **No Docker required**
* **Memory Primitives:**
  * **Retain:** Ingests SEO observations, hypotheses, and experiment outcomes.
  * **Recall:** Multi-modal semantic, keyword, graph, and temporal memory retrieval.
  * **Reflect:** Synthesizes observations and reasons over past experimental results to guide recommendations.
* **LLM Layer:** Provider-agnostic via LiteLLM/Hindsight (supports OpenAI, Gemini, Groq, Anthropic, Ollama, etc.)

---

## Windows Setup & Installation

### Prerequisites
* Windows 10/11 x64
* Python 3.12 (verified with Python 3.12.6)
* Git

> [!NOTE]
> Docker is **not** required. SearchMind leverages Hindsight's native embedded daemon (`pg0-embedded`), which runs locally on Windows without containers.

### 1. Project Directory & Virtual Environment
From the repository root (`C:\Antigravity\searchmind`):

```powershell
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
# Upgrade pip and install pinned dependencies
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Configuration & Environment Variables

Copy the example configuration file:

```powershell
Copy-Item .env.example .env
```

Configure your LLM credentials in `.env`:

```env
# Application Settings
ENVIRONMENT=development
LOG_LEVEL=info
HOST=127.0.0.1
PORT=8000

# Vectorize Hindsight & LLM Configuration
# Supported providers: openai, gemini, groq, anthropic, ollama
HINDSIGHT_API_LLM_PROVIDER=openai
HINDSIGHT_API_LLM_API_KEY=your_actual_api_key_here
HINDSIGHT_API_LLM_MODEL=gpt-4o-mini
HINDSIGHT_API_LLM_BASE_URL=

# Hindsight Database URL (uses embedded pg0 by default)
HINDSIGHT_API_DATABASE_URL=pg0
HINDSIGHT_PROFILE=searchmind
```

> [!IMPORTANT]
> A valid LLM API key is **required** because Hindsight's `reflect` operation and memory engine rely on an LLM to synthesize memories and extract causal links. Never commit `.env` to source control.

---

## Running the Application

### Start the Backend Server
```powershell
# From C:\Antigravity\searchmind\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive documentation is available at:
* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health Endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
* Diagnostic Endpoint: [http://127.0.0.1:8000/api/v1/diagnostic](http://127.0.0.1:8000/api/v1/diagnostic)

---

## Running Tests

### 1. Unit Tests (No LLM API calls required)
Unit tests verify configuration loading, health checks, and error handling without incurring LLM costs:

```powershell
.\.venv\Scripts\python.exe -m pytest -m "not integration" -v
```

### 2. Live Hindsight Smoke Test (Retain → Recall → Reflect)
Once `.env` is populated with a valid LLM API key, run the end-to-end Hindsight verification:

```powershell
.\.venv\Scripts\python.exe -m app.smoke_test
```

Or run via pytest integration suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -m integration -v
```

The smoke test validates:
1. **Embedded Daemon Launch:** Starts local Hindsight daemon (`pg0`) on Windows.
2. **Retain:** Stores test SEO memory in bank `searchmind-smoke-test`.
3. **Recall:** Recalls memories using semantic natural language query.
4. **Reflect:** Asks Hindsight to synthesize reasoning over the retrieved memories.
