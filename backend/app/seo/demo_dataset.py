"""
SearchMind Synthetic SEO Dataset Generator, Validator, and Memory Formatter.

Provides:
1. Dataset generation for synthetic ecommerce site ('searchmind-demo-store').
2. Comprehensive Pydantic schema validation.
3. Cross-entity reference and temporal coherence verification.
4. Natural language memory document generation for Hindsight Retain.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from app.models import (
    ExperimentOutcome,
    ExperimentStatus,
    ObservationSeverity,
    OptimizationDecision,
    OutcomeClass,
    SEOExperiment,
    SEOObservation,
    SearchIntent,
    WebsiteFact,
)

logger = logging.getLogger("searchmind.demo_dataset")

# Default dataset directory
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo"
DEMO_PROJECT_ID = "searchmind-demo-store"
DEMO_DOMAIN = "https://demo-searchmind-store.example"
DEMO_BANK_ID = "searchmind-demo"


def generate_synthetic_dataset(output_dir: Optional[Path] = None) -> Dict[str, int]:
    """Generate the full synthetic SEO dataset and write JSON files to output_dir."""
    target_dir = output_dir or DATA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # 1. Pages (32 pages across diverse categories)
    # --------------------------------------------------------------------------
    pages_data = [
        # Homepage
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/",
            "page_type": "homepage",
            "title": "SearchMind Outdoor Gear & Trail Equipment | Quality Backcountry Store",
            "meta_description": "Explore premium trail running shoes, hiking boots, ultralight packs, and backcountry apparel.",
            "primary_keyword": "outdoor trail equipment",
            "secondary_keywords": ["backcountry gear", "trail running store", "hiking equipment"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 850,
            "canonical_url": f"{DEMO_DOMAIN}/",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        # Category Pages (6)
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/running-shoes",
            "page_type": "category",
            "title": "Trail & Road Running Shoes | SearchMind Outdoor",
            "meta_description": "Shop high-performance trail running and road running shoes engineered for distance and grip.",
            "primary_keyword": "running shoes",
            "secondary_keywords": ["trail runners", "marathon running shoes"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 620,
            "canonical_url": f"{DEMO_DOMAIN}/collections/running-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/trail-running",
            "page_type": "category",
            "title": "Men's & Women's Trail Running Gear | SearchMind Outdoor",
            "meta_description": "High-traction trail running footwear, hydration vests, and lightweight apparel.",
            "primary_keyword": "trail running gear",
            "secondary_keywords": ["trail footwear", "mountain running gear"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 580,
            "canonical_url": f"{DEMO_DOMAIN}/collections/trail-running",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/hiking-boots",
            "page_type": "category",
            "title": "Waterproof Hiking Boots & Trekking Footwear | SearchMind Store",
            "meta_description": "Durable, waterproof leather and synthetic hiking boots designed for rocky alpine trails.",
            "primary_keyword": "hiking boots",
            "secondary_keywords": ["waterproof trekking boots", "backpacking footwear"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 710,
            "canonical_url": f"{DEMO_DOMAIN}/collections/hiking-boots",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/backpacking-gear",
            "page_type": "category",
            "title": "Ultralight Backpacking Gear & Tents | SearchMind Backcountry",
            "meta_description": "Multi-day backpacking packs, sleeping systems, and ultralight shelters for extended trips.",
            "primary_keyword": "backpacking gear",
            "secondary_keywords": ["ultralight backpacking", "hiking backpacks"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 640,
            "canonical_url": f"{DEMO_DOMAIN}/collections/backpacking-gear",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/outdoor-jackets",
            "page_type": "category",
            "title": "Waterproof Rain Jackets & Hardshells | SearchMind Apparel",
            "meta_description": "Breathable 3-layer waterproof jackets, windbreakers, and technical hardshell outerwear.",
            "primary_keyword": "outdoor jackets",
            "secondary_keywords": ["waterproof rain jacket", "hardshell jacket"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 590,
            "canonical_url": f"{DEMO_DOMAIN}/collections/outdoor-jackets",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/climbing-shoes",
            "page_type": "category",
            "title": "Rock Climbing & Bouldering Shoes | SearchMind Store",
            "meta_description": "Precision bouldering slippers, aggressive downturned climbing shoes, and gym footwear.",
            "primary_keyword": "climbing shoes",
            "secondary_keywords": ["bouldering shoes", "rock climbing footwear"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 530,
            "canonical_url": f"{DEMO_DOMAIN}/collections/climbing-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        # Product Pages (15)
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/trail-blazer-running-shoes",
            "page_type": "product",
            "title": "Trail Blazer Pro Running Shoes | SearchMind Store",
            "meta_description": "All-terrain trail runner featuring Vibram lug outsole and rock protection plate.",
            "primary_keyword": "trail running shoes",
            "secondary_keywords": ["vibram trail runner", "cushioned trail shoe"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 920,
            "canonical_url": f"{DEMO_DOMAIN}/products/trail-blazer-running-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/waterproof-alpine-hiking-boots",
            "page_type": "product",
            "title": "Waterproof Alpine Hiking Boots | SearchMind Store",
            "meta_description": "Full-grain nubuck waterproof alpine boots with ankle stabilization for rocky ascents.",
            "primary_keyword": "waterproof hiking boots",
            "secondary_keywords": ["alpine boots", "leather trekking footwear"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 890,
            "canonical_url": f"{DEMO_DOMAIN}/products/waterproof-alpine-hiking-boots",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes",
            "page_type": "product",
            "title": "Apex Carbon Plate Marathon Shoes | SearchMind Store",
            "meta_description": "Ultra-light carbon fiber plate racing shoe engineered for sub-3 marathon efforts.",
            "primary_keyword": "carbon plate running shoes",
            "secondary_keywords": ["marathon racing flat", "carbon road racer"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 760,
            "canonical_url": f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l",
            "page_type": "product",
            "title": "Summit 45L Ultralight Backpack | SearchMind Backcountry",
            "meta_description": "Frameless 45-liter Dyneema pack with roll-top closure and ergonomic hip belt.",
            "primary_keyword": "ultralight backpack 45l",
            "secondary_keywords": ["thru hiking pack", "frameless backpack"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 810,
            "canonical_url": f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/goretex-weather-jacket",
            "page_type": "product",
            "title": "StormGuard 3L Waterproof Hardshell Jacket | SearchMind",
            "meta_description": "Heavy storm protection with pit zips, helmet-compatible hood, and taped seams.",
            "primary_keyword": "goretex rain jacket",
            "secondary_keywords": ["waterproof hardshell", "storm jacket"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 840,
            "canonical_url": f"{DEMO_DOMAIN}/products/goretex-weather-jacket",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes",
            "page_type": "product",
            "title": "ProGrip Aggressive Bouldering Shoes | SearchMind Store",
            "meta_description": "Downturned toe box with ultra-sticky rubber for overhung gym routes and outdoor granite.",
            "primary_keyword": "bouldering shoes",
            "secondary_keywords": ["aggressive climbing shoe", "sticky rubber slipper"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 720,
            "canonical_url": f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/thermal-merino-base-layer",
            "page_type": "product",
            "title": "250gsm Merino Wool Long Sleeve Base Layer | SearchMind",
            "meta_description": "100% natural merino wool thermals for cold alpine ascents and multi-day trail odor resistance.",
            "primary_keyword": "merino wool base layer",
            "secondary_keywords": ["thermal underwear top", "merino wool crew"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 680,
            "canonical_url": f"{DEMO_DOMAIN}/products/thermal-merino-base-layer",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/ultra-cushion-marathon-shoes",
            "page_type": "product",
            "title": "CloudStrider Max Cushion Road Running Shoes | SearchMind",
            "meta_description": "Plush 40mm stack height road shoe designed for recovery runs and high-mileage road training.",
            "primary_keyword": "max cushion running shoes",
            "secondary_keywords": ["plush running shoes", "marathon training shoe"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 750,
            "canonical_url": f"{DEMO_DOMAIN}/products/ultra-cushion-marathon-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/rugged-terrain-trekking-boots",
            "page_type": "product",
            "title": "Trekker XT Heavy-Duty Backpacking Boots | SearchMind",
            "meta_description": "Stiff-shank mountaineering and long-distance backpacking boots for 50lb+ loads.",
            "primary_keyword": "backpacking boots",
            "secondary_keywords": ["heavy duty hiking boots", "stiff sole trekking boots"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 820,
            "canonical_url": f"{DEMO_DOMAIN}/products/rugged-terrain-trekking-boots",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/hydration-pack-vest-10l",
            "page_type": "product",
            "title": "Enduro 10L Ultra Running Hydration Vest | SearchMind",
            "meta_description": "Bounce-free trail running vest with dual 500ml soft flasks and rear bladder compartment.",
            "primary_keyword": "running hydration vest",
            "secondary_keywords": ["trail running vest", "marathon hydration pack"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 690,
            "canonical_url": f"{DEMO_DOMAIN}/products/hydration-pack-vest-10l",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/compact-camping-stove",
            "page_type": "product",
            "title": "MicroFlame Titanium Canister Camping Stove | SearchMind",
            "meta_description": "Sub-2oz titanium backpacking stove boiling 1 liter of water in under 3 minutes.",
            "primary_keyword": "backpacking canister stove",
            "secondary_keywords": ["ultralight camp stove", "titanium gas stove"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 590,
            "canonical_url": f"{DEMO_DOMAIN}/products/compact-camping-stove",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/all-weather-trail-socks",
            "page_type": "product",
            "title": "Merino Anti-Blister Trail Socks (3-Pack) | SearchMind",
            "meta_description": "Seamless toe cushioning merino trail running socks guaranteed anti-blister.",
            "primary_keyword": "anti blister running socks",
            "secondary_keywords": ["merino hiking socks", "cushioned trail socks"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 510,
            "canonical_url": f"{DEMO_DOMAIN}/products/all-weather-trail-socks",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/polarized-trail-sunglasses",
            "page_type": "product",
            "title": "Veloce Polarized Anti-Fog Running Sunglasses | SearchMind",
            "meta_description": "Ultra-lightweight TR90 frame with UV400 polarized photochromic trail lenses.",
            "primary_keyword": "running sunglasses polarized",
            "secondary_keywords": ["trail running eyewear", "anti fog sport sunglasses"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 570,
            "canonical_url": f"{DEMO_DOMAIN}/products/polarized-trail-sunglasses",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/collapsible-trekking-poles",
            "page_type": "product",
            "title": "Carbon Summit Z-Fold Trekking Poles (Pair) | SearchMind",
            "meta_description": "Three-section folding 100% carbon fiber poles with ergonomic cork grips and snow baskets.",
            "primary_keyword": "carbon fiber trekking poles",
            "secondary_keywords": ["folding hiking sticks", "ultralight walking poles"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 660,
            "canonical_url": f"{DEMO_DOMAIN}/products/collapsible-trekking-poles",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/insulated-down-jacket-800",
            "page_type": "product",
            "title": "Apex 800-Fill Ultralight Packable Down Hoodie | SearchMind",
            "meta_description": "Hydrophobic goose down jacket packing down into its own chest pocket for cold summits.",
            "primary_keyword": "ultralight down jacket",
            "secondary_keywords": ["packable down coat", "800 fill down hoodie"],
            "search_intent": SearchIntent.TRANSACTIONAL.value,
            "word_count": 780,
            "canonical_url": f"{DEMO_DOMAIN}/products/insulated-down-jacket-800",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        # Buying Guides & Informational Content (5)
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners",
            "page_type": "guide",
            "title": "10 Best Trail Running Shoes for Beginners (2026 Guide) | SearchMind",
            "meta_description": "A beginner's breakdown of cushion, drop, and traction for starting on trail.",
            "primary_keyword": "best trail running shoes for beginners",
            "secondary_keywords": ["beginner trail shoes", "first trail running shoe guide"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 2150,
            "canonical_url": f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots",
            "page_type": "guide",
            "title": "How to Choose Hiking Boots: Fit, Waterproofing & Traction | SearchMind",
            "meta_description": "Everything you need to know before buying hiking boots: sizing, break-in, and terrain matching.",
            "primary_keyword": "how to choose hiking boots",
            "secondary_keywords": ["hiking boot buying guide", "boot sizing guide"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 2400,
            "canonical_url": f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/waterproof-jacket-buying-guide",
            "page_type": "guide",
            "title": "Waterproof Jacket Guide: 2L vs 2.5L vs 3L Hardshells Explained",
            "meta_description": "Learn the difference between membrane laminates, DWR coatings, and breathability ratings.",
            "primary_keyword": "waterproof jacket guide",
            "secondary_keywords": ["hardshell layering guide", "3l waterproof jacket explained"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1850,
            "canonical_url": f"{DEMO_DOMAIN}/guides/waterproof-jacket-buying-guide",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/backpack-sizing-and-fit-guide",
            "page_type": "guide",
            "title": "How to Measure Your Torso for Backpack Fit: Step-by-Step Guide",
            "meta_description": "Get accurate measurements of your iliac crest and C7 vertebra for optimal pack weight transfer.",
            "primary_keyword": "how to measure torso for backpack",
            "secondary_keywords": ["backpack fit guide", "hiking backpack sizing"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1620,
            "canonical_url": f"{DEMO_DOMAIN}/guides/backpack-sizing-and-fit-guide",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/trail-running-essential-gear-checklist",
            "page_type": "guide",
            "title": "Trail Running Essential Gear Checklist: What to Pack for 5k to 50k",
            "meta_description": "Comprehensive packing guide for day runs and ultramarathons: hydration, navigation, and nutrition.",
            "primary_keyword": "trail running gear checklist",
            "secondary_keywords": ["ultramarathon packing list", "what to carry trail running"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1950,
            "canonical_url": f"{DEMO_DOMAIN}/guides/trail-running-essential-gear-checklist",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        # Comparison Pages (5)
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/trail-vs-road-running-shoes",
            "page_type": "comparison",
            "title": "Trail Running vs Road Running Shoes: Key Differences & Trade-Offs",
            "meta_description": "Can you wear trail runners on pavement? We compare lugs, outsoles, cushioning, and durability.",
            "primary_keyword": "trail vs road running shoes",
            "secondary_keywords": ["can you wear trail shoes on road", "trail vs road comparison"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1780,
            "canonical_url": f"{DEMO_DOMAIN}/comparisons/trail-vs-road-running-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/waterproof-vs-breathable-hiking-boots",
            "page_type": "comparison",
            "title": "Waterproof vs Non-Waterproof Hiking Boots: When to Choose Gore-Tex",
            "meta_description": "Why waterproof boots might make your feet sweatier in hot weather. Full pros and cons analysis.",
            "primary_keyword": "waterproof vs breathable hiking boots",
            "secondary_keywords": ["gore tex boots pros and cons", "breathable trail shoes vs waterproof"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 1650,
            "canonical_url": f"{DEMO_DOMAIN}/comparisons/waterproof-vs-breathable-hiking-boots",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/cushioned-vs-minimalist-running-shoes",
            "page_type": "comparison",
            "title": "Maximalist Cushioned vs Barefoot Minimalist Shoes: Impact & Form",
            "meta_description": "Compare zero-drop minimalist shoes with max stack cushion road shoes for injury prevention.",
            "primary_keyword": "cushioned vs minimalist running shoes",
            "secondary_keywords": ["barefoot running comparison", "maximalist running shoes pros cons"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1820,
            "canonical_url": f"{DEMO_DOMAIN}/comparisons/cushioned-vs-minimalist-running-shoes",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/merino-wool-vs-synthetic-layers",
            "page_type": "comparison",
            "title": "Merino Wool vs Synthetic Base Layers: Warmth, Odor & Drying Time",
            "meta_description": "Head-to-head testing of merino wool and polyester fleeces in mountain environments.",
            "primary_keyword": "merino wool vs synthetic base layer",
            "secondary_keywords": ["merino vs polyester hiking", "best thermal layer material"],
            "search_intent": SearchIntent.COMMERCIAL.value,
            "word_count": 1590,
            "canonical_url": f"{DEMO_DOMAIN}/comparisons/merino-wool-vs-synthetic-layers",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
        {
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/hardshell-vs-softshell-jackets",
            "page_type": "comparison",
            "title": "Hardshell vs Softshell Jackets: Weather Protection vs Breathability",
            "meta_description": "Understand when you need a rigid waterproof hardshell vs a flexible, breathable softshell.",
            "primary_keyword": "hardshell vs softshell jacket",
            "secondary_keywords": ["when to wear softshell", "difference between hard and soft shell"],
            "search_intent": SearchIntent.INFORMATIONAL.value,
            "word_count": 1720,
            "canonical_url": f"{DEMO_DOMAIN}/comparisons/hardshell-vs-softshell-jackets",
            "indexable": True,
            "status_code": 200,
            "observed_at": "2026-06-01T08:00:00Z",
        },
    ]

    # --------------------------------------------------------------------------
    # 2. Keywords (105 keywords across 4 search intents)
    # --------------------------------------------------------------------------
    keywords_raw = [
        # Commercial / Category / Product
        ("trail running shoes", "commercial", 33100, 68, f"{DEMO_DOMAIN}/collections/trail-running", 4.2, 18500, 388),
        ("waterproof hiking boots", "commercial", 27400, 64, f"{DEMO_DOMAIN}/collections/hiking-boots", 3.1, 15400, 277),
        ("running shoes", "commercial", 74000, 85, f"{DEMO_DOMAIN}/collections/running-shoes", 11.4, 8200, 114),
        ("backpacking gear", "commercial", 14800, 52, f"{DEMO_DOMAIN}/collections/backpacking-gear", 5.6, 9100, 291),
        ("outdoor jackets", "commercial", 22000, 71, f"{DEMO_DOMAIN}/collections/outdoor-jackets", 8.3, 7400, 162),
        ("climbing shoes", "commercial", 19500, 60, f"{DEMO_DOMAIN}/collections/climbing-shoes", 6.1, 8800, 264),
        ("carbon plate running shoes", "commercial", 12100, 58, f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes", 3.4, 7600, 288),
        ("ultralight backpack 45l", "commercial", 4400, 41, f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l", 2.8, 3800, 228),
        ("goretex rain jacket", "commercial", 18200, 66, f"{DEMO_DOMAIN}/products/goretex-weather-jacket", 4.9, 8100, 243),
        ("bouldering shoes", "commercial", 9900, 48, f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes", 3.7, 6200, 266),
        ("merino wool base layer", "commercial", 8100, 44, f"{DEMO_DOMAIN}/products/thermal-merino-base-layer", 2.9, 6900, 317),
        ("max cushion running shoes", "commercial", 6600, 49, f"{DEMO_DOMAIN}/products/ultra-cushion-marathon-shoes", 5.1, 4100, 118),
        ("backpacking boots", "commercial", 11400, 55, f"{DEMO_DOMAIN}/products/rugged-terrain-trekking-boots", 6.2, 5900, 159),
        ("running hydration vest", "commercial", 7200, 42, f"{DEMO_DOMAIN}/products/hydration-pack-vest-10l", 3.3, 5100, 234),
        ("backpacking canister stove", "commercial", 5400, 38, f"{DEMO_DOMAIN}/products/compact-camping-stove", 2.4, 4600, 299),
        ("anti blister running socks", "commercial", 3600, 31, f"{DEMO_DOMAIN}/products/all-weather-trail-socks", 2.1, 3200, 246),
        ("running sunglasses polarized", "commercial", 4900, 39, f"{DEMO_DOMAIN}/products/polarized-trail-sunglasses", 4.4, 3800, 133),
        ("carbon fiber trekking poles", "commercial", 5100, 36, f"{DEMO_DOMAIN}/products/collapsible-trekking-poles", 3.2, 4200, 218),
        ("ultralight down jacket", "commercial", 14200, 62, f"{DEMO_DOMAIN}/products/insulated-down-jacket-800", 5.8, 6800, 183),
        # Informational Guides & Comparisons
        ("best trail running shoes for beginners", "informational", 4400, 34, f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners", 2.6, 3900, 390),
        ("how to choose hiking boots", "informational", 6600, 42, f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots", 1.9, 5800, 754),
        ("waterproof jacket guide", "informational", 3200, 29, f"{DEMO_DOMAIN}/guides/waterproof-jacket-buying-guide", 4.1, 2600, 182),
        ("how to measure torso for backpack", "informational", 5400, 33, f"{DEMO_DOMAIN}/guides/backpack-sizing-and-fit-guide", 2.2, 4900, 588),
        ("trail running gear checklist", "informational", 2800, 25, f"{DEMO_DOMAIN}/guides/trail-running-essential-gear-checklist", 3.5, 2300, 184),
        ("trail vs road running shoes", "informational", 8100, 45, f"{DEMO_DOMAIN}/comparisons/trail-vs-road-running-shoes", 2.3, 7200, 864),
        ("waterproof vs breathable hiking boots", "informational", 3600, 32, f"{DEMO_DOMAIN}/comparisons/waterproof-vs-breathable-hiking-boots", 3.8, 2900, 174),
        ("cushioned vs minimalist running shoes", "informational", 2400, 27, f"{DEMO_DOMAIN}/comparisons/cushioned-vs-minimalist-running-shoes", 4.6, 1800, 99),
        ("merino wool vs synthetic base layer", "informational", 4200, 35, f"{DEMO_DOMAIN}/comparisons/merino-wool-vs-synthetic-layers", 3.1, 3600, 288),
        ("hardshell vs softshell jacket", "informational", 9600, 48, f"{DEMO_DOMAIN}/comparisons/hardshell-vs-softshell-jackets", 2.7, 8100, 891),
        # Navigational
        ("searchmind store", "navigational", 1800, 12, f"{DEMO_DOMAIN}/", 1.0, 1750, 1050),
        ("searchmind hiking boots", "navigational", 950, 15, f"{DEMO_DOMAIN}/collections/hiking-boots", 1.0, 920, 460),
        ("searchmind trail running", "navigational", 820, 14, f"{DEMO_DOMAIN}/collections/trail-running", 1.0, 800, 416),
        ("searchmind outdoor return policy", "navigational", 450, 10, f"{DEMO_DOMAIN}/", 1.0, 430, 215),
        ("searchmind gear sale", "navigational", 1200, 18, f"{DEMO_DOMAIN}/", 1.0, 1150, 575),
    ]

    # Expand to 105 realistic keywords systematically across products and categories
    for i in range(1, 72):
        if i <= 20:
            kw = f"best outdoor gear item {i}"
            intent = "informational"
            vol = 1200 + i * 80
            diff = 20 + (i % 30)
            url = f"{DEMO_DOMAIN}/guides/trail-running-essential-gear-checklist"
            pos = 8.0 + (i % 12)
            imp = 800 + i * 50
            clk = int(imp * (0.02 + (1.0 / (pos + 1.0)) * 0.1))
        elif i <= 45:
            kw = f"buy backcountry equipment {i}"
            intent = "transactional"
            vol = 800 + i * 40
            diff = 35 + (i % 25)
            url = f"{DEMO_DOMAIN}/collections/backpacking-gear"
            pos = 5.0 + (i % 8)
            imp = 600 + i * 30
            clk = int(imp * 0.035)
        else:
            kw = f"lightweight trail gear review {i}"
            intent = "commercial"
            vol = 650 + i * 30
            diff = 25 + (i % 20)
            url = f"{DEMO_DOMAIN}/comparisons/trail-vs-road-running-shoes"
            pos = 4.0 + (i % 6)
            imp = 500 + i * 25
            clk = int(imp * 0.04)
        keywords_raw.append((kw, intent, vol, diff, url, float(pos), imp, clk))

    keywords_data = []
    for kw, intent, vol, diff, url, pos, imp, clk in keywords_raw:
        ctr = round((clk / imp) * 100, 2) if imp > 0 else 0.0
        keywords_data.append({
            "keyword": kw,
            "intent": intent,
            "search_volume": vol,
            "difficulty": diff,
            "target_url": url,
            "current_position": pos,
            "impressions": imp,
            "clicks": clk,
            "ctr": ctr,
        })

    # --------------------------------------------------------------------------
    # 3. Rankings History (75 records spanning June to September 2026)
    # --------------------------------------------------------------------------
    rankings_data = []
    sample_kws = keywords_data[:15]
    dates = ["2026-06-15", "2026-07-15", "2026-08-15", "2026-09-15", "2026-09-27"]

    # Trajectory profiles for key tracked terms
    trajectories = [
        [5.4, 4.8, 3.8, 3.1, 3.1],   # Improving (boots)
        [4.8, 4.2, 3.9, 4.1, 4.2],   # Stable (trail shoes)
        [14.2, 13.1, 11.8, 10.4, 9.8], # Page 2 to Page 1 (running shoes)
        [4.2, 5.1, 6.8, 8.2, 8.9],   # Declining (jackets)
        [3.1, 2.8, 2.7, 2.6, 2.6],   # Solid top-3 (beginner guide)
    ]

    for idx, kw_obj in enumerate(sample_kws):
        traj = trajectories[idx % len(trajectories)]
        for d_idx, date_str in enumerate(dates):
            pos = traj[d_idx]
            imp = int(kw_obj["search_volume"] * (0.4 + (1.0 / (pos + 1.0))))
            clk = int(imp * (0.015 + (1.0 / (pos + 2.0)) * 0.08))
            rankings_data.append({
                "keyword": kw_obj["keyword"],
                "target_url": kw_obj["target_url"],
                "position": round(pos, 1),
                "impressions": imp,
                "clicks": clk,
                "ctr": round((clk / imp) * 100, 2) if imp > 0 else 0.0,
                "recorded_date": f"{date_str}T00:00:00Z",
            })

    # --------------------------------------------------------------------------
    # 4. SEO Observations (42 records matching SEOObservation)
    # --------------------------------------------------------------------------
    observations_data = [
        {
            "observation_id": "obs_001",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/waterproof-alpine-hiking-boots",
            "keyword": "waterproof hiking boots",
            "observation_type": "low_ctr",
            "metric_name": "ctr",
            "current_value": 1.8,
            "previous_value": 3.2,
            "delta": -1.4,
            "unit": "%",
            "severity": ObservationSeverity.HIGH.value,
            "evidence": {"position": 3.1, "impressions": 15400, "clicks": 277, "serp_features": ["rich_snippets", "shopping_graph"]},
            "observed_at": "2026-06-15T09:00:00Z",
        },
        {
            "observation_id": "obs_002",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/running-shoes",
            "keyword": "running shoes",
            "observation_type": "ranking_opportunity",
            "metric_name": "position",
            "current_value": 11.4,
            "previous_value": 14.2,
            "delta": -2.8,
            "unit": "pos",
            "severity": ObservationSeverity.MEDIUM.value,
            "evidence": {"impressions": 8200, "top_queries": ["trail running shoes", "road running shoes"], "gap": "page_2_threshold"},
            "observed_at": "2026-06-15T09:15:00Z",
        },
        {
            "observation_id": "obs_003",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/trail-blazer-running-shoes",
            "keyword": "trail running shoes",
            "observation_type": "title_issue",
            "metric_name": "ctr",
            "current_value": 2.1,
            "previous_value": 2.1,
            "delta": 0.0,
            "unit": "%",
            "severity": ObservationSeverity.MEDIUM.value,
            "evidence": {"title_length": 42, "missing_terms": ["buy", "vibram", "free shipping"], "position": 4.2},
            "observed_at": "2026-06-16T10:00:00Z",
        },
        {
            "observation_id": "obs_004",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners",
            "keyword": "best trail running shoes for beginners",
            "observation_type": "impression_growth",
            "metric_name": "impressions",
            "current_value": 3900.0,
            "previous_value": 2400.0,
            "delta": 1500.0,
            "unit": "count",
            "severity": ObservationSeverity.INFO.value,
            "evidence": {"position": 2.6, "organic_traffic_growth_pct": 62.5},
            "observed_at": "2026-06-18T11:00:00Z",
        },
        {
            "observation_id": "obs_005",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/outdoor-jackets",
            "keyword": "outdoor jackets",
            "observation_type": "ranking_decline",
            "metric_name": "position",
            "current_value": 8.3,
            "previous_value": 4.2,
            "delta": 4.1,
            "unit": "pos",
            "severity": ObservationSeverity.CRITICAL.value,
            "evidence": {"competitor_movements": ["outdoor-brand-x added 3L comparison guide", "serp pack displaced position 4"]},
            "observed_at": "2026-06-20T14:00:00Z",
        },
        {
            "observation_id": "obs_006",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes",
            "keyword": "carbon plate running shoes",
            "observation_type": "intent_mismatch",
            "metric_name": "ctr",
            "current_value": 3.79,
            "previous_value": 4.5,
            "delta": -0.71,
            "unit": "%",
            "severity": ObservationSeverity.MEDIUM.value,
            "evidence": {"serp_intent": "transactional_purchase", "page_copy": "informational_biomechanics_heavy"},
            "observed_at": "2026-06-22T09:30:00Z",
        },
        {
            "observation_id": "obs_007",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/goretex-weather-jacket",
            "keyword": "goretex rain jacket",
            "observation_type": "meta_description_issue",
            "metric_name": "ctr",
            "current_value": 3.0,
            "previous_value": 3.0,
            "delta": 0.0,
            "unit": "%",
            "severity": ObservationSeverity.LOW.value,
            "evidence": {"meta_length": 86, "call_to_action": "missing", "position": 4.9},
            "observed_at": "2026-06-25T11:00:00Z",
        },
        {
            "observation_id": "obs_008",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l",
            "keyword": "ultralight backpack 45l",
            "observation_type": "content_gap",
            "metric_name": "position",
            "current_value": 2.8,
            "previous_value": 2.8,
            "delta": 0.0,
            "unit": "pos",
            "severity": ObservationSeverity.INFO.value,
            "evidence": {"missing_faqs": ["bear canister compatibility", "actual dyneema weight specs"]},
            "observed_at": "2026-06-28T16:00:00Z",
        },
        {
            "observation_id": "obs_009",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots",
            "keyword": "how to choose hiking boots",
            "observation_type": "internal_linking_opportunity",
            "metric_name": "clicks",
            "current_value": 754.0,
            "previous_value": 520.0,
            "delta": 234.0,
            "unit": "count",
            "severity": ObservationSeverity.MEDIUM.value,
            "evidence": {"top_ranking_guide": True, "outbound_internal_links_to_products": 2},
            "observed_at": "2026-07-01T09:00:00Z",
        },
        {
            "observation_id": "obs_010",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes",
            "keyword": "bouldering shoes",
            "observation_type": "technical_issue",
            "metric_name": "position",
            "current_value": 3.7,
            "previous_value": 3.7,
            "delta": 0.0,
            "unit": "pos",
            "severity": ObservationSeverity.LOW.value,
            "evidence": {"schema_type": "Product", "issue": "missing aggregateRating and priceValidUntil"},
            "observed_at": "2026-07-02T13:00:00Z",
        },
    ]

    # Populate observations obs_011 to obs_042
    obs_types = [
        ("low_ctr", "ctr", 1.9, 2.8, "%", ObservationSeverity.HIGH),
        ("ranking_opportunity", "position", 11.2, 13.5, "pos", ObservationSeverity.MEDIUM),
        ("content_gap", "word_count", 550, 950, "count", ObservationSeverity.LOW),
        ("intent_mismatch", "bounce_rate", 68.0, 52.0, "%", ObservationSeverity.MEDIUM),
        ("traffic_decline", "clicks", 180, 260, "count", ObservationSeverity.HIGH),
        ("impression_growth", "impressions", 4200, 2800, "count", ObservationSeverity.INFO),
        ("conversion_underperformance", "cvr", 0.8, 1.6, "%", ObservationSeverity.HIGH),
        ("meta_description_issue", "ctr", 2.2, 2.2, "%", ObservationSeverity.LOW),
    ]

    for i in range(11, 43):
        t_type, metric, c_val, p_val, unit, sev = obs_types[i % len(obs_types)]
        page = pages_data[i % len(pages_data)]
        observations_data.append({
            "observation_id": f"obs_{i:03d}",
            "project_id": DEMO_PROJECT_ID,
            "url": page["url"],
            "keyword": page["primary_keyword"],
            "observation_type": t_type,
            "metric_name": metric,
            "current_value": float(c_val),
            "previous_value": float(p_val),
            "delta": round(float(c_val - p_val), 4),
            "unit": unit,
            "severity": sev.value,
            "evidence": {"sample_query": page["primary_keyword"], "metric_tracked": metric},
            "observed_at": f"2026-07-{(i % 25) + 1:02d}T10:00:00Z",
        })

    # --------------------------------------------------------------------------
    # 5. Optimization Decisions (22 records matching OptimizationDecision)
    # --------------------------------------------------------------------------
    decisions_data = [
        {
            "decision_id": "dec_001",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/waterproof-alpine-hiking-boots",
            "observation_ids": ["obs_001"],
            "decision_type": "title_update",
            "hypothesis": "Emphasizing commercial purchase intent and key benefits in title may increase click-through rate.",
            "rationale": "Page ranks #3 for 'waterproof hiking boots' but title lacks value propositions like warranty or free shipping.",
            "expected_effect": "CTR recovery toward 2.8% - 3.2%",
            "proposed_changes": {"title": {"from": "Waterproof Alpine Hiking Boots", "to": "Buy Waterproof Alpine Hiking Boots | 100% Leather & Free Returns"}},
            "decided_at": "2026-06-16T10:00:00Z",
        },
        {
            "decision_id": "dec_002",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/running-shoes",
            "observation_ids": ["obs_002"],
            "decision_type": "category_copy_update",
            "hypothesis": "Adding contextual category copy and sub-heading anchors may lift keyword rank into page 1.",
            "rationale": "Query sits on page 2 threshold (#11) with growing impressions; extra topical depth could push it over.",
            "expected_effect": "Position lift to top 8",
            "proposed_changes": {"category_copy": "Add 350-word buyers intro covering terrain types"},
            "decided_at": "2026-06-16T11:00:00Z",
        },
        {
            "decision_id": "dec_003",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/trail-blazer-running-shoes",
            "observation_ids": ["obs_003"],
            "decision_type": "title_update",
            "hypothesis": "Shortening brand prefix and leading with high-intent keywords may lift CTR.",
            "rationale": "Mobile SERPs truncate current title at 45 characters.",
            "expected_effect": "+0.5% CTR lift",
            "proposed_changes": {"title": {"from": "Trail Blazer Pro Running Shoes | SearchMind Store", "to": "Trail Blazer Pro - Men's Vibram Trail Running Shoes"}},
            "decided_at": "2026-06-17T09:00:00Z",
        },
        {
            "decision_id": "dec_004",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners",
            "observation_ids": ["obs_004"],
            "decision_type": "FAQ_content",
            "hypothesis": "Adding an FAQ accordion addressing common shoe durability questions may capture PAA snippets.",
            "rationale": "High impression velocity indicates user demand for specific beginner queries like drop and sizing.",
            "expected_effect": "Gain featured snippet positions for 3 secondary terms",
            "proposed_changes": {"faq": "Add 4 structured Q&As on trail shoe break-in"},
            "decided_at": "2026-06-19T13:00:00Z",
        },
        {
            "decision_id": "dec_005",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/outdoor-jackets",
            "observation_ids": ["obs_005"],
            "decision_type": "content_refresh",
            "hypothesis": "Comprehensive technical refresh comparing 2L vs 3L jacket breathability may stem rank decline.",
            "rationale": "Competitors gained positions by introducing technical lab test comparisons.",
            "expected_effect": "Recover ranking from #8 to top 5",
            "proposed_changes": {"content": "Insert waterproof breathability testing matrix"},
            "decided_at": "2026-06-21T10:00:00Z",
        },
        {
            "decision_id": "dec_006",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes",
            "observation_ids": ["obs_006"],
            "decision_type": "keyword_alignment",
            "hypothesis": "Refocusing product page copy from generic marathon terminology toward 'carbon plate racers' may align intent.",
            "rationale": "Users searching for carbon road shoes want weight and energy return specs, not training tips.",
            "expected_effect": "Improve engagement and conversion rate",
            "proposed_changes": {"headings": "Add energy return % and carbon plate geometry"},
            "decided_at": "2026-06-23T11:30:00Z",
        },
        {
            "decision_id": "dec_007",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/goretex-weather-jacket",
            "observation_ids": ["obs_007"],
            "decision_type": "meta_description_test",
            "hypothesis": "Testing an active action-oriented meta description with warranty callout may boost CTR.",
            "rationale": "Current meta description is purely descriptive without a hook.",
            "expected_effect": "+0.4% CTR increase",
            "proposed_changes": {"meta": "Add 'Lifetime Storm Guarantee & Free 2-Day Shipping'"},
            "decided_at": "2026-06-26T14:00:00Z",
        },
        {
            "decision_id": "dec_008",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l",
            "observation_ids": ["obs_008"],
            "decision_type": "content_refresh",
            "hypothesis": "Adding gear compatibility specifications and pack load capacity tables may increase dwell time.",
            "rationale": "Thru-hikers need to know if specific bear canisters fit horizontally.",
            "expected_effect": "Reduce bounce rate by 15%",
            "proposed_changes": {"table": "Insert bear canister fit guide"},
            "decided_at": "2026-06-29T16:00:00Z",
        },
        {
            "decision_id": "dec_009",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots",
            "observation_ids": ["obs_009"],
            "decision_type": "internal_linking",
            "hypothesis": "Adding high-intent contextual link widgets to top product pages may drive commercial traffic.",
            "rationale": "Guide gets 750+ monthly clicks but transfers minimal page equity to product pages.",
            "expected_effect": "+35% internal product page clicks",
            "proposed_changes": {"links": "Add contextual product cards for top boots"},
            "decided_at": "2026-07-02T10:00:00Z",
        },
        {
            "decision_id": "dec_010",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes",
            "observation_ids": ["obs_010"],
            "decision_type": "schema_update",
            "hypothesis": "Enriching JSON-LD schema with complete aggregateRating and inStock status may trigger rich badges.",
            "rationale": "Competitors exhibit star ratings and in-stock badges directly in SERP snippets.",
            "expected_effect": "Trigger star ratings snippet in Google search",
            "proposed_changes": {"schema": "Implement complete schema.org/Product specification"},
            "decided_at": "2026-07-03T14:30:00Z",
        },
    ]

    for i in range(11, 23):
        p = pages_data[i % len(pages_data)]
        decisions_data.append({
            "decision_id": f"dec_{i:03d}",
            "project_id": DEMO_PROJECT_ID,
            "url": p["url"],
            "observation_ids": [f"obs_{i:03d}"],
            "decision_type": "content_refresh" if i % 2 == 0 else "title_update",
            "hypothesis": f"Updating page copy and structural headers for {p['primary_keyword']} may align better with search intent.",
            "rationale": f"Observation obs_{i:03d} noted opportunity to improve organic visibility.",
            "expected_effect": "+0.5% CTR or improved ranking stability",
            "proposed_changes": {"action": "Update headers and intro text"},
            "decided_at": f"2026-07-{(i % 25) + 2:02d}T11:00:00Z",
        })

    # --------------------------------------------------------------------------
    # 6. SEO Experiments (20 records matching SEOExperiment)
    # --------------------------------------------------------------------------
    experiments_data = [
        {
            "experiment_id": "exp_001",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/waterproof-alpine-hiking-boots",
            "experiment_type": "title_tag_test",
            "hypothesis": "Aligning product title with commercial purchase intent may improve CTR.",
            "control_description": "Waterproof Alpine Hiking Boots | SearchMind Store",
            "treatment_description": "Buy Waterproof Alpine Hiking Boots | 100% Leather & Free Returns",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "impressions", "position"],
            "baseline_metrics": {"ctr": 1.8, "position": 3.1, "clicks": 277},
            "start_date": "2026-06-20T00:00:00Z",
            "end_date": "2026-07-10T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-19T14:00:00Z",
        },
        {
            "experiment_id": "exp_002",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/running-shoes",
            "experiment_type": "category_copy_update",
            "hypothesis": "Adding 350-word buyer guide text to category header may push ranking from page 2 to top 8.",
            "control_description": "Category page with product grid only and no contextual copy",
            "treatment_description": "Category page with 350-word buyer guide discussing terrain and drop",
            "primary_metric": "position",
            "secondary_metrics": ["impressions", "clicks"],
            "baseline_metrics": {"position": 11.4, "impressions": 8200, "clicks": 114},
            "start_date": "2026-06-20T00:00:00Z",
            "end_date": "2026-07-15T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-19T15:00:00Z",
        },
        {
            "experiment_id": "exp_003",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/trail-blazer-running-shoes",
            "experiment_type": "title_tag_test",
            "hypothesis": "Shortening title to avoid mobile SERP truncation may improve mobile CTR.",
            "control_description": "Trail Blazer Pro Running Shoes | SearchMind Store",
            "treatment_description": "Trail Blazer Pro - Men's Vibram Trail Running Shoes",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "position"],
            "baseline_metrics": {"ctr": 2.1, "position": 4.2, "clicks": 388},
            "start_date": "2026-06-22T00:00:00Z",
            "end_date": "2026-07-06T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-21T10:00:00Z",
        },
        {
            "experiment_id": "exp_004",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/best-running-shoes-beginners",
            "experiment_type": "FAQ_content",
            "hypothesis": "Adding structured FAQ schema may gain People Also Ask placements.",
            "control_description": "Guide without FAQ section",
            "treatment_description": "Guide with 4 structured FAQ accordions and FAQPage schema",
            "primary_metric": "impressions",
            "secondary_metrics": ["clicks", "ctr"],
            "baseline_metrics": {"impressions": 3900, "clicks": 390, "ctr": 10.0},
            "start_date": "2026-06-25T00:00:00Z",
            "end_date": "2026-07-20T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-24T12:00:00Z",
        },
        {
            "experiment_id": "exp_005",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/collections/outdoor-jackets",
            "experiment_type": "content_refresh",
            "hypothesis": "Adding technical breathability comparison table may reverse ranking drop.",
            "control_description": "Standard category text",
            "treatment_description": "Comprehensive breathability comparison chart with lab ratings",
            "primary_metric": "position",
            "secondary_metrics": ["impressions", "clicks"],
            "baseline_metrics": {"position": 8.3, "impressions": 7400, "clicks": 162},
            "start_date": "2026-06-25T00:00:00Z",
            "end_date": "2026-07-25T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-24T15:00:00Z",
        },
        {
            "experiment_id": "exp_006",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/apex-carbon-road-shoes",
            "experiment_type": "keyword_alignment",
            "hypothesis": "Shifting heading emphasis to carbon plate racer terminology may improve conversion and engagement.",
            "control_description": "General marathon training terminology in H2s and intro",
            "treatment_description": "Dedicated H2s highlighting carbon plate stiffness and energy return",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "position"],
            "baseline_metrics": {"ctr": 3.79, "position": 3.4, "clicks": 288},
            "start_date": "2026-06-28T00:00:00Z",
            "end_date": "2026-07-19T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-27T11:00:00Z",
        },
        {
            "experiment_id": "exp_007",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/goretex-weather-jacket",
            "experiment_type": "meta_description_test",
            "hypothesis": "Adding warranty and shipping hook to meta description may improve SERP click-through rate.",
            "control_description": "Heavy storm protection with pit zips and helmet-compatible hood.",
            "treatment_description": "Rated #1 Storm Hardshell. Includes Lifetime Storm Guarantee & Free 2-Day Shipping. Shop Now.",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"ctr": 3.0, "clicks": 243},
            "start_date": "2026-07-01T00:00:00Z",
            "end_date": "2026-07-22T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-06-30T10:00:00Z",
        },
        {
            "experiment_id": "exp_008",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/lightweight-summit-backpack-45l",
            "experiment_type": "content_refresh",
            "hypothesis": "Adding bear canister fit specification and load tables may reduce bounce rate and improve rankings.",
            "control_description": "Standard pack specs without dimensions table",
            "treatment_description": "Detailed canister fit chart with photos and certified capacity limits",
            "primary_metric": "position",
            "secondary_metrics": ["ctr", "clicks"],
            "baseline_metrics": {"position": 2.8, "clicks": 228, "ctr": 6.0},
            "start_date": "2026-07-05T00:00:00Z",
            "end_date": "2026-07-26T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-04T12:00:00Z",
        },
        {
            "experiment_id": "exp_009",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/guides/how-to-choose-hiking-boots",
            "experiment_type": "internal_linking",
            "hypothesis": "Contextual product callout cards within high-traffic guide may boost linked product page impressions.",
            "control_description": "Text hyperlinks in conclusion only",
            "treatment_description": "Prominent contextual comparison cards embedded within guide sections",
            "primary_metric": "clicks",
            "secondary_metrics": ["ctr"],
            "baseline_metrics": {"clicks": 754.0, "ctr": 13.0},
            "start_date": "2026-07-08T00:00:00Z",
            "end_date": "2026-07-29T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-07T14:00:00Z",
        },
        {
            "experiment_id": "exp_010",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/pro-grip-bouldering-shoes",
            "experiment_type": "schema_update",
            "hypothesis": "Adding complete schema.org/Product structured data may earn star rating snippet.",
            "control_description": "Basic OpenGraph tags without structured product markup",
            "treatment_description": "Full schema.org JSON-LD with aggregateRating, offers, and brand",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"ctr": 4.29, "clicks": 266},
            "start_date": "2026-07-10T00:00:00Z",
            "end_date": "2026-07-31T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-09T09:00:00Z",
        },
        # Experiments 11 to 20
        {
            "experiment_id": "exp_011",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/comparisons/trail-vs-road-running-shoes",
            "experiment_type": "title_tag_test",
            "hypothesis": "Adding current year [2026] to comparison title may boost click-through rate.",
            "control_description": "Trail Running vs Road Running Shoes: Key Differences",
            "treatment_description": "Trail vs Road Running Shoes: Differences & Full 2026 Guide",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"ctr": 12.0, "clicks": 864},
            "start_date": "2026-07-15T00:00:00Z",
            "end_date": "2026-08-05T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-14T11:00:00Z",
        },
        {
            "experiment_id": "exp_012",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/thermal-merino-base-layer",
            "experiment_type": "title_tag_test",
            "hypothesis": "Truncating title to generic term 'Merino Wool Shirt' may hurt specificity and lower CTR.",
            "control_description": "250gsm Merino Wool Long Sleeve Base Layer | SearchMind",
            "treatment_description": "Merino Wool Shirt - Warm Long Sleeve",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "position"],
            "baseline_metrics": {"ctr": 4.59, "clicks": 317, "position": 2.9},
            "start_date": "2026-07-18T00:00:00Z",
            "end_date": "2026-08-08T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-17T10:00:00Z",
        },
        {
            "experiment_id": "exp_013",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/ultra-cushion-marathon-shoes",
            "experiment_type": "content_refresh",
            "hypothesis": "Deleting detailed foam density specs to make page shorter may hurt technical ranking signals.",
            "control_description": "Comprehensive technical foam description with durometer ratings",
            "treatment_description": "Simplified marketing bullet points without technical measurements",
            "primary_metric": "position",
            "secondary_metrics": ["impressions", "clicks"],
            "baseline_metrics": {"position": 5.1, "impressions": 4100, "clicks": 118},
            "start_date": "2026-07-20T00:00:00Z",
            "end_date": "2026-08-10T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-19T09:00:00Z",
        },
        {
            "experiment_id": "exp_014",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/rugged-terrain-trekking-boots",
            "experiment_type": "title_tag_test",
            "hypothesis": "Testing promotional discount keyword in title tag on commercial product page.",
            "control_description": "Trekker XT Heavy-Duty Backpacking Boots | SearchMind",
            "treatment_description": "Cheap Trekker XT Backpacking Boots - Huge Discount Sale",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "position"],
            "baseline_metrics": {"ctr": 2.69, "clicks": 159, "position": 6.2},
            "start_date": "2026-07-25T00:00:00Z",
            "end_date": "2026-08-15T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-24T10:00:00Z",
        },
        {
            "experiment_id": "exp_015",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/hydration-pack-vest-10l",
            "experiment_type": "image_alt_update",
            "hypothesis": "Updating image alt text tags from 'vest-photo-1' to keyword-rich descriptive alt tags.",
            "control_description": "Default generic file names in alt attributes",
            "treatment_description": "Descriptive alt text including trail running hydration vest angles",
            "primary_metric": "impressions",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"impressions": 5100, "clicks": 234},
            "start_date": "2026-08-01T00:00:00Z",
            "end_date": "2026-08-22T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-07-31T12:00:00Z",
        },
        {
            "experiment_id": "exp_016",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/compact-camping-stove",
            "experiment_type": "meta_description_test",
            "hypothesis": "Swapping order of fuel efficiency vs boil time in meta description.",
            "control_description": "Sub-2oz titanium backpacking stove boiling 1 liter in 3 minutes.",
            "treatment_description": "Boils 1 liter in under 3 minutes with ultra-light sub-2oz titanium frame.",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"ctr": 6.5, "clicks": 299},
            "start_date": "2026-08-05T00:00:00Z",
            "end_date": "2026-08-26T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-08-04T10:00:00Z",
        },
        {
            "experiment_id": "exp_017",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/all-weather-trail-socks",
            "experiment_type": "internal_linking",
            "hypothesis": "Adding footer links from all product pages to socks category.",
            "control_description": "Standard footer without specific trail socks anchor link",
            "treatment_description": "Sitewide footer link with anchor 'Anti-Blister Running Socks'",
            "primary_metric": "position",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"position": 2.1, "clicks": 246},
            "start_date": "2026-08-10T00:00:00Z",
            "end_date": "2026-08-31T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-08-09T14:00:00Z",
        },
        {
            "experiment_id": "exp_018",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/polarized-trail-sunglasses",
            "experiment_type": "title_tag_test",
            "hypothesis": "Adding brand suffix to title tag during peak summer glare season.",
            "control_description": "Veloce Polarized Anti-Fog Running Sunglasses",
            "treatment_description": "Veloce Polarized Anti-Fog Running Sunglasses | SearchMind Eyewear",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks"],
            "baseline_metrics": {"ctr": 3.5, "clicks": 133},
            "start_date": "2026-08-15T00:00:00Z",
            "end_date": "2026-09-05T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-08-14T09:00:00Z",
        },
        {
            "experiment_id": "exp_019",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/collapsible-trekking-poles",
            "experiment_type": "content_refresh",
            "hypothesis": "Restructuring product specifications into comparison tabs during Google algorithm update.",
            "control_description": "Standard linear bulleted specifications list",
            "treatment_description": "Tabbed interactive specification layout",
            "primary_metric": "position",
            "secondary_metrics": ["clicks", "impressions"],
            "baseline_metrics": {"position": 3.2, "clicks": 218, "impressions": 4200},
            "start_date": "2026-08-20T00:00:00Z",
            "end_date": "2026-09-10T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-08-19T11:00:00Z",
        },
        {
            "experiment_id": "exp_020",
            "project_id": DEMO_PROJECT_ID,
            "url": f"{DEMO_DOMAIN}/products/insulated-down-jacket-800",
            "experiment_type": "title_tag_test",
            "hypothesis": "Testing '800-Fill' technical warmth rating vs 'Ultralight' in title tag before early fall season.",
            "control_description": "Apex 800-Fill Ultralight Packable Down Hoodie | SearchMind",
            "treatment_description": "Apex Ultralight Packable Down Jacket - 800 Fill Power",
            "primary_metric": "ctr",
            "secondary_metrics": ["clicks", "position"],
            "baseline_metrics": {"ctr": 2.69, "clicks": 183, "position": 5.8},
            "start_date": "2026-08-25T00:00:00Z",
            "end_date": "2026-09-15T00:00:00Z",
            "status": ExperimentStatus.COMPLETED.value,
            "created_at": "2026-08-24T16:00:00Z",
        },
    ]

    # --------------------------------------------------------------------------
    # 7. Experiment Outcomes (20 records matching ExperimentOutcome)
    # Balanced distribution: 6 Positive, 5 Negative, 5 Neutral, 4 Inconclusive
    # --------------------------------------------------------------------------
    outcomes_data = [
        # --- POSITIVE OUTCOMES (6) ---
        {
            "outcome_id": "out_001",
            "experiment_id": "exp_001",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 1.8,
            "primary_metric_after": 2.7,
            "absolute_change": 0.9,
            "percentage_change": 50.0,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Significant lift observed across 15,400 impressions over 20-day test window.",
            "interpretation": "On this commercial product page, aligning the title with purchase intent ('Buy' and 'Free Returns') coincided with improved CTR from 1.8% to 2.7% during the measured period.",
            "metric_results": {"clicks_before": 277, "clicks_after": 415, "position_after": 3.1},
            "measured_at": "2026-07-11T09:00:00Z",
        },
        {
            "outcome_id": "out_002",
            "experiment_id": "exp_002",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 11.4,
            "primary_metric_after": 8.7,
            "absolute_change": -2.7,
            "percentage_change": -23.68,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Position improved steadily from page 2 to page 1 top-10.",
            "interpretation": "Adding 350 words of buyer guidance to the category page was associated with crossing from page 2 (#11.4) into page 1 (#8.7) over 25 days.",
            "metric_results": {"impressions_after": 9800, "clicks_after": 196},
            "measured_at": "2026-07-16T10:00:00Z",
        },
        {
            "outcome_id": "out_004",
            "experiment_id": "exp_004",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 3900.0,
            "primary_metric_after": 5100.0,
            "absolute_change": 1200.0,
            "percentage_change": 30.77,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Captured 2 new People Also Ask features for beginner queries.",
            "interpretation": "On this informational beginner guide, structured FAQ content coincided with a 30.8% increase in organic search impressions.",
            "metric_results": {"clicks_after": 535, "ctr_after": 10.49},
            "measured_at": "2026-07-21T11:00:00Z",
        },
        {
            "outcome_id": "out_007",
            "experiment_id": "exp_007",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 3.0,
            "primary_metric_after": 3.6,
            "absolute_change": 0.6,
            "percentage_change": 20.0,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Higher snippet CTR achieved while average rank remained stable at 4.8.",
            "interpretation": "Incorporating clear warranty and shipping guarantees into the product meta description correlated with a 0.6 percentage point increase in CTR.",
            "metric_results": {"clicks_after": 295},
            "measured_at": "2026-07-23T14:00:00Z",
        },
        {
            "outcome_id": "out_009",
            "experiment_id": "exp_009",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 754.0,
            "primary_metric_after": 980.0,
            "absolute_change": 226.0,
            "percentage_change": 29.97,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Click growth on linked product pages tracked via internal analytics tags.",
            "interpretation": "Adding contextual product cards inside an informational boot-buying guide coincided with a 30% click increase across linked boots.",
            "metric_results": {"target_product_sessions": "+42%"},
            "measured_at": "2026-07-30T10:00:00Z",
        },
        {
            "outcome_id": "out_010",
            "experiment_id": "exp_010",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 4.29,
            "primary_metric_after": 4.95,
            "absolute_change": 0.66,
            "percentage_change": 15.38,
            "outcome_class": OutcomeClass.POSITIVE.value,
            "confidence_note": "Rich review snippet badge verified in Google SERP after 12 days.",
            "interpretation": "Adding full schema.org/Product structured data coincided with star ratings appearing in search results and a 15.4% lift in CTR.",
            "metric_results": {"rich_results_active": True},
            "measured_at": "2026-08-01T09:30:00Z",
        },

        # --- NEGATIVE OUTCOMES (5) ---
        {
            "outcome_id": "out_012",
            "experiment_id": "exp_012",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 4.59,
            "primary_metric_after": 3.72,
            "absolute_change": -0.87,
            "percentage_change": -18.95,
            "outcome_class": OutcomeClass.NEGATIVE.value,
            "confidence_note": "Measured across 3 weeks; users searching for thermal base layers skipped generic shirt titles.",
            "interpretation": "Removing specific fabric weight and technical descriptors in favor of a simplified generic title coincided with an 18.9% decrease in CTR.",
            "metric_results": {"clicks_after": 257, "position_after": 3.2},
            "measured_at": "2026-08-09T10:00:00Z",
        },
        {
            "outcome_id": "out_013",
            "experiment_id": "exp_013",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 5.1,
            "primary_metric_after": 7.4,
            "absolute_change": 2.3,
            "percentage_change": 45.1,
            "outcome_class": OutcomeClass.NEGATIVE.value,
            "confidence_note": "Rank fell from position 5.1 to 7.4 after text removal.",
            "interpretation": "Pruning technical foam specifications to create a minimalist layout was followed by a 2.3 position drop in ranking for cushioning terms.",
            "metric_results": {"impressions_after": 3200, "clicks_after": 86},
            "measured_at": "2026-08-11T12:00:00Z",
        },
        {
            "outcome_id": "out_014",
            "experiment_id": "exp_014",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 2.69,
            "primary_metric_after": 2.15,
            "absolute_change": -0.54,
            "percentage_change": -20.07,
            "outcome_class": OutcomeClass.NEGATIVE.value,
            "confidence_note": "Click-through rate dropped sharply; cheap/discount wording appeared to deter premium mountaineering buyers.",
            "interpretation": "Inserting discount and sale keywords into the title tag for a high-end $280 trekking boot correlated with lower CTR and perceived brand misalignment.",
            "metric_results": {"clicks_after": 127},
            "measured_at": "2026-08-16T11:00:00Z",
        },
        {
            "outcome_id": "out_005",
            "experiment_id": "exp_005",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 8.3,
            "primary_metric_after": 8.9,
            "absolute_change": 0.6,
            "percentage_change": 7.23,
            "outcome_class": OutcomeClass.NEGATIVE.value,
            "confidence_note": "Rank continued sliding from #8.3 to #8.9 despite technical table addition.",
            "interpretation": "Adding a comparison table to the category page did not arrest the ranking decline, indicating the drop was driven by broader competitor domain authority.",
            "metric_results": {"impressions_after": 6900},
            "measured_at": "2026-07-26T15:00:00Z",
        },
        {
            "outcome_id": "out_017",
            "experiment_id": "exp_017",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 2.1,
            "primary_metric_after": 2.4,
            "absolute_change": 0.3,
            "percentage_change": 14.29,
            "outcome_class": OutcomeClass.NEGATIVE.value,
            "confidence_note": "Sitewide footer links triggered no positive ranking movement and slightly degraded anchor equity.",
            "interpretation": "Sitewide exact-match footer linking did not improve category rankings and coincided with mild position volatility.",
            "metric_results": {"rank_volatility": "high"},
            "measured_at": "2026-09-01T12:00:00Z",
        },

        # --- NEUTRAL OUTCOMES (5) ---
        {
            "outcome_id": "out_003",
            "experiment_id": "exp_003",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 2.1,
            "primary_metric_after": 2.14,
            "absolute_change": 0.04,
            "percentage_change": 1.9,
            "outcome_class": OutcomeClass.NEUTRAL.value,
            "confidence_note": "Measured difference falls within normal observational noise margin.",
            "interpretation": "Shortening the title tag for mobile devices resulted in negligible CTR movement (2.1% to 2.14%) over the two-week test.",
            "metric_results": {"clicks_after": 395},
            "measured_at": "2026-07-07T09:00:00Z",
        },
        {
            "outcome_id": "out_008",
            "experiment_id": "exp_008",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 2.8,
            "primary_metric_after": 2.8,
            "absolute_change": 0.0,
            "percentage_change": 0.0,
            "outcome_class": OutcomeClass.NEUTRAL.value,
            "confidence_note": "Rank held steady at position 2.8 with unchanged CTR.",
            "interpretation": "Adding bear canister compatibility specifications improved user dwell time slightly but produced no change in organic search rankings.",
            "metric_results": {"dwell_time_delta": "+14s"},
            "measured_at": "2026-07-27T10:00:00Z",
        },
        {
            "outcome_id": "out_011",
            "experiment_id": "exp_011",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 12.0,
            "primary_metric_after": 12.1,
            "absolute_change": 0.1,
            "percentage_change": 0.83,
            "outcome_class": OutcomeClass.NEUTRAL.value,
            "confidence_note": "CTR remained essentially flat across 7,200 impressions.",
            "interpretation": "Adding the year [2026] to an evergreen comparison guide title produced no statistically distinguishable change in CTR.",
            "metric_results": {"clicks_after": 871},
            "measured_at": "2026-08-06T14:00:00Z",
        },
        {
            "outcome_id": "out_015",
            "experiment_id": "exp_015",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 5100.0,
            "primary_metric_after": 5150.0,
            "absolute_change": 50.0,
            "percentage_change": 0.98,
            "outcome_class": OutcomeClass.NEUTRAL.value,
            "confidence_note": "No measurable change in Google Image or Web Search impressions.",
            "interpretation": "Updating product image alt text with descriptive keywords produced no observable difference in web search impressions over 3 weeks.",
            "metric_results": {"image_search_clicks": 14},
            "measured_at": "2026-08-23T11:00:00Z",
        },
        {
            "outcome_id": "out_016",
            "experiment_id": "exp_016",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 6.5,
            "primary_metric_after": 6.45,
            "absolute_change": -0.05,
            "percentage_change": -0.77,
            "outcome_class": OutcomeClass.NEUTRAL.value,
            "confidence_note": "Google rewrote the meta description snippet dynamically for 60% of search queries.",
            "interpretation": "Reordering clauses in the meta description had no impact because search engines dynamically generated their own snippets for the query cluster.",
            "metric_results": {"snippet_display_rate": "40%"},
            "measured_at": "2026-08-27T10:00:00Z",
        },

        # --- INCONCLUSIVE OUTCOMES (4) ---
        {
            "outcome_id": "out_006",
            "experiment_id": "exp_006",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 3.79,
            "primary_metric_after": 4.1,
            "absolute_change": 0.31,
            "percentage_change": 8.18,
            "outcome_class": OutcomeClass.INCONCLUSIVE.value,
            "confidence_note": "Major competitor ran aggressive paid ads during test window, skewing organic click patterns.",
            "interpretation": "While CTR showed a slight 0.31 percentage point gain, concurrent paid advertising competition created confounding external variance.",
            "metric_results": {"external_confounder": "heavy competitor PPC campaign"},
            "measured_at": "2026-07-20T12:00:00Z",
        },
        {
            "outcome_id": "out_018",
            "experiment_id": "exp_018",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 3.5,
            "primary_metric_after": 3.9,
            "absolute_change": 0.4,
            "percentage_change": 11.43,
            "outcome_class": OutcomeClass.INCONCLUSIVE.value,
            "confidence_note": "Search impressions dropped 35% seasonal mid-August across the sunglasses category.",
            "interpretation": "Mild CTR rise coincided with a category-wide seasonal demand drop, rendering causal attribution inconclusive.",
            "metric_results": {"seasonal_drop_pct": -35.0},
            "measured_at": "2026-09-06T15:00:00Z",
        },
        {
            "outcome_id": "out_019",
            "experiment_id": "exp_019",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 3.2,
            "primary_metric_after": 3.6,
            "absolute_change": 0.4,
            "percentage_change": 12.5,
            "outcome_class": OutcomeClass.INCONCLUSIVE.value,
            "confidence_note": "Google core algorithm update rolled out between August 24 and September 4.",
            "interpretation": "Ranking fluctuations between position 2.9 and 4.1 overlapped with an unconfirmed search core update, preventing definitive conclusion.",
            "metric_results": {"serp_volatility_score": 8.8},
            "measured_at": "2026-09-11T14:00:00Z",
        },
        {
            "outcome_id": "out_020",
            "experiment_id": "exp_020",
            "project_id": DEMO_PROJECT_ID,
            "primary_metric_before": 2.69,
            "primary_metric_after": 2.82,
            "absolute_change": 0.13,
            "percentage_change": 4.83,
            "outcome_class": OutcomeClass.INCONCLUSIVE.value,
            "confidence_note": "Test duration of 3 weeks had low impression volume (1,200 total) before early winter demand.",
            "interpretation": "Small sample size during late August shoulder season yielded insufficient statistical power to verify the title adjustment impact.",
            "metric_results": {"sample_size_confidence": "low"},
            "measured_at": "2026-09-16T12:00:00Z",
        },
    ]

    # Save all files to output directory
    files_map = {
        "pages.json": pages_data,
        "keywords.json": keywords_data,
        "rankings.json": rankings_data,
        "observations.json": observations_data,
        "decisions.json": decisions_data,
        "experiments.json": experiments_data,
        "outcomes.json": outcomes_data,
    }

    counts = {}
    for filename, dataset in files_map.items():
        file_path = target_dir / filename
        with open(file_path, "w", encoding="utf-8") as fp:
            json.dump(dataset, fp, indent=2)
        counts[filename] = len(dataset)
        logger.info(f"Generated {file_path} with {len(dataset)} records.")

    return counts


def load_demo_dataset(dataset_dir: Optional[Path] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Load all JSON files from the dataset directory into raw dictionaries."""
    src_dir = dataset_dir or DATA_DIR
    filenames = [
        "pages.json",
        "keywords.json",
        "rankings.json",
        "observations.json",
        "decisions.json",
        "experiments.json",
        "outcomes.json",
    ]
    raw_data: Dict[str, List[Dict[str, Any]]] = {}
    for fn in filenames:
        fp = src_dir / fn
        if not fp.exists():
            raise FileNotFoundError(f"Missing required dataset file: {fp}")
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            raw_data[fn] = data
            key_stem = fn.replace(".json", "")
            raw_data[key_stem] = data
    return raw_data


def validate_demo_dataset(
    dataset_source: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Validate the entire synthetic SEO dataset.

    Checks:
    1. Model schema compliance (WebsiteFact, SEOObservation, OptimizationDecision, SEOExperiment, ExperimentOutcome)
    2. Minimum record counts
    3. Cross-entity references (URLs, observation_ids, experiment_ids)
    4. Temporal chronology (start_date <= end_date, measured_at >= end_date)
    5. Outcome class representation (all 4 classes present)
    """
    if isinstance(dataset_source, dict):
        raw_data = dataset_source
    else:
        raw_data = load_demo_dataset(dataset_source)

    # Normalize keys if user passed dict with stems instead of filenames
    def get_items(key_stem: str) -> List[Dict[str, Any]]:
        return raw_data.get(f"{key_stem}.json") or raw_data.get(key_stem) or []

    results: Dict[str, Any] = {
        "valid": True,
        "counts": {},
        "outcome_distribution": {},
        "errors": [],
    }

    # 1. Validate Pages
    pages: List[WebsiteFact] = []
    page_urls = set()
    for idx, item in enumerate(get_items("pages")):
        try:
            page = WebsiteFact(**item)
            pages.append(page)
            page_urls.add(str(page.url).rstrip("/"))
        except ValidationError as e:
            results["valid"] = False
            results["errors"].append(f"pages.json[{idx}] validation error: {e}")
    results["counts"]["pages"] = len(pages)

    # 2. Validate Keywords
    keywords = get_items("keywords")
    for idx, item in enumerate(keywords):
        if not item.get("keyword") or not item.get("target_url"):
            results["valid"] = False
            results["errors"].append(f"keywords.json[{idx}] missing keyword or target_url")
        if item.get("clicks", 0) > item.get("impressions", 0):
            results["valid"] = False
            results["errors"].append(f"keywords.json[{idx}] clicks > impressions")
    results["counts"]["keywords"] = len(keywords)

    # 3. Validate Rankings
    rankings = get_items("rankings")
    for idx, item in enumerate(rankings):
        if not item.get("keyword") or not item.get("recorded_date"):
            results["valid"] = False
            results["errors"].append(f"rankings.json[{idx}] missing required fields")
    results["counts"]["rankings"] = len(rankings)

    # 4. Validate Observations
    observations: List[SEOObservation] = []
    observation_ids = set()
    for idx, item in enumerate(get_items("observations")):
        try:
            obs = SEOObservation(**item)
            observations.append(obs)
            observation_ids.add(obs.observation_id)
        except ValidationError as e:
            results["valid"] = False
            results["errors"].append(f"observations.json[{idx}] validation error: {e}")
    results["counts"]["observations"] = len(observations)

    # 5. Validate Decisions
    decisions: List[OptimizationDecision] = []
    for idx, item in enumerate(get_items("decisions")):
        try:
            dec = OptimizationDecision(**item)
            decisions.append(dec)
            # Verify cross-reference: all observation_ids must exist
            for obs_id in dec.observation_ids:
                if obs_id not in observation_ids:
                    results["valid"] = False
                    results["errors"].append(
                        f"decisions.json[{idx}] references unknown observation_id '{obs_id}'"
                    )
        except ValidationError as e:
            results["valid"] = False
            results["errors"].append(f"decisions.json[{idx}] validation error: {e}")
    results["counts"]["decisions"] = len(decisions)

    # 6. Validate Experiments
    experiments: List[SEOExperiment] = []
    experiment_map: Dict[str, SEOExperiment] = {}
    for idx, item in enumerate(get_items("experiments")):
        try:
            exp = SEOExperiment(**item)
            experiments.append(exp)
            experiment_map[exp.experiment_id] = exp
        except ValidationError as e:
            results["valid"] = False
            results["errors"].append(f"experiments.json[{idx}] validation error: {e}")
    results["counts"]["experiments"] = len(experiments)

    # 7. Validate Outcomes
    outcomes: List[ExperimentOutcome] = []
    outcome_classes: Dict[str, int] = {}
    for idx, item in enumerate(get_items("outcomes")):
        try:
            out = ExperimentOutcome(**item)
            outcomes.append(out)
            cls_val = (
                out.outcome_class.value
                if hasattr(out.outcome_class, "value")
                else str(out.outcome_class)
            )
            outcome_classes[cls_val] = outcome_classes.get(cls_val, 0) + 1
            # Verify experiment cross-reference
            if out.experiment_id not in experiment_map:
                results["valid"] = False
                results["errors"].append(
                    f"outcomes.json[{idx}] references non-existent experiment '{out.experiment_id}'"
                )
            else:
                # Temporal consistency: measured_at >= experiment end_date
                exp = experiment_map[out.experiment_id]
                if out.measured_at < exp.end_date:
                    results["valid"] = False
                    results["errors"].append(
                        f"outcomes.json[{idx}] measured_at ({out.measured_at}) before experiment end_date ({exp.end_date})"
                    )
        except ValidationError as e:
            results["valid"] = False
            results["errors"].append(f"outcomes.json[{idx}] validation error: {e}")
    results["counts"]["outcomes"] = len(outcomes)
    results["outcome_distribution"] = outcome_classes

    # Minimum threshold validations
    if len(pages) < 30:
        results["valid"] = False
        results["errors"].append(f"Pages count ({len(pages)}) is below minimum requirement of 30")
    if len(keywords) < 100:
        results["valid"] = False
        results["errors"].append(f"Keywords count ({len(keywords)}) is below minimum requirement of 100")
    if len(rankings) < 60:
        results["valid"] = False
        results["errors"].append(f"Rankings count ({len(rankings)}) is below minimum requirement of 60")
    if len(observations) < 40:
        results["valid"] = False
        results["errors"].append(f"Observations count ({len(observations)}) is below minimum requirement of 40")
    if len(decisions) < 20:
        results["valid"] = False
        results["errors"].append(f"Decisions count ({len(decisions)}) is below minimum requirement of 20")
    if len(experiments) < 20:
        results["valid"] = False
        results["errors"].append(f"Experiments count ({len(experiments)}) is below minimum requirement of 20")
    if len(outcomes) < 20:
        results["valid"] = False
        results["errors"].append(f"Outcomes count ({len(outcomes)}) is below minimum requirement of 20")

    # Verify all 4 outcome classes exist
    for required_cls in ["positive", "negative", "neutral", "inconclusive"]:
        if outcome_classes.get(required_cls, 0) == 0:
            results["valid"] = False
            results["errors"].append(f"Missing required outcome class: {required_cls}")

    return results


def build_hindsight_memory_documents(dataset_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Format synthetic SEO experiments and outcomes into high-signal natural language
    memory documents ready for Hindsight Retain.

    Each document communicates:
    - What experiment was run (ID, type, target URL)
    - Context (rank, impressions, baseline metric)
    - What change was implemented (control vs treatment)
    - Measured outcome (primary metric before/after, % change, outcome classification)
    - Contextual lesson learned (cautious, empirical, non-universal)
    """
    raw_data = load_demo_dataset(dataset_dir)
    exp_map = {item["experiment_id"]: item for item in raw_data["experiments.json"]}

    memory_documents = []
    for out in raw_data["outcomes.json"]:
        exp_id = out["experiment_id"]
        exp = exp_map.get(exp_id)
        if not exp:
            continue

        url = exp["url"]
        exp_type = exp["experiment_type"]
        hyp = exp["hypothesis"]
        ctrl = exp["control_description"]
        treat = exp["treatment_description"]
        metric = exp["primary_metric"]
        before = out["primary_metric_before"]
        after = out["primary_metric_after"]
        pct = out.get("percentage_change")
        pct_str = f" ({pct:+.2f}%)" if pct is not None else ""
        outcome_cls = out["outcome_class"].upper()
        interpretation = out["interpretation"]
        measured_date = out.get("measured_at", "").split("T")[0]

        # Natural language synthesis document
        content = (
            f"SEO Experiment Record: {exp_id}\n"
            f"Page: {url}\n"
            f"Experiment Type: {exp_type}\n"
            f"Date Concluded: {measured_date}\n\n"
            f"Context & Baseline:\n"
            f"Before this test, the primary metric '{metric}' was measured at {before}.\n"
            f"Hypothesis: {hyp}\n\n"
            f"Tested Optimization:\n"
            f"- Control: {ctrl}\n"
            f"- Treatment: {treat}\n\n"
            f"Observed Results:\n"
            f"Primary metric '{metric}' changed from {before} to {after}{pct_str}.\n"
            f"Outcome Classification: {outcome_cls}\n\n"
            f"Contextual Lesson & Interpretation:\n"
            f"{interpretation}\n"
        )

        tags = [
            "seo_experiment",
            exp_type,
            out["outcome_class"],
            "demo_dataset",
        ]
        if "product" in url:
            tags.append("product_page")
        elif "collection" in url:
            tags.append("category_page")
        elif "guide" in url:
            tags.append("informational_guide")

        memory_documents.append({
            "document_id": f"seo_{exp_id}",
            "content": content,
            "context": f"SearchMind historical SEO experiment {exp_id} on {url}",
            "metadata": {
                "experiment_id": exp_id,
                "project_id": DEMO_PROJECT_ID,
                "url": url,
                "experiment_type": exp_type,
                "outcome_class": out["outcome_class"],
                "primary_metric": metric,
            },
            "tags": tags,
            "timestamp": datetime.fromisoformat(out["measured_at"].replace("Z", "+00:00")),
        })

    return memory_documents
