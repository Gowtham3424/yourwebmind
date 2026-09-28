# SearchMind

> "An SEO agent that remembers what happened, learns what worked, and gets smarter over time."

SearchMind is an SEO intelligence agent powered by **Vectorize Hindsight** persistent memory. Rather than performing stateless, one-off audits, SearchMind retains observations, optimization hypotheses, controlled A/B experiments, and measurable empirical outcomes to synthesize contextual, evidence-backed recommendations through continuous learning.

---

## Why SearchMind

### The Problem with Traditional SEO Tooling
Conventional SEO software (crawlers, rank trackers, keyword explorers) provides rich diagnostic snapshots of the current moment:
* A rank tracker detects that organic CTR dropped on a high-ranking product page.
* A crawler flags a meta description as truncated or a title as non-optimal.
* A standard LLM assistant suggests a generic best-practice title tag based solely on public web training data.

What is missing is **organizational memory**:
* *Did the team already test a title tag rewrite on this category page three months ago?*
* *Did aggressive promotional wording increase clicks or trigger brand distrust and CTR decline?*
* *How did search intent alignment perform on commercial product pages versus top-of-funnel informational guides?*

Without persistent experiential memory, SEO teams repeatedly make the same mistakes, discard hard-won lessons across team turnover, and rely on dogmatic "best practices" that frequently fail in specific commercial contexts.

### The SearchMind Solution
SearchMind treats SEO as an **empirical, experimental science governed by contextual precedent**:
1. **Persistent Memory:** Stores every observation, decision, experiment, and measured metric delta in Vectorize Hindsight.
2. **Contextual Retrieval:** Recalls past experiments from comparable page types and search intents before formulating an action.
3. **Evidence-Based Reasoning:** Weighs positive, negative, neutral, and inconclusive precedents to identify what worked and what backfired.
4. **Human-in-the-Loop Gateway:** Enforces operator review and explicit approval before any experiment can be created or executed.
5. **Continuous Learning:** When an experiment completes, the measured outcome and contextual lesson are retained into Hindsight, making future recommendations progressively smarter.

> [!NOTE]
> **Scope & Realistic Expectations:**
> SearchMind does not claim to replace established enterprise rank trackers or crawlers, nor does it assert universal SEO causality. SEO algorithms are dynamic external systems influenced by competition and seasonal shifts. SearchMind provides **contextual precedent intelligence** to replace blind guesswork with documented historical evidence.

---

## The Core Differentiator

Most AI-assisted SEO tools operate as simple, stateless pipelines:

```text
CURRENT SEO DATA ──► [ GENERIC LLM PROMPT ] ──► "BEST PRACTICE" RECOMMENDATION
```

This stateless approach has no memory of past failures and treats all websites and page types identically.

### SearchMind's 10-Stage Biomimetic Memory Loop

SearchMind implements a closed-loop evidence architecture:

```text
CURRENT SEO SIGNAL (Rank 3.1, CTR drop -1.40 pp on Product Page)
         │
         ▼
HINDSIGHT RECALL (Semantic & lexical search across historical memory)
         │
         ▼
RELEVANT PRECEDENTS (2 Positive, 3 Negative, 2 Neutral, 2 Inconclusive)
         │
         ▼
CONTEXTUAL REASONING (Synthesize supporting evidence, conflicting evidence & caveats)
         │
         ▼
RECOMMENDATION (Front-load primary keyword, maintain brand, exclude discounts; Confidence: 0.57)
         │
         ▼
HUMAN APPROVAL GATEWAY (Enforced operator review: PENDING_APPROVAL ──► APPROVED / REJECTED)
         │
         ▼
CONTROLLED EXPERIMENT (Controlled 4-week trial tracking CTR & Clicks against baseline)
         │
         ▼
MEASURED OUTCOME (Empirical result: CTR 1.80% ──► 2.70%, +50.0% uplift, POSITIVE)
         │
         ▼
HINDSIGHT RETAIN (Factual lesson, context, and caveats ingested into persistent memory)
         │
         ▼
FUTURE RECOMMENDATIONS IMPROVE (Precedent is recalled for subsequent optimization decisions)
```

### Contextual Specificity vs. Dogmatic Rules
Historical SEO experiments in SearchMind are classified into four balanced empirical categories:
* **Positive Precedents:** Demonstrated measurable uplift under specific intent and page conditions.
* **Negative Precedents (Cautionary Lessons):** Optimization tactics that harmed rankings, clicks, or conversion (e.g., aggressive discount keywords degrading brand trust).
* **Neutral Precedents:** Changes whose variance fell within normal SERP noise without significant impact.
* **Inconclusive Precedents:** Experiments confounded by external seasonality or concurrent algorithm updates.

SearchMind explicitly surfaces conflicting evidence and contextual caveats rather than declaring any single experiment outcome a universal rule.

---

## Operating Modes

SearchMind is architected with a strict separation between its **Evaluator Demo Mode** and its **Live Hindsight Verification Mode**:

| Attribute | Offline Evaluator Demo Mode (`SEARCHMIND_DEMO_MODE=true`) | Live Hindsight Verification Mode (`SEARCHMIND_DEMO_MODE=false`) |
| :--- | :--- | :--- |
| **Purpose** | Deterministic, zero-token local evaluation for hackathon judges | Live integration verification of real Retain, Recall, and Reflect operations |
| **LLM Provider** | None (0 external API requests) | Google Gemini (`gemini-3.5-flash-lite`) via native `hindsight-all` |
| **Memory Engine** | In-memory adapters populated from `data/demo/` | Live `HindsightEmbedded` daemon on embedded PostgreSQL (`pg0`) |
| **Memory Bank** | Reads `searchmind-demo` fixtures (133 persistent memory units intact) | Verified on isolated test bank (`searchmind-live-test`) |
| **Token Cost** | **Zero tokens**; fully immune to rate limits and 429 exhaustion | Minimal API calls (strictly 2 calls during full lifecycle test) |
| **Network Need** | Completely offline | Requires valid outbound network access and Gemini API key |

---

## Recommended Demo Flow (Evaluator Walkthrough)

Follow this 12-step sequence to evaluate SearchMind's evidence-based learning loop:

### Step 1: Launch in Offline Demo Mode
Ensure `SEARCHMIND_DEMO_MODE=true` in `backend/.env` (default state), then start the backend:
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Step 2: Open the Evaluator Workbench
Open your browser and navigate to:
```
http://127.0.0.1:8000/app
```
Confirm the editorial workbench renders with the `DEMO DATA` disclosure badge visible in the navigation bar.

### Step 3: Inspect the Current SEO Signal
Observe Section 1 (`CURRENT SEO SIGNAL`):
* **Page:** `Waterproof Alpine Hiking Boots` (`/products/waterproof-alpine-hiking-boots`)
* **Search Intent:** `Commercial`
* **SERP Ranking:** `3.1` (top-3 position maintained)
* **CTR Decline:** `1.80%` down from `3.20%` (`-1.40 pp` delta)
* **Observed Clicks:** `277` clicks from `15,400` impressions

### Step 4: Examine Historical Memory & Relevant Precedents
Observe Section 2 (`HISTORICAL MEMORY`):
* Displays **9 relevant historical experiments** retrieved from memory.
* Balanced empirical distribution: **2 Positive, 3 Negative, 2 Neutral, 2 Inconclusive**.
* Surfaces direct conflicting evidence: `EXP_014` saw a `-20.1%` CTR drop when discount modifiers were added to trekking boots.

### Step 5: Review Contextual Reasoning & Caveats
Observe Section 3 (`WHAT SEARCHMIND LEARNED`):
* **Precedent Synthesis:** Explains that keyword-first commercial alignment reliably recovered CTR on comparable product pages, whereas discount modifiers degraded performance.
* **Notice:** Truthfully indicates `Reasoning synthesized via deterministic contextual precedent evaluation.`
* **Contextual Caveat:** Emphasizes that historical outcomes are contextual to observed templates and seasonal intent, not universal laws.

### Step 6: Review the Recommendation & Bounded Confidence
Observe Section 4 (`RECOMMENDATION & APPROVAL GATEWAY`):
* **Action:** Proposes revising the title tag to front-load "waterproof hiking boots", retain brand identity, and strictly avoid aggressive discount modifiers.
* **Bounded Confidence:** Displays `0.57 (Bounded between 0.10 and 0.85 per deterministic evidence rules)`.
* **Impact Estimate:** Projected `+15% to +30% CTR` recovery.

### Step 7: Observe the Human Approval Gateway
Notice the prominent status badge:
```
PENDING APPROVAL
```
The `[Run Controlled Experiment]` button is disabled. SearchMind strictly blocks autonomous experiment execution without operator consent.

### Step 8: Grant Operator Approval
1. Enter an optional operator note in the input field:
   `"Approved keyword-first title test. Exclude aggressive discount phrasing."`
2. Click **`[Approve Recommendation]`**.
3. Observe the immediate transition to green `APPROVED` status with timestamp and recorded note.
4. The **`[Run Controlled Experiment]`** action button is now unlocked.

### Step 9: Execute the Controlled Experiment
Click **`[Run Controlled Experiment]`**:
* Simulates the 4-week controlled A/B measurement period.
* **Measured CTR:** `1.80%` baseline moves to `2.70%` (`+0.90 pp` absolute change).
* **Relative Lift:** `+50.0%` organic CTR improvement.
* **Outcome Classification:** Validated as `POSITIVE`.

### Step 10: Verify Memory Retention (Retained Lesson)
Observe Section 6 (`MEMORY UPDATED (RETAINED LESSON)`):
* Displays the structured lesson retained for future cycles.
* **Memory Document ID:** `seo_exp_021_demo`
* **Verification Confirmation:** Confirms future recall queries on commercial hiking boot pages will now incorporate `exp_021` as a positive precedent.

### Step 11: Explore the Memory Browser
Scroll down to Section 7 (`SEARCH DEMO SEO MEMORY`):
* Search across the 20 historical SEO experiment records using the search bar or filter pills (`Positive (5)`, `Negative (6)`, `Neutral (4)`, `Inconclusive (5)`).
* Search for `"waterproof hiking boots"` to inspect the exact historical precedent cards that influenced the recommendation.

### Step 12: Reset Session to Initial State
Click the **`[Reset Demo]`** button in the top navigation bar.
* Verifies `POST /api/v1/agent/reset`.
* Returns the in-memory session cleanly to the initial `PENDING APPROVAL` state without altering the underlying persistent database.

---

## Technical Foundation & Architecture

### Core Components
* **Backend Framework:** FastAPI + Pydantic v2 (Python 3.12)
* **Persistent Memory Engine:** Vectorize Hindsight (`hindsight-all==0.10.1`)
* **Storage Daemon:** Native Windows embedded PostgreSQL (`pg0` / `pg0-embedded 0.15.2`) — **No Docker required**
* **Frontend:** Minimalist vanilla JavaScript + CSS editorial workbench (zero external frameworks, zero CDNs)
* **Domain Model:** Falsifiable relational entities (`WebsiteFact`, `SEOObservation`, `OptimizationDecision`, `SEOExperiment`, `ExperimentOutcome`, `SEORecommendation`)

### Live Hindsight Verification

SearchMind's live Hindsight integration was independently verified using the Google Gemini provider:

* **Provider:** `gemini` (via native `hindsight-all` provider engine)
* **Model:** `gemini-3.5-flash-lite`
* **Storage:** Embedded PostgreSQL (`pg0`) on Windows x64
* **Verified Operations:**
  * **Daemon Init:** Initialized embedded Hindsight daemon and verified database connectivity.
  * **Retain:** Successfully stored structured memory into an isolated test bank (`searchmind-live-test`).
  * **Recall:** Successfully executed natural language semantic recall against the stored memory.
  * **Reflect:** Successfully synthesized qualitative reflection reasoning over the memory bank.
* **Demo Bank Integrity:** The validated 20-experiment demo bank (`searchmind-demo`) was strictly preserved and remains intact at exactly **133 persistent memory units**.

To run the single, isolated live integration test against Gemini:
```powershell
# From backend/ with HINDSIGHT_API_LLM_API_KEY set in .env
[Environment]::SetEnvironmentVariable('SEARCHMIND_DEMO_MODE', 'false')
.\.venv\Scripts\python.exe -m pytest tests/test_hindsight_integration.py -v
```

---

## Verification & Test Suite

SearchMind maintains a comprehensive deterministic test suite providing zero-token verification across all domain models, adapters, audit rules, and API endpoints:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -m "not integration" -v
```

* **Test Suite Status:** **118 passed, 1 deselected** (the single deselected test is the optional live integration test).
* **Token Cost:** **0 tokens consumed**.
* **Duration:** ~25–65s depending on CPU disk I/O.

### Verified Test Categories
1. `test_models.py` (20 tests): Pydantic v2 validation, schema constraints, serialization, and enum boundaries.
2. `test_demo_dataset.py` (12 tests): Cross-reference integrity, temporal coherence, and metric validation across synthetic dataset.
3. `test_seo_agent.py` (14 tests): Evidence extraction, precedent matching, bounded confidence calculations, and approval gating.
4. `test_memory_integration.py` (9 tests): In-memory recall adapters, query variations, and provenance extraction.
5. `test_memory_reflect.py` (12 tests): Contextual synthesis, reflection fallbacks, and non-dogmatic sanitization.
6. `test_experiments_learning.py` (20 tests): State transitions, outcome classification, metric deltas, and retention payloads.
7. `test_audit_and_fallback.py` (10 tests): Fallback resilience, immutability, zero-baseline safety, and approval enforcement.
8. `test_config.py` (4 tests): Configuration loading, placeholder key rejection, and demo mode toggling.
9. `test_health.py` (3 tests): Health endpoint status reporting in demo and live states.
10. `test_agent_api.py` (6 tests): End-to-end API lifecycle, approval gating, and memory browser endpoints.
11. `test_qa_flow.py` (8 tests): Complete evaluator flow QA, security scanning (no secret leaks), and error handling without stack traces.

---

## Deployment Readiness & Constraints

* **Stateful Embedded Database (`pg0-embedded`):** Vectorize Hindsight operates on a native embedded PostgreSQL instance that binds locally to port 5432 and stores memory units on disk.
* **Persistent Host Requirement:** SearchMind is designed for local evaluation, dedicated VMs, or persistent container environments (e.g., Docker with mounted persistent volumes, AWS EC2, GCP Compute Engine).
* **Stateless Serverless Incompatibility:** Due to the local process daemon requirements of embedded `pg0`, SearchMind cannot be deployed to stateless ephemeral platforms (e.g., AWS Lambda, Vercel Serverless) without configuring an external managed PostgreSQL database via `HINDSIGHT_API_DATABASE_URL`.
* **Production Deployment Path:** For cloud production deployments, point `HINDSIGHT_API_DATABASE_URL` to an external PostgreSQL instance (AWS RDS, Supabase, Cloud SQL) and run FastAPI via standard ASGI container infrastructure.

---

## Project Structure

```text
searchmind/
├── data/
│   └── demo/                      # Synthetic e-commerce SEO benchmark dataset
│       ├── pages.json             # 32 catalog and content pages
│       ├── keywords.json          # 105 tracked search terms
│       ├── rankings.json          # 75 historical SERP measurements
│       ├── observations.json      # 42 diagnostic signal records
│       ├── decisions.json         # 22 optimization proposals
│       ├── experiments.json       # 20 controlled SEO A/B trials
│       └── outcomes.json          # 20 empirical results (balanced distribution)
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint, lifespan manager, static routes
│   │   ├── config.py              # Pydantic Settings & environment management
│   │   ├── smoke_test.py          # Retain -> Recall -> Reflect verification runner
│   │   ├── api/
│   │   │   ├── health.py          # /health status endpoint
│   │   │   ├── diagnostic.py      # /api/v1/diagnostic runtime inspection
│   │   │   └── agent.py           # /api/v1/agent & /api/v1/memory endpoints
│   │   ├── models/                # Pydantic v2 domain schemas (WebsiteFact, SEOExperiment, etc.)
│   │   ├── services/
│   │   │   └── hindsight_service.py # HindsightEmbedded client lifecycle management
│   │   ├── agents/                # SEOWorkflowEngine, HistoricalAnalyzer, RecommendationEngine
│   │   ├── memory/                # In-memory Recall, Reflect, and Retain adapters
│   │   ├── experiments/           # ExperimentExecutionService & metric calculators
│   │   ├── seo/                   # Demo dataset loader and validator
│   │   ├── seeding/               # Hindsight bank ingestion utility
│   │   └── static/                # Minimalist editorial evaluator workbench (HTML/JS/CSS)
│   ├── tests/                     # 119-test automated pytest suite
│   ├── pytest.ini                 # Pytest configuration with integration marker
│   ├── requirements.txt           # Pinned Python dependencies
│   ├── .env.example               # Example configuration template
│   └── .env                       # Local configuration (strictly ignored by Git)
├── README.md                      # Comprehensive submission documentation
└── .gitignore                     # Git ignore rules protecting secrets and virtual environment
```

---

## License & Disclosures

* **Hackathon Submission:** Built for the Vectorize Hindsight Hackathon.
* **Persistent Memory Engine:** Powered by Vectorize Hindsight (`hindsight-all`).
* **Synthetic Data Disclosure:** All keyword rankings, URLs, traffic statistics, and experiment outcomes in `data/demo/` represent a synthetic e-commerce benchmark created solely for consistent, auditable demonstration and testing.
