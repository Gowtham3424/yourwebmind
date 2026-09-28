# SearchMind Synthetic SEO Dataset

This directory contains the production-grade synthetic SEO dataset generated for **SearchMind** hackathon demonstrations, benchmarking, and persistent memory seeding.

All records are strictly validated against SearchMind's Pydantic domain models defined in `backend/app/models/`.

---

## 1. Domain Context

- **Project ID**: `searchmind-demo-store`
- **Domain URL**: `https://demo-searchmind-store.example`
- **Industry / Vertical**: Outdoor gear, apparel, hiking footwear, and trail running equipment ecommerce store.
- **Data Period**: Historical records spanning June 2026 through September 2026.

---

## 2. Dataset Inventory

The dataset consists of 7 interconnected JSON files with strict foreign-key relationships and temporal consistency:

| File | Records | Domain Model | Purpose |
| :--- | :--- | :--- | :--- |
| `pages.json` | 32 | `WebsiteFact` | Core site taxonomy: home, 5 category/collection pages, 20 product pages, 6 editorial guide pages. |
| `keywords.json` | 105 | Custom schema | High-intent search terms across informational, navigational, commercial, and transactional intents. |
| `rankings.json` | 75 | Custom schema | SERP tracking history across 5 observation dates with realistic trajectories (improving, stable, decaying). |
| `observations.json` | 42 | `SEOObservation` | Empirical issues and opportunities identified by crawlers and ranking monitors (low CTR, rank drops, thin content). |
| `decisions.json` | 22 | `OptimizationDecision` | Concrete strategic choices made in response to observations, capturing hypotheses and proposed diffs. |
| `experiments.json` | 20 | `SEOExperiment` | Controlled A/B trials tracking control vs. treatment changes, start/end dates, and primary KPIs. |
| `outcomes.json` | 20 | `ExperimentOutcome` | Measured empirical results evaluated at or after experiment end dates, classifying performance. |

---

## 3. Experiment Outcome Balance

SearchMind avoids dogmatic or "always positive" SEO assumptions. The 20 experiments reflect the reality of organic search testing:

| Outcome Class | Count | Percentage | Real-World SEO Dynamic |
| :--- | :--- | :--- | :--- |
| **Positive** | 6 | 30% | Clear gains in CTR or rankings (e.g., adding purchase intent to product titles, schema markup). |
| **Negative** | 5 | 25% | Performance regressions (e.g., keyword stuffing in H1s, removing buyer FAQs, title truncation). |
| **Neutral** | 5 | 25% | No statistically significant difference (e.g., minor meta description wording, image alt text tweaks). |
| **Inconclusive**| 4 | 20% | High SERP volatility or external seasonal shifts masking signal. |

---

## 4. Cross-Entity Integrity & Chronology

All records adhere to strict relational and temporal constraints:
1. **URL Consistency**: Every URL referenced in `rankings.json`, `observations.json`, `decisions.json`, and `experiments.json` exists in `pages.json`.
2. **Observation Links**: Every decision references valid `observation_ids`.
3. **Experiment Links**: Every outcome references a valid `experiment_id`.
4. **Temporal Ordering**:
   $$\text{start\_date} \le \text{end\_date} \le \text{measured\_at}$$
   Experiments ran between June and September 2026, and all outcomes were measured on or after the experiment completion date.

---

## 5. Hindsight Memory Ingestion

To feed Vectorize Hindsight's episodic and semantic memory, `backend/app/seo/demo_dataset.py` transforms the 20 experiments into rich narrative case studies:

- **Format**:
  - Context & baseline metrics
  - Tested optimization (control vs. treatment diff)
  - Observed quantitative results
  - Empirical outcome classification (`POSITIVE`, `NEGATIVE`, `NEUTRAL`, `INCONCLUSIVE`)
  - Nuanced, context-bound SEO interpretation
- **Memory Bank**: `searchmind-demo`
- **Idempotency**: Retained with unique `document_id=seo_{exp_id}` and `update_mode="replace"`.

---

## 6. CLI Usage

### Dry-Run Validation (No external APIs / no tokens used)
```powershell
python -m app.seeding.demo --dry-run
```

### Full Ingestion into Hindsight Memory Bank
```powershell
python -m app.seeding.demo --bank searchmind-demo
```

### Run Deterministic Unit Tests
```powershell
pytest tests/test_demo_dataset.py -v
```
