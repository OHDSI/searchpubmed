from __future__ import annotations
"""searchpubmed
============

A lightweight helper-library for:
* searching PubMed (ESearch),
* mapping PMIDs ↔ PMCIDs (ELink),
* pulling PubMed metadata (EFetch),
* downloading full-text JATS XML & HTML from PMC,
* and stitching everything into a single DataFrame.
"""

# ---------------------------------------------------------------------------
# Public re-export list
# ---------------------------------------------------------------------------

__all__: list[str] = [
    # core pubmed helpers
    "get_pubmed_metadata_pmid",
    "get_pubmed_metadata_pmcid",
    "map_pmids_to_pmcids",
    "get_pmc_full_xml",
    "get_pmc_html_text",
    "get_pmc_full_text",
    "fetch_pubmed_fulltexts",
    # query-builder surface
    "QueryOptions",
    "build_query",
    "STRATEGY1_OPTS",
    "STRATEGY2_OPTS",
    "STRATEGY3_OPTS",
    "STRATEGY4_OPTS",
    "STRATEGY5_OPTS",
    # package meta
    "__version__",
]

__version__: str = "0.1.0"

# ---------------------------------------------------------------------------
# Core PubMed functionality (unchanged)
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
# Query-builder re-exports (minimal wiring)
# ---------------------------------------------------------------------------

from .query_builder import (
    QueryOptions,
    build_query,
    STRATEGY1_OPTS,
    STRATEGY2_OPTS,
    STRATEGY3_OPTS,
    STRATEGY4_OPTS,
    STRATEGY5_OPTS,
)
