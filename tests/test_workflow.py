"""Replacement test_workflow.py
------------------------------------------------
A self‑contained smoke‑test for the public
`searchpubmed.pubmed.fetch_pubmed_fulltexts` entry‑point.
The test stubs out **all** network traffic so it can run
completely offline and deterministically in CI.
"""

from __future__ import annotations

import textwrap
import requests
import searchpubmed.pubmed as p

# ---------------------------------------------------------------------------
# Tiny stand‑in for ``requests.Response``
# ---------------------------------------------------------------------------
class R:  # pragma: no cover – trivial helper used only in tests
    """A *very* small subset of :pyclass:`requests.Response`."""

    def __init__(self, text: str, code: int = 200):
        self.text = text
        self.content = text.encode()
        self.status_code = code
        self.ok = code == 200

    # The library under test calls only ``raise_for_status``; provide it.
    def raise_for_status(self) -> None:  # pragma: no cover – trivial helper
        if not self.ok:
            raise requests.HTTPError(response=self)

# ---------------------------------------------------------------------------
# Main workflow test
# ---------------------------------------------------------------------------

def test_fetch_pubmed_fulltexts(monkeypatch):
    """End‑to‑end workflow using canned XML fixtures (no real HTTP)."""

    # --- XML fixtures -------------------------------------------------------
    esearch_xml = R(
        textwrap.dedent(
            """
            <eSearchResult>
                <IdList>
                    <Id>1</Id>
                    <Id>2</Id>
                </IdList>
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
                    <Journal>
                      <JournalIssue>
                        <PubDate><Year>2025</Year></PubDate>
                      </JournalIssue>
                    </Journal>
                    <ArticleTitle>T</ArticleTitle>
                    <Abstract><AbstractText>A</AbstractText></Abstract>
                    <AuthorList>
                      <Author><LastName>X</LastName></Author>
                    </AuthorList>
                  </Article>
                </MedlineCitation>
              </PubmedArticle>
            </PubmedArticleSet>
            """
        )
    )

    # --- HTTP monkey‑patches -----------------------------------------------
    def fake_post(url, *a, **k):
        """Return ESearch for search endpoint, else ELink."""
        return esearch_xml if "esearch" in url else elink_xml

    def fake_get(*_a, **_k):  # covers both ``requests.get`` & ``Session.get``
        return efetch_xml

    monkeypatch.setattr(p.requests, "post", fake_post)
    monkeypatch.setattr(p.requests, "get", fake_get)
    monkeypatch.setattr(
        p.requests.Session,
        "get",
        lambda self, url, *a, **k: fake_get(url, *a, **k),
    )

    # Skip the library's ``time.sleep`` back‑off so the test is instant
    monkeypatch.setattr(p.time, "sleep", lambda *_: None)

    # ------------------------------------------------------------------ run
    df = p.fetch_pubmed_fulltexts("anything", retmax=2)

    # ---------------------------------------------------------------- assert
    assert list(df.columns) == ["pmid", "pmcid", "title"]
    assert df.iloc[0].pmid == "1"
    assert df.iloc[0].pmcid == "PMC10"
    assert df.iloc[0].title == "T"
