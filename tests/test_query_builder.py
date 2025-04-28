import re
import pytest
from searchpubmed.query_builder import (
    build_query, STRATEGY1_OPTS, STRATEGY2_OPTS, STRATEGY3_OPTS,
    STRATEGY4_OPTS, STRATEGY5_OPTS, QueryOptions
)

def _contains(q, pieces):
    missing = [p for p in pieces if p.lower() not in q.lower()]
    assert not missing, f"missing {missing}"

def test_strategy1():
    q = build_query(STRATEGY1_OPTS)
    _contains(q, ['"Databases, Factual"', '"Observational Study"', 'english[lang]'])
    assert 'NOT (' not in q

def test_strategy3_proximity():
    q = build_query(STRATEGY3_OPTS)
    assert '"observational" 5 "ehr"[tiab]' in q.lower()

def test_not_block():
    q = build_query(STRATEGY4_OPTS)
    assert 'randomized controlled trial' in q.lower() and 'NOT (' in q

def test_error_on_bad_key():
    with pytest.raises(KeyError):
        build_query(QueryOptions(data_sources=['foo']))
