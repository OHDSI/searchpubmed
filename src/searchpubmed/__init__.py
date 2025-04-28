"""
searchpubmed
============

A lightweight helper-library for:
* searching PubMed (ESearch),
* mapping PMIDs ↔ PMCIDs (ELink),
* pulling PubMed metadata (EFetch),
* downloading full-text JATS XML & HTML from PMC,
* and stitching everything into a single DataFrame.
"""
from __future__ import annotations

__version__: str = "0.1.0"

# ---------------------------------------------------------------------------
# Core PubMed functionality
# ---------------------------------------------------------------------------
from .pubmed import (
    fetch_pubmed_fulltexts,
    get_pmc_full_text,
    get_pmc_full_xml,
    get_pmc_html_text,
    get_pubmed_metadata_pmid,
    get_pubmed_metadata_pmcid,
    map_pmids_to_pmcids,
)

# ---------------------------------------------------------------------------
# Query-builder re-exports
# ---------------------------------------------------------------------------
from .query_builder import (
    QueryOptions,
    build_query,
    STRATEGY1_OPTS,
    STRATEGY2_OPTS,
    STRATEGY3_OPTS,
    STRATEGY4_OPTS,
    STRATEGY5_OPTS,
    STRATEGY6_OPTS,
)

# ---------------------------------------------------------------------------
# Public export list
# ---------------------------------------------------------------------------
__all__: list[str] = [
    # PubMed helpers
    "get_pmid_from_pubmed",  
    "get_pubmed_metadata_pmid",
    "get_pubmed_metadata_pmcid",
    "map_pmids_to_pmcids",
    "get_pmc_full_xml",
    "get_pmc_html_text",
    "get_pmc_full_text",
    "fetch_pubmed_fulltexts",
    # Query-builder helpers
    "QueryOptions",
    "build_query",
    "STRATEGY1_OPTS",
    "STRATEGY2_OPTS",
    "STRATEGY3_OPTS",
    "STRATEGY4_OPTS",
    "STRATEGY5_OPTS",
    "STRATEGY6_OPTS",
    # Meta
    "__version__",
]
