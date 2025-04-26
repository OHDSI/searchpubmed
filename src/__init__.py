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

__all__: list[str] = [
    "get_pubmed_metadata_pmid",
    "get_pubmed_metadata_pmcid",
    "map_pmids_to_pmcids",
    "get_pmc_full_xml",
    "get_pmc_html_text",
    "get_pmc_full_text",
    "fetch_pubmed_fulltexts",
    "__version__",
]

__version__: str = "0.1.0"

from .pubmed import (
    fetch_pubmed_fulltexts,
    get_pmc_full_text,
    get_pmc_full_xml,
    get_pmc_html_text,
    get_pubmed_metadata_pmid,
    get_pubmed_metadata_pmcid,
    map_pmids_to_pmcids,
)

