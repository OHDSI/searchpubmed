from __future__ import annotations
"""searchpubmed.query_builder ― opinionated helper for composing PubMed
Boolean expressions **plus five ready‑made strategies**.

Usage examples
--------------
>>> from searchpubmed.query_builder import (
...     QueryOptions, build_query,
...     STRATEGY1_OPTS, STRATEGY2_OPTS, STRATEGY3_OPTS)
>>> print(build_query(STRATEGY1_OPTS)[:120])
(("Databases, Factual"[MeSH] OR "Electronic Health Records"[MeSH] ...

Quick reference
---------------
* :class:`QueryOptions` ― high‑level knobs (data_sources, design_terms,
  start_year, etc.).
* :func:`build_query(opts)` ― turn those knobs into a Boolean string.
* **STRATEGY*\_OPTS** ― pre‑configured :class:`QueryOptions` objects.

------------------------------------------

"""
from dataclasses import dataclass, field
from typing import List, Sequence, Optional

__all__ = [
    # public builder API
    "QueryOptions", "build_query",
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
        '"Routinely Collected Health Data"[MeSH]',
        '"EHR"[TIAB]',
        '"EMR"[TIAB]',
        '"electronic health record"[TIAB]',
        '"electronic medical record"[TIAB]',
    ],
    "claims": [
        '"Insurance Claim Review"[MeSH]',
        '"Insurance Claim Reporting"[MeSH]',
        '"claims data"[TIAB]',
        '"administrative data"[TIAB]',
        '"insurance claims"[TIAB]',
    ],
    "registry": [
        '"Registries"[MeSH]',
        'registry[TIAB]',
        'registry-based[TIAB]',
    ],
    "realworld": [
        '"Databases, Factual"[MeSH]',
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
        '"PharMetrics"[TIAB]',
        '"Symphony Health"[TIAB]',
        '"Premier Healthcare"[TIAB]',
        '"Medicare"[TIAB]',
        '"Medicaid"[TIAB]',    
        '"All-Payer"[TIAB]',
        '"All Payer"[TIAB]',
        '"TriNetX"[TIAB]',
        '"Cerner"[TIAB]',
        '"Komodo"[TIAB]',
        '"Kaiser"[TIAB]',
        '"Explorys"[TIAB]',
        '"The Health Improvement Network"[TIAB]',
        '"Vizient"[TIAB]',
        '"HealthVerity"[TIAB]',
        '"Datavant"[TIAB]',
        '"Merativ"[TIAB]',
    ],
}

_DESIGN_SYNONYMS = {
    "observational": [
        '"Observational Study"[PT]',
        '"Observational Studies as Topic"[MeSH]',
        'observational[TIAB]',
        '"observational study"[TIAB]',
        'observational stud*[TIAB]',
    ],
    "retrospective": [
        '"Retrospective Studies"[MeSH]',
        'retrospective[TIAB]',
        '"retrospective study"[TIAB]',
    ],
    "secondary": [
        '"Secondary Data Analysis"[PT]',
        '"secondary analysis"[TIAB]',
        '"secondary data analysis"[TIAB]',
    ],
    "cohort": [
        '"Cohort Studies"[MeSH]',
        'cohort[TIAB]',
        '"cohort study"[TIAB]',
        'cohort stud*[TIAB]',
    ],
    "case_control": [
        '"Case-Control Studies"[MeSH]',
        '"case-control"[TIAB]',
        '"case control"[TIAB]',
    ],
    "cross_sectional": [
        '"Cross-Sectional Studies"[MeSH]',
        '"cross-sectional"[TIAB]',
        '"cross sectional"[TIAB]',
    ],
    "research_group": [
        '"Health Services Research"[MeSH]',
        '"Outcome Assessment, Health Care"[MeSH]',
        '"Comparative Effectiveness Research"[MeSH]',
    ],
    "prospective": [
        '"Prospective Studies"[MeSH]',
        'prospective[TIAB]',
    ],
    "longitudinal": [
        '"Longitudinal Studies"[MeSH]',
        '"longitudinal study"[TIAB]',
    ],
}

_EXCLUDE_CT_TERMS = (
    '"Clinical Trials as Topic"[MeSH]',
    '"Controlled Clinical Trials as Topic"[MeSH]',
    '"Controlled Clinical Trials as Topic"[MeSH]',
    '"Randomized Controlled Trial"[PT]',
    '"Clinical Trial"[PT]'
)

_EXCLUDE_GENOME_TERMS = (
    'genomic[TIAB]',
    'genome[TIAB]',
    '"Exome Sequencing"[MeSH]',
    '"Genome-Wide Association Study"[MeSH]'
)

_SYSTEMATIC_REVIEW = (
    '"Systematic Review"[PT]',
    '"Systematic Reviews as Topic"[MeSH]'
)

_META_ANALYSIS = (
    '"Meta-Analysis"[PT]',
    '"Meta-Analysis as Topic"[MeSH]'
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
# Five canned QueryOptions presets
# ──────────────────────────────────────────────────────────────

# Strategy 1 – Controlled vocabulary
STRATEGY1_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 2 – Controlled and free-name (max sensitivity)
STRATEGY2_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary", "research_group", "cohort", "longitudinal"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 3 – Controlled and free-name (max sensitivity) AND Proximity coupling (≤5 words)
STRATEGY3_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary", "research_group", "cohort", "longitudinal"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 4 – Controlled and free-name (max sensitivity) AND Tigher Proximity coupling (≤5 words)
STRATEGY4_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 5 – High specificity
STRATEGY5_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 6 – Highest specificity AND Tigher Proximity coupling (≤5 words)
STRATEGY6_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)
