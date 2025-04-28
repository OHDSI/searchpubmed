from __future__ import annotations
"""searchpubmed.query_builder – helper for composing PubMed Boolean
expressions plus **six** ready‑made query strategies.
"""

from dataclasses import dataclass, field
from typing import List, Sequence, Optional

__all__ = [
    "QueryOptions", "build_query",
    "STRATEGY1_OPTS", "STRATEGY2_OPTS", "STRATEGY3_OPTS",
    "STRATEGY4_OPTS", "STRATEGY5_OPTS", "STRATEGY6_OPTS",
]

# ──────────────────────────────────────────────────────────────
# Synonym dictionaries (extensible)
# ──────────────────────────────────────────────────────────────

# -------------------- data-source terms --------------------
_DATA_SOURCE_SYNONYMS = {
    "ehr": [
        'Electronic Health Records[MeSH]',
        'Medical Record Systems, Computerized[MeSH]',
        '"routinely collected health data"[MeSH]',
        'EHR[TIAB]',
        'EMR[TIAB]',
        '"electronic health record"[TIAB]',
        '"electronic medical record"[TIAB]',
    ],
    "claims": [
        'Insurance Claim Review[MeSH]',
        'Insurance Claim Reporting[MeSH]',
        '"claims data"[TIAB]',
        '"administrative data"[TIAB]',
        '"insurance claims"[TIAB]',
    ],
    "registry": [
        'Registries[MeSH]',
        'registry[TIAB]',
        'registry-based[TIAB]',
    ],
    "realworld": [
        'Databases, Factual[MeSH]',
        '"Real-World Data"[TIAB]',
        '"Real-World Evidence"[TIAB]',
        '"real-world data"[TIAB]',
        '"real-world evidence"[TIAB]',
    ],
    "named": [
        '"SEER"[TIAB]', '"NHANES"[TIAB]', '"CPRD"[TIAB]',
        '"MarketScan"[TIAB]', '"Optum"[TIAB]', '"Truven"[TIAB]',
        '"IQVIA"[TIAB]', '"PharMetrics"[TIAB]', '"Symphony Health"[TIAB]',
        '"Premier Healthcare"[TIAB]', '"Medicare"[TIAB]', '"Medicaid"[TIAB]',
        '"All-Payer"[TIAB]', '"All Payer"[TIAB]', '"TriNetX"[TIAB]',
        '"Cerner"[TIAB]', '"Komodo"[TIAB]', '"Kaiser"[TIAB]', '"Explorys"[TIAB]',
        '"The Health Improvement Network"[TIAB]', '"Vizient"[TIAB]',
        '"HealthVerity"[TIAB]', '"Datavant"[TIAB]', '"Merative"[TIAB]',
    ],
}

# -------------------- study-design terms --------------------
_DESIGN_SYNONYMS = {
    "observational": [
        'Observational Study[PT]',    
        'Observational Studies as Topic[MeSH]',
        'observational[TIAB]',
        '"observational study"[TIAB]',
        'observational stud*[TIAB]',
    ],
    "retrospective": [
        'Retrospective Studies[MeSH]',
        'retrospective[TIAB]',
        '"retrospective study"[TIAB]',
    ],
    "secondary": [
        'Secondary Data Analysis[MeSH]',
        '"secondary analysis"[TIAB]',
        '"secondary data analysis"[TIAB]',
    ],
    "cohort": [
        'Cohort Studies[MeSH]',
        'cohort[TIAB]',
        '"cohort study"[TIAB]',
        'cohort stud*[TIAB]',
    ],
    "case_control": [
        'Case-Control Studies[MeSH]',
        '"case-control"[TIAB]',
        '"case control"[TIAB]',
    ],
    "cross_sectional": [
        'Cross-Sectional Studies[MeSH]',
        '"cross-sectional"[TIAB]',
        '"cross sectional"[TIAB]',
    ],
    "research_group": [
        'Health Services Research[MeSH]',
        'Outcome Assessment, Health Care[MeSH]',
        'Comparative Effectiveness Research[MeSH]',
    ],
    "prospective": [
        'Prospective Studies[MeSH]',
        'prospective[TIAB]',
    ],
    "longitudinal": [
        'Longitudinal Studies[MeSH]',
        '"longitudinal study"[TIAB]',
    ],
}

# -------------------- exclusion terms --------------------
_EXCLUDE_CT_TERMS = (
    'Clinical Trials as Topic[MeSH]',
    'Controlled Clinical Trials as Topic[MeSH]',
    'Randomized Controlled Trial[PT]',
    'Clinical Trial[PT]',
)


# ──────────────────────────────────────────────────────────────
# Public dataclass of options
# ──────────────────────────────────────────────────────────────

@dataclass
class QueryOptions:
    """High‑level knobs for building a PubMed Boolean query."""

    data_sources: Sequence[str] = field(default_factory=lambda: [
        "ehr", "claims", "registry", "realworld", "named"
    ])
    design_terms: Sequence[str] = field(default_factory=lambda: [
        "observational", "retrospective", "secondary", "cohort",
        "case_control", "cross_sectional"
    ])
    start_year: Optional[int] = 2010
    end_year: Optional[int] = None  # inclusive
    restrict_english: bool = True
    proximity_within: Optional[int] = None  # N‑word proximity
    exclude_clinical_trials: bool = False

    def _lookup(self, keys: Sequence[str], table: dict[str, List[str]]) -> List[str]:
        out: List[str] = []
        for k in keys:
            try:
                out.extend(table[k])
            except KeyError as exc:
                raise KeyError(
                    f"Unknown key '{k}'.  Allowed: {list(table)[:10]} …"
                ) from exc
        return out

# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _apply_proximity(designs: List[str], sources: List[str], N: int) -> List[str]:
    prox: List[str] = []
    for d in designs:
        d_clean = d.rstrip("]").split("[")[0].strip('"')
        for s in sources:
            s_clean = s.rstrip("]").split("[")[0].strip('"')
            prox.append(f'"{d_clean}" {N} "{s_clean}"[TIAB]')
    return prox

# ──────────────────────────────────────────────────────────────
# Core builder
# ──────────────────────────────────────────────────────────────

def build_query(opts: QueryOptions) -> str:
    """Return a PubMed Boolean expression assembled from *opts*."""
    design = opts._lookup(opts.design_terms, _DESIGN_SYNONYMS)
    source = opts._lookup(opts.data_sources, _DATA_SOURCE_SYNONYMS)

    # core concept(s)
    if opts.proximity_within is not None:
        prox_parts = _apply_proximity(design, source, opts.proximity_within)
        core = f"({' OR '.join(prox_parts)})"
    else:
        core = f"(({' OR '.join(source)}) AND ({' OR '.join(design)}))"

    # optional filters
    parts: List[str] = [core]

    if opts.restrict_english:
        parts.append("english[lang]")

    if opts.start_year or opts.end_year:
        s = str(opts.start_year or 1800)
        e = str(opts.end_year or 3000)
        parts.append(f'("{s}"[dp] : "{e}"[dp])')

    if opts.exclude_clinical_trials:
        parts.append("NOT (" + " OR ".join(_EXCLUDE_CT_TERMS) + ")")

    # PubMed treats whitespace as an implicit AND, so no explicit “AND NOT” appears
    return " ".join(parts)



# ──────────────────────────────────────────────────────────────
# Strategy presets – identical semantics to upstream
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

# Strategy 2 – Controlled + named data sources (max sensitivity)
STRATEGY2_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=[
        "observational", "retrospective", "secondary", "research_group",
        "cohort", "longitudinal",
    ],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 3 – Strategy 2 with proximity coupling (≤ 5 words)
STRATEGY3_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=[
        "observational", "retrospective", "secondary", "research_group",
        "cohort", "longitudinal",
    ],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 4 – Drop cohort/longitudinal, keep proximity (specific)
STRATEGY4_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld", "named"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 5 – Highest specificity (no named sources, no proximity)
STRATEGY5_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=None,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)

# Strategy 6 – Like Strategy 5 but with proximity (specific + context)
STRATEGY6_OPTS = QueryOptions(
    data_sources=["ehr", "claims", "realworld"],
    design_terms=["observational", "retrospective", "secondary", "research_group"],
    proximity_within=5,
    restrict_english=True,
    start_year=2010,
    exclude_clinical_trials=True,
)
