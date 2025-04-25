"""Comprehensive test suite for searchpubmed.pubmed

All network‑bound functions are exercised with monkey‑patched stand‑ins, so no
HTTP traffic is generated.  The goal is to cover all public helpers in
``searchpubmed.pubmed`` and, crucially, all error‑handling branches that were
only partially tested in the original suite.
"""

from __future__ import annotations

import textwrap
from types import SimpleNamespace

import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
import requests

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

class DummyResp:
    """Lightweight replacement for :class:`requests.Response`."""

    def __init__(self, *, text: str | None = None, content: bytes | None = None,
                 status: int = 200):
        self.status_code = status
        self.ok = status == 200
        self.text = text or (content.decode() if isinstance(content, bytes) else "")
        self.content = content or self.text.encode()

    def raise_for_status(self) -> None:
        if not self.ok:
            raise requests.HTTPError(response=self)

# For convenience we re‑use the same response instance in several tests
_OK_XML = DummyResp(content=b"""<?xml version='1.0'?>
<eSearchResult>
  <IdList>
    <Id>111</Id><Id>222</Id><Id>111</Id>
  </IdList>
</eSearchResult>""")

@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    """Skip ``time.sleep`` calls so the test suite is instant."""
    import searchpubmed.pubmed as p
    monkeypatch.setattr(p.time, "sleep", lambda *_: None)
    yield


# --------------------------------------------------------------------------- #
# get_pmid_from_pubmed()                                                      #
# --------------------------------------------------------------------------- #

def test_get_pmid_success(monkeypatch):
    import searchpubmed.pubmed as p

    monkeypatch.setattr(p.requests, "post", lambda *a, **k: _OK_XML)
    pmids = p.get_pmid_from_pubmed("cancer")

    assert pmids == ["111", "222"], "Duplicates should be removed while preserving order"


def test_get_pmid_retries_then_success(monkeypatch):
    import searchpubmed.pubmed as p

    calls = {"n": 0}

    def flaky(*_args, **_kw):
        calls["n"] += 1
        # first call → 500, second → OK
        if calls["n"] == 1:
            return DummyResp(text="boom", status=500)
        return _OK_XML

    monkeypatch.setattr(p.requests, "post", flaky)
    out = p.get_pmid_from_pubmed("test", max_retries=2, delay=0)

    assert calls["n"] == 2  # one retry happened
    assert out == ["111", "222"]


def test_get_pmid_total_failure(monkeypatch):
    import searchpubmed.pubmed as p

    monkeypatch.setattr(p.requests, "post",
                        lambda *_a, **_k: (_ for _ in ()).throw(
                            requests.RequestException("network down")))
    assert p.get_pmid_from_pubmed("x") == []


# --------------------------------------------------------------------------- #
# map_pmids_to_pmcids()                                                       #
# --------------------------------------------------------------------------- #

_ELINK_XML = DummyResp(content=b"""<?xml version='1.0'?>
<eLinkResult>
  <LinkSet>
    <IdList><Id>111</Id></IdList>
    <LinkSetDb>
      <DbTo>pmc</DbTo>
      <Link><Id>PMC555</Id></Link>
      <Link><Id>PMC555</Id></Link>
    </LinkSetDb>
  </LinkSet>
</eLinkResult>""")

def test_map_pmids_basic(monkeypatch):
    import searchpubmed.pubmed as p

    # Patch *method* on Session so all instances share the stub
    monkeypatch.setattr(p.requests.Session, "post", lambda *_a, **_k: _ELINK_XML)

    df = p.map_pmids_to_pmcids(["111", "111"])
    expected = pd.DataFrame({"pmid": ["111"], "pmcid": ["PMC555"]}, dtype="string")

    assert_frame_equal(df, expected)


def test_map_pmids_http_error(monkeypatch):
    import searchpubmed.pubmed as p

    # always 500 → function should degrade to <NA>
    monkeypatch.setattr(p.requests.Session, "post",
                        lambda *_a, **_k: DummyResp(text="fail", status=500))

    df = p.map_pmids_to_pmcids(["42"])
    assert pd.isna(df.loc[0, "pmcid"])


# --------------------------------------------------------------------------- #
# get_pubmed_metadata_pmid()                                                  #
# --------------------------------------------------------------------------- #

_EFETCH_XML = DummyResp(content=textwrap.dedent("""\
<?xml version='1.0'?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <Journal>
          <Title>J Awesome</Title>
          <JournalIssue>
            <PubDate><Year>2024</Year><Month>Jan</Month><Day>15</Day></PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>A great discovery</ArticleTitle>
        <Abstract><AbstractText>Stuff</AbstractText></Abstract>
        <AuthorList>
          <Author><LastName>Doe</LastName><ForeName>Jane</ForeName></Author>
          <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
        </AuthorList>
      </Article>
      <MeshHeadingList>
        <MeshHeading><DescriptorName>Cats</DescriptorName></MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType=\"doi\">10.1/xyz</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>""").encode())

def test_metadata_parsing(monkeypatch):
    import searchpubmed.pubmed as p
    monkeypatch.setattr(p.requests.Session, "get", lambda *_a, **_k: _EFETCH_XML)

    df = p.get_pubmed_metadata_pmid(["111", "111"])

    assert list(df.columns) == [
        "pmid", "title", "abstract", "journal", "publicationDate", "doi",
        "firstAuthor", "lastAuthor", "authorAffiliations", "meshTags", "keywords"
    ]
    row = df.iloc[0]
    assert row.pmid == "111"
    assert row.title == "A great discovery"
    assert row.publicationDate.startswith("2024-01-15"[:7])  # allow YYYY-MM
    assert row.firstAuthor == "Jane Doe"
    assert row.lastAuthor == "John Smith"
    # meshTags collapsed
    assert row.meshTags == "Cats"


def test_metadata_http_failure(monkeypatch):
    import searchpubmed.pubmed as p
    monkeypatch.setattr(p.requests.Session, "get",
                        lambda *_a, **_k: DummyResp(text="nope", status=500))

    df = p.get_pubmed_metadata_pmid(["999"])
    assert (df.drop(columns=["pmid"]) == "N/A").all(axis=None)


# --------------------------------------------------------------------------- #
# get_pmc_full_text()                                                         #
# --------------------------------------------------------------------------- #

def test_full_text_html_then_xml(monkeypatch):
    import searchpubmed.pubmed as p

    calls = {"n": 0}

    def fake_get(url, *_, **__):
        calls["n"] += 1
        if "?format=flat" in url:
            # very short HTML so that fallback is triggered
            return DummyResp(text="<p>tiny</p>")
        elif "efetch.fcgi" in url:
            xml = """<article><body><p>Very long text here</p></body></article>"""
            return DummyResp(content=xml.encode())
        raise AssertionError("Unexpected URL")

    monkeypatch.setattr(p.requests, "get", fake_get)

    out = p.get_pmc_full_text("123", xml_fallback_min_chars=20)
    assert out == {"PMC123": "Very long text here"}  # PMC prefix added, XML used
    assert calls["n"] == 2  # HTML + XML


def test_full_text_complete_failure(monkeypatch):
    import searchpubmed.pubmed as p

    monkeypatch.setattr(p.requests, "get",
                        lambda *_a, **_k: (_ for _ in ()).throw(
                            requests.RequestException("boom")))

    out = p.get_pmc_full_text(["PMC1", "PMC2"])
    assert out == {"PMC1": "N/A", "PMC2": "N/A"}

