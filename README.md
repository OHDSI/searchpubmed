# searchpubmed

A Python package for searching PubMed and retrieving article metadata via the NCBI E-utilities (ESearch, ESummary, EFetch, ELink).

---

![CI](https://github.com/OHDSI/searchpubmed/actions/workflows/python-tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/OHDSI/searchpubmed/branch/main/graph/badge.svg)](https://codecov.io/gh/OHDSI/searchpubmed)


## Features

- Perform complex PubMed searches with boolean operators
- Batch retrieval of PubMed IDs (PMID) and conversion to PMCIDs
- Fetch detailed article metadata (title, abstract, authors, journal, publication date)
- Configurable rate-limiting to comply with NCBI usage policies
- Returns results as pandas DataFrames for seamless analysis

---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
