"""Replacement test_workflow.py (v2)
------------------------------------------------
End‑to‑end smoke‑test for `searchpubmed.pubmed.fetch_pubmed_fulltexts`.
All external HTTP traffic is stubbed so the suite runs offline.
"""

from __future__ import annotations

import textwrap
import requests
import pandas as pd
import searchpubmed.pubmed as p

# ---------------------------------------------------------------------------
# Tiny stand‑in for ``requests.Response``
# ---------------------------------------------------------------------------
class R:  # pragma: no cover – trivial helper
    """A *very* small subset of :pyclass:`requests.Response`."""

    def __init__(self, text: str, code: int = 200):
        self.text = text
        self.content = text.encode()
        self.status_code = code
        self.ok = code == 200

    def raise_for_status(self) -> None:  # pragma: no cover
        if not self.ok:
            raise requests.HTTPError(response=self)

# ---------------------------------------------------------------------------
# Main workflow test
# ---------------------------------------------------------------------------

def test_fetch_pubmed_fulltexts(monkeypatch):
    """Exercise the full workflow with canned XML fixtures."""

    # === 1. XML fixtures =====================================================
    esearch_xml = R(
        textwrap.dedent(
            """
            <eSearchResult>
              <IdList><Id>1</Id><Id>2</Id></IdList>
            </eSearchResult>
            """
        )
    )

    elink_xml = R(
        textwrap.dedent(
            """
            <eLinkResult>
              <LinkSet>
                <IdList><Id>1</Id></IdList>
                <LinkSetDb>
                  <DbTo>pmc</DbTo>
                  <Link><Id>PMC10</Id></Link>
                </LinkSetDb>
              </LinkSet>
            </eLinkResult>
            """
        )
    )

    efetch_xml = R(
        textwrap.dedent(
            """
            <PubmedArticleSet>
              <PubmedArticle>
                <MedlineCitation>
                  <PMID>1</PMID>
                  <Article>
                    <Journal><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
                    <ArticleTitle>T</ArticleTitle>
                    <Abstract><AbstractText>A</AbstractText></Abstract>
                    <AuthorList><Author><LastName>X</LastName></Author></AuthorList>
                  </Article>
                </MedlineCitation>
              </PubmedArticle>
            </PubmedArticleSet>
            """
        )
    )

    # === 2. Monkey‑patch HTTP layer =========================================
    def fake_post(url, *a, **k):
        return esearch_xml if "esearch" in url else elink_xml

    def fake_get(*_a, **_k):
        return efetch_xml

    monkeypatch.setattr(p.requests, "post", fake_post)
    monkeypatch.setattr(p.requests, "get", fake_get)
    monkeypatch.setattr(p.requests.Session, "get", lambda self, url, *a, **k: fake_get(url, *a, **k))

    # Skip back‑off delays
    monkeypatch.setattr(p.time, "sleep", lambda *_: None)

    # Supply minimal PMC‑level metadata so downstream merge succeeds
    monkeypatch.setattr(
        p,
        "get_pubmed_metadata_pmcid",
        lambda pmcids, *a, **k: pd.DataFrame({"pmcid": pmcids})
    )

    # === 3. Run ==============================================================
    df = p.fetch_pubmed_fulltexts("anything", retmax=2)

    # === 4. Assert ===========================================================
    assert list(df.columns) == ["pmid", "pmcid", "title"]
    assert df.iloc[0].pmid == "1"
    assert df.iloc[0].pmcid == "PMC10"
    assert df.iloc[0].title == "T"
