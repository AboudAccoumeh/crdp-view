# Official Exam Papers

A single-page, offline-capable viewer for official Lebanese exam papers.
Papers are sourced from [CRDP](https://www.crdp.org/official-exams-corrections-lebanon);
the source is credited only in a small link at the bottom of the page.

## What is included

- All branches / levels:
  - **Brevet** — Grade 9
  - **SE** — Economics & Sociology
  - **SG** — General Sciences
  - **SV** — Life Sciences
  - **SH** — Humanities
- Every session listed on the source page, including 2021–2024 and the
  exceptional sessions. (The 2020 listing exists but contains no documents.)
- All subjects, not only the scientific stream.
- Arabic, French and English interface, with RTL support for Arabic.
- Normal papers are shown first. Marking schemes are separated, and
  special-needs / blind papers are hidden by default behind a clearly
  labelled toggle that shows how many are hidden.
- Installable progressive web app (PWA) with an offline app shell.

## Deploying to GitHub Pages

1. Push every file in this folder to your repository.
2. In the repository, open **Settings → Pages → Build and deployment**.
3. Set **Source** to `Deploy from a branch`, then pick `main` / `root` and save.
4. Open `https://<username>.github.io/<repository>/`.

All URLs in the manifest, service worker and page are relative, so the app
works both from a GitHub Pages project subpath and from a custom domain root.
`.nojekyll` makes sure GitHub serves the files untouched.

**Installing on a phone**

- Android / Chrome or Edge: visit the site once online. An **Install app**
  button appears in the header; tap it, or use the browser menu → *Install app*.
- iPhone / Safari: visit the site, then **Share → Add to Home Screen**.

The first visit must be online so the service worker can cache the app.
After that, the interface and the whole exam index work offline; opening a
PDF link still needs an internet connection.

## Regenerating the data

The source site is protected by Cloudflare, which blocks Python requests.
`scrape.py` therefore calls `curl.exe` with a browser user-agent (no visible
browser window, so no reCAPTCHA popup).

```powershell
python -m pip install beautifulsoup4
python scrape.py
```

This rewrites `data.js`. The icon set can be regenerated with
`python make_icons.py` (requires Pillow).

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Viewer UI (vanilla JS, no build step) |
| `data.js` | Generated exam PDF index |
| `scrape.py` | Scraper that regenerates `data.js` |
| `manifest.webmanifest` | PWA metadata |
| `sw.js` | Service worker (offline caching) |
| `icons/` | PWA icons (192/512, normal and maskable) |
| `favicon.ico`, `favicon.svg` | Browser tab icons |
| `make_icons.py` | Regenerates `icons/` and the favicons |
| `.nojekyll` | Tells GitHub Pages to serve files as-is |
