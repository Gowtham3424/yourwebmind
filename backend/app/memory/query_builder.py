"""Deterministic memory query builder for SearchMind SEO Agent.

Translates current page context, diagnostic findings, and optimization technique
into structured natural language queries for Hindsight Recall without requiring an LLM.
"""

from typing import Optional


def build_memory_query(
    page_type: Optional[str] = None,
    search_intent: Optional[str] = None,
    target_keyword: Optional[str] = None,
    observation_type: Optional[str] = None,
    technique: Optional[str] = None,
) -> str:
    """
    Construct a targeted, deterministic natural language query for Hindsight Recall.

    Rules:
    - Normalizes technique names ('title_tag_test' -> 'title tag optimization')
    - Combines page type and search intent qualifiers ('commercial product pages')
    - Incorporates keyword specificity or diagnostic context when present
    """
    # 1. Normalize technique label
    t = (technique or "optimization").lower().replace("_", " ").strip()
    if "test" in t:
        t = t.replace("test", "optimization").strip()
    if not t.endswith("optimization") and not t.endswith("addition") and not t.endswith("changes"):
        t = f"{t} optimization"

    # 2. Page type qualifier
    pt = (page_type or "page").lower().strip()
    if pt in ("product", "category", "guide"):
        pt_str = f"{pt} pages"
    elif pt == "homepage":
        pt_str = "the homepage"
    else:
        pt_str = "pages"

    # 3. Intent qualifier
    intent = (search_intent or "").lower().strip()
    context_str = f"{intent} {pt_str}" if intent else pt_str

    # 4. Construct base query
    if target_keyword:
        kw = target_keyword.strip()
        query = f"What happened when {t} was tested on {context_str} for '{kw}'?"
    elif observation_type and "ctr" in observation_type.lower():
        query = f"What happened in past experiments involving {t} to improve CTR on {context_str}?"
    else:
        query = f"What happened in past experiments involving {t} on {context_str}?"

    return query
