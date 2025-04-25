"""Extra tests to push overall coverage to 100 %."""
from __future__ import annotations
import builtins, types, textwrap
import pytest, requests, searchpubmed.pubmed as p
from types import SimpleNamespace
# ------------------------------------------------------------------ helpers ---
class _Resp:
    def __init__(self, *, text: str = "", content: bytes | None = None, code=200):
        self.text = text or (content.decode() if content else "")
        self.content = content or self.text.encode()
        self.status_code = code
        self.ok = code == 200
    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(response=self)

GOOD_XML = _Resp(content=b"""<?xml version='1.0'?><articles><article>
  <article-id pub-id-type="pmc">PMC42</article-id>
  <article-id pub-id-type="pmid">4242</article-id>
  <journal-title>J Test</journal-title>
  <article-title>Title!</article-title>
  <abstract><p>Hello</p></abstract>
</article></articles>""")

@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(p.time, "sleep", lambda *_: None)
    yield

# ------------------------------ internal helpers -----------------------------
def test_strip_default_ns():
    raw = b'<a xmlns="x"><b/></a>'
    assert p._strip_default_ns(raw) == b'<a><b/></a>'

# -------------------------- get_pmc_full_xml happy path ----------------------
def test_get_pmc_full_xml(monkeypatch):
    monkeypatch.setattr(p.requests.Session, "get", lambda *a, **k: GOOD_XML)
    df = p.get_pmc_full_xml(["42"])
    assert list(df.columns) == ["pmcid", "fullXML"]
    assert df.loc[0, "pmcid"] == "PMC42"
    assert "<article-id pub-id-type=\"pmc\">PMC42" in df.loc[0, "fullXML"]

# --------------- get_pmc_html_text degrades to 'N/A' after retries -----------
def test_get_pmc_html_text_failure(monkeypatch):
    # always 500 → should return scrapeMsg and "N/A"
    monkeypatch.setattr(p.requests, "get",
                        lambda *_a, **_k: _Resp(text="nope", code=500))
    df = p.get_pmc_html_text(["PMC9"], max_retries=2, delay=0)
    row = df.iloc[0]
    assert row.pmcid == "PMC9" and row.htmlText == "N/A" and row.scrapeMsg

# ---- _scrape_pmc_standard_html succeeds when both other paths are tiny -------
def test_scrape_standard_html(monkeypatch):
    html = _Resp(text="<html><p>big text here</p></html>")
    monkeypatch.setattr(p.requests, "get", lambda *_a, **_k: html)
    out = p._scrape_pmc_standard_html("PMC100")
    assert "big text" in out
