import pytest
from searchpubmed.pubmed import get_jats_text_chunks

SAMPLE_JATS = (
    "<article>"
    "<front><title-group><article-title>Main</article-title></title-group></front>"
    "<body>"
    "<sec><title>Intro</title><p>Intro text.</p></sec>"
    "<sec><title>Results</title>"
        "<sec><title>Sub</title><p>Sub text.</p></sec>"
    "</sec>"
    "<table-wrap><tbody><tr><td>Cell1</td></tr></tbody></table-wrap>"
    "</body>"
    "</article>"
)

NON_JATS = "<PubmedArticle><MedlineCitation /></PubmedArticle>"


def test_basic_chunk_extraction():
    chunks = get_jats_text_chunks(SAMPLE_JATS, min_len=1, include_table_cells=True)
    texts = [c[0] for c in chunks]

    # the parser now keeps section titles as individual chunks
    assert texts == [
        "Main",
        "Intro",
        "Intro text.",
        "Results",
        "Sub",
        "Sub text.",
        "Cell1",
    ]

    # the context for “Sub text.” should still point to section/Sub-section metadata
    idx = texts.index("Sub text.")
    ctx = chunks[idx][1]
    assert ctx["section"] == "Sub"
    assert ctx["parent_sec"] == "Results"


def test_non_jats_rejected():
    with pytest.raises(ValueError):
        get_jats_text_chunks(NON_JATS)
