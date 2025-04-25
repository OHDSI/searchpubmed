"""End-to-end smoke-test for fetch_pubmed_fulltexts."""
import searchpubmed.pubmed as p, pytest, requests, textwrap
class R:  # tiny Response stand-in
    def __init__(self, text: str, code=200): self.text, self.status_code, self.ok = text, code, code == 200
    def raise_for_status(self): 
        if not self.ok: raise requests.HTTPError(response=self)

def test_fetch_pubmed_fulltexts(monkeypatch):
    # 1) ESearch returns two PMIDs
    esearch_xml = R(textwrap.dedent("""\
        <eSearchResult><IdList><Id>1</Id><Id>2</Id></IdList></eSearchResult>"""))
    # 2) ELink maps both to one PMC
    elink_xml = R(textwrap.dedent("""\
        <eLinkResult><LinkSet><IdList><Id>1</Id></IdList>
        <LinkSetDb><DbTo>pmc</DbTo><Link><Id>PMC10</Id></Link></LinkSetDb></LinkSet></eLinkResult>"""))
    # 3) EFetch (metadata) returns bare-bones record for PMID 1
    efetch_xml = R(textwrap.dedent("""\
        <PubmedArticleSet><PubmedArticle><MedlineCitation>
        <PMID>1</PMID><Article><Journal><Title>J</Title><JournalIssue>
        <PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>T</ArticleTitle><Abstract><AbstractText>A</AbstractText></Abstract>
        <AuthorList><Author><LastName>X</LastName></Author></AuthorList>
        </Article></MedlineCitation><PubmedData/></PubmedArticle></PubmedArticleSet>"""))
    # map URL → fake response
    def fake_requests_post(url,*a,**k): return esearch_xml if "esearch" in url else elink_xml
    def fake_requests_get(url,*a,**k): return efetch_xml
    monkeypatch.setattr(p.requests, "post", fake_requests_post)
    monkeypatch.setattr(p.requests, "get", fake_requests_get)
    monkeypatch.setattr(p.time, "sleep", lambda *_: None)  # speed
    df = p.fetch_pubmed_fulltexts("anything", retmax=2)
    # We asked for 2 PMIDs, mapped them to one PMC – should still succeed
    assert list(df.columns)[:3] == ["pmid", "pmcid", "title"]
    assert df.iloc[0].title == "T"
