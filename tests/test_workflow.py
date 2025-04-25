# tests/test_workflow.py
import searchpubmed.pubmed as p, pytest, requests, textwrap

class R:                 # tiny Response stand-in
    def __init__(self, text: str, code: int = 200):
        self.text = text
        self.content = text.encode()   # <-- Session.get uses .content
        self.status_code = code
        self.ok = code == 200
    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(response=self)

def test_fetch_pubmed_fulltexts(monkeypatch):
    # … all XML fixtures stay the same …

    def fake_post(url, *a, **k):       # ESearch / ELink
        return esearch_xml if "esearch" in url else elink_xml

    def fake_get(*args, **kwargs):     # works for both requests.get & Session.get
        return efetch_xml

    monkeypatch.setattr(p.requests, "post", fake_post)
    monkeypatch.setattr(p.requests, "get",  fake_get)
    monkeypatch.setattr(p.requests.Session, "get",
                        lambda self, url, *a, **k: fake_get(url, *a, **k))

    monkeypatch.setattr(p.time, "sleep", lambda *_: None)   # speed-up

    df = p.fetch_pubmed_fulltexts("anything", retmax=2)

    assert list(df.columns)[:3] == ["pmid", "pmcid", "title"]
    assert df.iloc[0].title == "T"
