"""
tests/test_pmcid.py

Smoke-tests for searchpubmed.pubmed.get_pubmed_metadata_pmcid.
* success  → correctly-filled DataFrame with canonical column order
* failure  → placeholder row filled with "N/A"
"""

from __future__ import annotations

import textwrap
import requests
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import searchpubmed.pubmed as p


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
_XML_OK = textwrap.dedent(
    """\
    <articles>
      <article>
        <article-id pub-id-type="pmcid">PMC123</article-id>
        <article-id pub-id-type="pmid">999</article-id>
        <journal-title>J</journal-title>
        <article-title>T</article-title>
        <pub-date>
          <year>2023</year><month>06</month><day>30</day>
        </pub-date>
        <abstract><p>A</p></abstract>
        <mesh-heading-list>
          <mesh-heading>
            <descriptor-name>Cats</descriptor-name>
          </mesh-heading>
        </mesh-heading-list>
      </article>
    </articles>
    """
).encode()


class _Resp:  # ultra-light requests.Response stub
    def __init__(self, *, ok: bool = True, content: bytes = b""):
        self.ok = ok
        self.content = content
        self.status_code = 200 if ok else 500

    def raise_for_status(self):  # emulate requests’ interface
        if not self.ok:
            raise requests.HTTPError(response=self)


# --------------------------------------------------------------------------- #
# tests                                                                       #
# --------------------------------------------------------------------------- #
def test_get_pubmed_metadata_pmcid_success(monkeypatch):
    """One well-formed record should yield a one-row DataFrame."""
    monkeypatch.setattr(p.requests.Session, "get", lambda *_a, **_k: _Resp(content=_XML_OK))

    df = p.get_pubmed_metadata_pmcid(["PMC123"])

    expected = pd.DataFrame(
        {
            "pmcid": ["PMC123"],
            "pmid": ["999"],
            "title": ["T"],
            "abstract": ["A"],
            "journal": ["J"],
            "publicationDate": ["2023-06-30"],
            "doi": ["N/A"],
            "firstAuthor": ["N/A"],
            "lastAuthor": ["N/A"],
            "authorAffiliations": ["N/A"],
            "meshTags": ["Cats"],
            "keywords": ["N/A"],
        },
        dtype="string",
    )

    assert_frame_equal(df, expected)


def test_get_pubmed_metadata_pmcid_http_error(monkeypatch):
    """HTTP 500 after retries should return a placeholder row filled with 'N/A'."""
    monkeypatch.setattr(p.requests.Session, "get", lambda *_a, **_k: _Resp(ok=False))

    df = p.get_pubmed_metadata_pmcid(["PMC999"])

    # canonical column order — pmcid must come first
    assert list(df.columns) == [
        "pmcid",
        "pmid",
        "title",
        "abstract",
        "journal",
        "publicationDate",
        "doi",
        "firstAuthor",
        "lastAuthor",
        "authorAffiliations",
        "meshTags",
        "keywords",
    ]

    row = df.iloc[0]
    assert row.pmcid == "PMC999"
    assert (row.drop(labels=["pmcid"]) == "N/A").all()
