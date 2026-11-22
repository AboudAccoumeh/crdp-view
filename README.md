# CRDP exam paper viewer

A single-page viewer for the official exam papers published by the
[Educational Research and Development Center (CRDP)](https://www.crdp.org/official-exams-corrections-lebanon).

## What is included

- All branches / levels published by CRDP:
  - **Brevet** — Grade 9 (الشهادة المتوسطة)
  - **SE** — Economics & Sociology (اجتماع واقتصاد)
  - **SG** — General Sciences (علوم عامة)
  - **SV** — Life Sciences (علوم الحياة)
  - **SH** — Humanities (آداب وإنسانيات)
- Every session listed on the CRDP page, including the newer 2020–2024
  sessions and the exceptional sessions.
- All subjects, not only the scientific stream.
- Arabic, French and English interface (with RTL support).
- Exam papers, special-needs papers and marking schemes/corrections are
  kept apart so the normal paper is always the first result.

## Regenerating the data

The CRDP site is protected by Cloudflare, which blocks Python requests.
The scraper therefore calls `curl.exe` with a browser user-agent.

```powershell
python -m pip install beautifulsoup4
python scrape.py
```

This writes `data.js` (`window.CRDP_DATA = {...}`). Open `index.html`
directly in a browser, or serve the folder with any static web server.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Viewer UI (vanilla JS, no build step) |
| `data.js` | Scraped exam index |
| `scrape.py` | Scraper that regenerates `data.js` |
