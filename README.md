# mcs-strategies.com

The public website of MCS Strategies, LLC: static HTML/CSS, no build step, served by GitHub Pages
with the custom domain in `CNAME`.

| Path | What it is |
|---|---|
| `index.html`, `products.html`, `work.html`, `about.html`, `404.html` | Pages; all share the header/footer in `index.html` |
| `pillsheet/` | PillSheet support page and the generated Terms & Privacy page |
| `assets/` | Images, the social preview image, icons |
| `tools/build_privacy.py` | Regenerates `pillsheet/privacy.html` from the app's `Terms.swift` (never hand-edit that page) |
| `tools/check_site.py` | Pre-publish gate: links, anchors, placeholders, header drift, privacy sync |

```bash
python3 -m http.server 8765                 # preview at http://localhost:8765/
python3 tools/check_site.py                  # must pass before every commit
python3 -m unittest tools/test_check_site.py
```
