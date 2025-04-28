# searchpubmed

A Python helper‑library for programmatic PubMed work:

* **Search** – build and run complex boolean queries (E‑Search)
* **Link** – map PMIDs ↔ PMCIDs (E‑Link)
* **Fetch** – pull rich article metadata (E‑Fetch / E‑Summary)
* **Full‑text** – download JATS XML + HTML from PMC
* **Analyse** – get tidy results as *pandas* DataFrames

---

![CI](https://github.com/OHDSI/searchpubmed/actions/workflows/python-tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/OHDSI/searchpubmed/branch/main/graph/badge.svg)](https://codecov.io/gh/OHDSI/searchpubmed)

## Query‑builder

The package now ships with a lightweight **query‑builder** and **five pre‑tuned
strategies** for common real‑world‑data searches.

```python
from searchpubmed import build_query, STRATEGY3_OPTS
print(build_query(STRATEGY3_OPTS)[:120] + "…")
# => (("observational" 5 "ehr"[tiab] OR …) AND english[lang] AND ("2010"[dp] : "3000"[dp]))
```

Create your own `QueryOptions`:

```python
from searchpubmed import QueryOptions, build_query
opts = QueryOptions(
    data_sources=["ehr", "claims"],  # synonym keys
    design_terms=["observational", "secondary"],
    proximity_within=None,
)
print(build_query(opts))
```

---

## Core features

* Perform complex boolean searches (AND/OR/NOT, phrase, proximity *N*)
* Batch retrieval of PMIDs and conversion to PMCIDs
* Fetch detailed metadata (title, abstract, authors, journal, date)
* Configurable rate‑limiting to stay within NCBI usage caps
* Results returned as *pandas* DataFrames for instant analysis

---

## Installation

```bash
pip install searchpubmed
```

---

## License

Apache 2.0 – see the [LICENSE](LICENSE) file for details.

