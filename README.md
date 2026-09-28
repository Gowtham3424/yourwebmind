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

## SearchMind Domain Model

SearchMind models the SEO decision lifecycle as a structured, evidence-grounded pipeline:

```text
WebsiteFact
    ↓
SEOObservation
    ↓
OptimizationDecision
    ↓
SEOExperiment
    ↓
ExperimentOutcome
    ↓
Hindsight Retain
    ↓
Future Recall / Reflect
    ↓
SEORecommendation
```

### Domain Schema Definitions
* **`WebsiteFact`**: Represents the current factual page state (URL, page type, title, meta description, keywords, search intent, word count, canonical URL, indexability, status code).
* **`SEOObservation`**: Represents empirical, measurable SEO signals and diagnostic findings (metric delta, severity levels `info`/`low`/`medium`/`high`/`critical`, and raw evidence rather than an arbitrary universal score).
* **`OptimizationDecision`**: Represents a concrete decision and falsifiable hypothesis proposed in response to SEO observations.
* **`SEOExperiment`**: Represents a controlled test with baseline metrics, control/treatment definitions, primary/secondary metrics, and start/end dates.
* **`ExperimentOutcome`**: Represents the observed empirical result (absolute and percentage changes, confidence notes, and outcome classification: `positive`, `negative`, `neutral`, `inconclusive`).
* **`SEORecommendation`**: The structured output produced for SEO teams, cleanly separating:
  1. **Current Evidence**: What is happening right now in the data?
  2. **Historical Evidence**: What happened previously in relevant experiment contexts? (Optional for new projects with zero memory).
  3. **Reflection**: What does Hindsight infer/synthesize from those memories?
  4. **Recommendation**: What concrete action is being proposed?

> [!IMPORTANT]
> **Evidence-Grounding & Contextual Specificity:**
> SearchMind does not treat SEO as static universal rules. A single experiment outcome is an empirical data point within a specific context, not proof that a strategy will universally succeed. The agent preserves measured metrics, confidence bounds, and caveats to distinguish observed correlation from proven causation.

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

---

## Synthetic SEO Dataset & Demo Memory Seeding

SearchMind includes an e-commerce SEO benchmark dataset under `data/demo/` representing 4 months (June–September 2026) of search performance for an outdoor gear brand (`searchmind-demo-store`).

### Dataset Overview
* **Pages (`pages.json`):** 32 URLs across homepage, categories, products, and buyer guides.
* **Keywords (`keywords.json`):** 105 tracked search terms spanning informational, commercial, and transactional search intents.
* **Rankings (`rankings.json`):** 75 SERP tracking measurements across 5 historical dates.
* **Observations (`observations.json`):** 42 empirical diagnostic signals (CTR dips, ranking gains, thin content).
* **Decisions (`decisions.json`):** 22 optimization proposals with hypotheses and proposed code/content changes.
* **Experiments (`experiments.json`):** 20 controlled SEO A/B trials tracking control vs. treatment implementations.
* **Outcomes (`outcomes.json`):** 20 measured results with balanced empirical distribution (6 positive, 5 negative, 5 neutral, 4 inconclusive).

### Seeding Hindsight Memory
The synthetic dataset can be ingested directly into Hindsight to provide persistent episodic and semantic memory:

```powershell
# Ingest 20 experiment narratives into the 'searchmind-demo' memory bank:
.\.venv\Scripts\python.exe -m app.seeding.demo

# Dry-run validation only (no external API calls):
.\.venv\Scripts\python.exe -m app.seeding.demo --dry-run

# Run dataset unit tests (strictly deterministic):
.\.venv\Scripts\python.exe -m pytest tests/test_demo_dataset.py -v
```

---

## SearchMind Agent Core & Workflow Engine

SearchMind's SEO Agent coordinates evidence-based diagnostic analysis and context-aware optimization decisions through a deterministic, human-in-the-loop workflow:

```text
CURRENT SEO DATA
        ↓
HINDSIGHT RECALL (Semantic & Keyword Memory Search)
        ↓
HISTORICAL CONTEXT (Local Deterministic Analyzer)
        ↓
OPTIONAL HINDSIGHT REFLECT (Thematic Reasoning & Cross-Experiment Synthesis)
  └─► Graceful Fallback to Local Analysis if Quota Blocked or Offline
        ↓
CONTEXT-AWARE RECOMMENDATION
        ↓
HUMAN APPROVAL GATEWAY (requires_approval = True)
        ↓
PLANNED EXPERIMENT PROPOSAL
        ↓
MEASURED OUTCOME & LESSON
        ↓
HINDSIGHT RETAIN (Idempotent update_mode="replace")
```

### Strict Separation of Evidence & Reasoning
SearchMind strictly distinguishes five cognitive components:
1. **Current Evidence:** Observable, empirical present-state measurements (SERP position, organic CTR, impression/click volumes, diagnostic observations, severity). Missing data is explicitly marked as unavailable rather than fabricated.
2. **Historical Evidence:** Recalled experiment records and measured outcomes from past trials on similar page types and search intents, categorized into positive, negative, neutral, and inconclusive precedents.
3. **Local Historical Analysis:** Deterministic, non-dogmatic rule-based precedent analysis and initial reflection narrative based on confirmed historical outcomes.
4. **Hindsight Reflect (Optional Reasoning Enhancement):** Qualitative cross-experiment synthesis identifying thematic patterns, supporting evidence, conflicting evidence, and external caveats across retrieved precedents. Reflect is strictly non-dogmatic (never asserts universal rules) and falls back safely to local analysis if the provider is unavailable or quota is exhausted.
5. **Recommendation & Bounded Confidence:** An actionable, falsifiable optimization proposal with bounded, explainable confidence (`0.10` to `0.85`), expected impact, and an enforced human approval requirement (`requires_approval = True`). Deterministic confidence calculations remain authoritative and are never overridden by LLM reflection.

### Decision Rules
* **Rule A (Opportunity):** When CTR declines and relevant historical title precedents exist, propose a targeted title optimization trial.
* **Rule B (Mixed Evidence):** When past trials show both positive and negative results, avoid declaring the technique proven and prescribe strict brand/intent guardrails.
* **Rule C (Precedent Caution):** When precedents are predominantly negative, surface past failures and recommend caution or alternative on-page enhancements.
* **Rule D (Inconclusive Precedent):** When past data was confounded by external factors (e.g. algorithm rollouts), propose a controlled measurement trial rather than guaranteed gains.
* **Rule E (Contextual Divergence):** When page types or intents differ between precedents and the current target, reduce confidence and explicitly state the contextual difference.
* **Rule F (Zero Precedent):** When no relevant experiments exist in memory, state that historical precedent is unavailable without inventing false confidence.

### Optional Reflect Fallback Guarantee
SearchMind's core workflow treats Hindsight Reflect as an optional reasoning enhancement, never as a single point of failure:
- **No Extra Recall:** Reflect consumes already-retrieved memories as context, eliminating redundant network requests.
- **Fail-Safe Fallback:** If Reflect fails, times out, or encounters a 429 quota exhaustion, the engine logs a warning and proceeds uninterrupted using deterministic local analysis.
- **Non-Dogmatic Guardrails:** Reflection text is automatically sanitized to prevent over-generalized assertions ("always increases", "guarantees") from polluting recommendations.
- **Authoritative Confidence:** Confidence scores are strictly computed by deterministic rules and cannot be inflated by reflection narrative.

### Token Conservation Policy
During ordinary test execution and agent workflow development, SearchMind executes all analysis, retrieval, and decision rules deterministically in local memory with zero external LLM calls. Live Hindsight/Groq calls are preserved for persistent memory storage and milestone integration tests.

### Running the Deterministic SEO Agent Demo & Evaluator Frontend
```powershell
# From the backend directory:
cd backend

# Option A: Start the FastAPI server and open the Evaluator Frontend:
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Open http://localhost:8000 or http://127.0.0.1:8000 in your browser.

# Option B: Execute the zero-token CLI learning loop demo runner:
.\.venv\Scripts\python.exe -m app.agents.demo_scenario

# Run the complete test suite (108 passed, 0 tokens consumed):
.\.venv\Scripts\python.exe -m pytest -v -m "not integration"

# Run frontend agent API tests specifically:
.\.venv\Scripts\python.exe -m pytest tests/test_agent_api.py -v
```

---

## Evaluator Frontend Architecture & Design System

The SearchMind frontend is a minimal, evidence-first editorial workbench built for hackathon evaluators. Adhering to the principle **“Results speak more than design”**, the UI prioritizes empirical clarity over decorative noise.

### Design Language & Standards
* **Palette:** Crisp off-white (`#fcfcfc`), dark charcoal typography (`#111111`), and subtle 1px gray borders (`#e5e5e5`).
* **Zero Decorative Noise:** Strictly zero gradients, glassmorphism, glowing cards, neon colors, excessive shadows, or bloated CSS frameworks.
* **Restrained Status Badges:** Accessible, subtle borders and background tints for `Positive` (green), `Negative` (crimson), `Neutral` (slate), and `Inconclusive` (amber).
* **Zero-Token Demo Mode:** Operates completely client-to-server locally using deterministic fixture data and in-memory adapters with zero external Groq token consumption.

### Primary Workspace Sections
1. **The Learning Loop (10-Stage Workflow Indicator):**
   `CURRENT DATA` → `RECALL` → `HISTORICAL EVIDENCE` → `REFLECT` → `RECOMMEND` → `APPROVAL` → `EXPERIMENT` → `OUTCOME` → `RETAIN` → `FUTURE LEARNING`
2. **Current SEO Signal:** Displays URL, commercial search intent, top-3 SERP rank (3.1), and CTR decline (-1.40 pp).
3. **Historical Evidence:** Compact summary of relevant precedents (2 positive, 3 negative, 2 neutral, 2 inconclusive) with unfiltered conflicting evidence.
4. **What SearchMind Learned:** Contextual precedent synthesis quote, supporting evidence (`exp_001`), conflicting evidence (`exp_014`), and contextual caveats.
5. **Recommendation & Human Approval Gateway:** Context-aware trial proposal with bounded confidence (0.57) and enforced approval gateway (`PENDING APPROVAL` → `APPROVED` / `REJECTED`). Autonomous experiment execution is strictly blocked.
6. **Controlled Experiment Execution:** Activated only when the operator explicitly clicks `[Run Controlled Experiment]`. Reports empirical metric movements (`+0.90 pp (+50.0%) CTR`) and outcome (`POSITIVE`).
7. **Memory Updated (Retained Lesson):** Shows retained factual lesson, context, caveat, Hindsight document ID (`seo_exp_021_demo`), and future recall verification confirmation.
8. **Memory Browser:** Interactive search and filtering tool across historical SEO experiments in Hindsight memory.



