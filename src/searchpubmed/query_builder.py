from __future__ import annotations
"""searchpubmed.query_builder ― opinionated helper for composing PubMed
Boolean expressions **plus five ready‑made strategies**.

Usage examples
--------------
>>> from searchpubmed.query_builder import (
...     QueryOptions, build_query,
...     STRATEGY1_OPTS, STRATEGY2_OPTS, STRATEGY3_OPTS,
...     STRATEGY4_OPTS, STRATEGY5_OPTS)
>>> print(build_query(STRATEGY1_OPTS)[:120])
(("Databases, Factual"[MeSH] OR "Electronic Health Records"[MeSH] ...

Quick reference
---------------
* :class:`QueryOptions` ― high‑level knobs (data_sources, design_terms,
  start_year, etc.).
* :func:`build_query(opts)` ― turn those knobs into a Boolean string.
* **STRATEGY*\_OPTS** ― five pre‑configured :class:`QueryOptions` objects.
* **STRATEGY*\_QUERY** ― frozen Boolean strings (built from the presets).

Canned strategies (2010+, English‑language)
------------------------------------------
===================  ============================================================
Constant name          Design goal
===================  ============================================================
STRATEGY1_OPTS / _QUERY  Highest recall / lowest precision (controlled vocab only)
STRATEGY2_OPTS / _QUERY  Add free‑text synonyms for max sensitivity
STRATEGY3_OPTS / _QUERY  Proximity coupling between design & data terms
STRATEGY4_OPTS / _QUERY  Named databases + moderate NOT block
STRATEGY5_OPTS / _QUERY  High specificity (hedges + strict NOT)
===================  ============================================================
"""
from dataclasses import dataclass, field
from typing import List, Sequence, Optional

__all__ = [
    # public builder API
    "QueryOptions", "build_query",
    # frozen Boolean strings
    "STRATEGY1_QUERY", "STRATEGY2_QUERY", "STRATEGY3_QUERY",
    "STRATEGY4_QUERY", "STRATEGY5_QUERY",
    # QueryOptions presets
    "STRATEGY1_OPTS", "STRATEGY2_OPTS", "STRATEGY3_OPTS",
    "STRATEGY4_OPTS", "STRATEGY5_OPTS",
]

# ──────────────────────────────────────────────────────────────
# Synonym dictionaries (extensible by users)
# ──────────────────────────────────────────────────────────────
_DATA_SOURCE_SYNONYMS = {
    "ehr": [
        '"Electronic Health Records"[MeSH]',
        '"Medical Records Systems, Computerized"[MeSH]',
        '"EHR"[TIAB]',
        '"EMR"[TIAB]',
        '"electronic health record"[TIAB]',
        '"electronic medical record"[TIAB]',
    ],
    "claims": [
        '"Insurance Claim Review"[MeSH]',
        '"claims data"[TIAB]',
        '"administrative data"[TIAB]',
        '"insurance claims"[TIAB]',
    ],
    "registry": [
        '"Registries"[MeSH]',
        'registry[TIAB]',
        'registry-based[TIAB]',
    ],
    "database": [
        '"Databases, Factual"[MeSH]',
        'database[TIAB]',
        'databases[TIAB]',
    ],
    "realworld": [
        '"Real-World Data"[MeSH]',
        '"Real-World Evidence"[MeSH]',
        '"real-world data"[TIAB]',
        '"real-world evidence"[TIAB]',
    ],
    "named": [
        '"SEER"[TIAB]',
        '"NHANES"[TIAB]',
        '"CPRD"[TIAB]',
        '"MarketScan"[TIAB]',
        '"Optum"[TIAB]',
        '"Truven"[TIAB]',
        '"IQVIA"[TIAB]',
    ],
}

_DESIGN_SYNONYMS = {
    "observational": [
        '"Observational Study"[PT]',
        'observational[TIAB]',
    ],
    "retrospective": [
        '"Retrospective Studies"[MeSH]',
        'retrospective[TIAB]',
    ],
    "secondary": [
        '"Secondary Analysis"[PT]',
        '"secondary analysis"[TIAB]',
    ],
    "cohort": [
        '"Cohort Studies"[MeSH]',
        'cohort[TIAB]',
    ],
    "case_control": [
        '"Case-Control Studies"[MeSH]',
        '"case-control"[TIAB]',
    ],
    "cross_sectional": [
        '"Cross-Sectional Studies"[MeSH]',
        '"cross-sectional"[TIAB]',
    ],
}

_EXCLUDE_CT_TERMS = (
    '"Randomized Controlled Trial"[PT]',
    '"Clinical Trial"[PT]',
    '"Systematic Review"[PT]',
    '"Meta-Analysis"[PT]',
    'genomic[TIAB]',
    'genome[TIAB]',
    '"Genome-Wide Association Study"[MeSH]'
)

# ──────────────────────────────────────────────────────────────
# Public dataclass of options
# ──────────────────────────────────────────────────────────────

@dataclass
class QueryOptions:
    """High-level knobs for building a PubMed Boolean expression."""

    data_sources: Sequence[str] = field(default_factory=lambda: ["ehr", "claims", "registry", "database", "realworld", "named"])
    design_terms: Sequence[str] = field(default_factory=lambda: ["observational", "retrospective", "secondary", "cohort", "case_control", "cross_sectional"])
    start_year: Optional[int] = 2010
    end_year: Optional[int] = None    # inclusive
    restrict_english: bool = True
    proximity_within: Optional[int] = None  # if set, apply N operator between design+source term
    exclude_clinical_trials: bool = False

    def _lookup(self, keys: Sequence[str], table: dict[str, List[str]]) -> List[str]:
        found: List[str] = []
        for k in keys:
            if k not in table:
                raise KeyError(f"Unknown key: {k}. Allowed: {list(table)[:10]} …")
            found.extend(table[k])
        return found

# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _apply_proximity(designs: List[str], sources: List[str], N: int) -> List[str]:
    prox_clauses: List[str] = []
    for d in designs:
        d_clean = d.rstrip(']').split('[')[0].strip('"')
        for s in sources:
            s_clean = s.rstrip(']').split('[')[0].strip('"')
            prox_clauses.append(f'"{d_clean}" {N} "{s_clean}"[TIAB]')
    return prox_clauses

# ──────────────────────────────────────────────────────────────
# Core builder
# ──────────────────────────────────────────────────────────────

def build_query(opts: QueryOptions) -> str:
    design_clauses = opts._lookup(opts.design_terms, _DESIGN_SYNONYMS)
    source_clauses = opts._lookup(opts.data_sources, _DATA_SOURCE_SYNONYMS)

    # proximity or simple AND
    if opts.proximity_within is not None:
        prox_parts = _apply_proximity(design_clauses, source_clauses, opts.proximity_within)
        core = "(" + " OR ".join(prox_parts) + ")"
    else:
        core = f"(({' OR '.join(source_clauses)}) AND ({' OR '.join(design_clauses)}))"

    filters: List[str] = []
    if opts.restrict_english:
        filters.append("english[lang]")

    if opts.start_year or opts.end_year:
        s = str(opts.start_year) if opts.start_year else "1800"
        e = str(opts.end_year) if opts.end_year else "3000"
        filters.append(f'("{s}"[dp] : "{e}"[dp])')

    if opts.exclude_clinical_trials:
        filters.append("NOT (" + " OR ".join(_EXCLUDE_CT_TERMS) + ")")

    return " AND ".join([core] + filters)

# ──────────────────────────────────────────────────────────────
# Ready‑made Boolean strings (frozen)
# ──────────────────────────────────────────────────────────────

# … (unchanged STRATEGY*_QUERY constants remain here) …

# ──────────────────────────────────────────────────────────────
# Five canned QueryOptions presets
# ──────────────────────────────────────────────────────────────

# Strategy 1 – Controlled vocabulary sweep
STRATEGY1_OPTS = QueryOptions(
    data_sources=["database", "ehr", "registry", "realworld"],
    design_terms=["observational", "retrospective", "secondary"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=False,
)

# Strategy 2 – Free‑text synonyms (max sensitivity)
STRATEGY2_OPTS = QueryOptions(
    data_sources=["database", "ehr", "registry", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=False,
)

# Strategy 3 – Proximity coupling (≤5 words)
STRATEGY3_OPTS = QueryOptions(
    data_sources=["database", "ehr", "registry", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=False,
)

# Strategy 4 – Named databases + moderate NOT block
STRATEGY4_OPTS = QueryOptions(
    data_sources=["database", "ehr", "registry", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 5 – High specificity (strict NOT + hedges)
STRATEGY5_OPTS = QueryOptions(
    data_sources=["database", "ehr", "registry"],  # fewer to tighten precision
    design_terms=["observational", "retrospective", "secondary", "cohort", "case_control", "cross_sectional"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)
