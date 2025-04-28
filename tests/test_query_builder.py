import pytest

from searchpubmed.query_builder import (
    build_query,
    STRATEGY1_OPTS,
    STRATEGY3_OPTS,
    STRATEGY4_OPTS,
    STRATEGY6_OPTS,
    QueryOptions,
)


def _contains(q: str, pieces):
    """Assert that every piece appears (case‑insensitive) in *q*."""
    missing = [p for p in pieces if p.lower() not in q.lower()]
    assert not missing, f"missing {missing}"


# ---------------------------------------------------------------------------
# Strategy‑specific sanity checks
# ---------------------------------------------------------------------------

def test_strategy1_includes_filters_and_not_block():
    """Strategy 1 now includes a NOT block excluding clinical trials."""
    q = build_query(STRATEGY1_OPTS)

    # Core vocabulary & language/date filters
    _contains(q, [
        '"Observational Study"',  # design publication type
        'english[lang]',  # language limiter
    ])

    # Since v0.2 the preset excludes clinical trials – ensure the NOT block is present
    assert 'NOT (' in q
    _contains(q, ['clinical trial'])


def test_strategy3_proximity():
    """Strategy 3 couples design & data terms within five words (adjacency)."""
    q = build_query(STRATEGY3_OPTS)
    assert '"observational" 5 "ehr"[tiab]' in q.lower()


def test_strategy4_not_block():
    """Strategy 4 keeps the NOT block that filters out RCTs and related designs."""
    q = build_query(STRATEGY4_OPTS)
    _contains(q, ['randomized controlled trial'])
    assert 'NOT (' in q


def test_strategy6_high_specificity():
    """Strategy 6 is the most specific: proximity + NOT block present."""
    q = build_query(STRATEGY6_OPTS)
    assert 'NOT (' in q and ' 5 ' in q  # proximity operator still in play


def test_error_on_bad_key():
    """Unknown synonym keys should raise *KeyError*."""
    with pytest.raises(KeyError):
        build_query(QueryOptions(data_sources=['foo']))
