"""Regenerate pillsheet/privacy.html from the app's Terms.swift.

The web policy must say exactly what the app says (App Store review compares them),
so the Swift file is the single source and this page is generated, never hand-edited.
"""
import html, pathlib, re, sys

SRC = pathlib.Path.home() / "Documents/code/Rx/ios/PillSheet/PillSheet/Model/Terms.swift"
OUT = pathlib.Path(__file__).resolve().parent.parent / "pillsheet/privacy.html"

def render() -> str:
    swift = SRC.read_text()
    consts = dict(re.findall(r'static let (\w+) = "([^"]*)"', swift))
    blocks = []
    for title, body in re.findall(r'Section\(title: "([^"]+)", body: """\n(.*?)"""\)', swift, re.S):
        body = body.replace("\\(company)", consts["company"]).replace("\\(contact)", consts["contact"])
        body = re.sub(r"\\\n\s*", "", body)          # Swift line-continuation
        paras = [" ".join(p.split()) for p in body.strip().split("\n\n")]
        ps = "".join(f"<p>{html.escape(p)}</p>\n" for p in paras)
        blocks.append(f"<h2>{html.escape(title)}</h2>\n{ps}")
    if not blocks:
        sys.exit("no sections parsed from Terms.swift")
    # Reuse the site chrome from index.html so this generated page never drifts from the others.
    index = (OUT.parent.parent / "index.html").read_text()
    icons = index[index.index('<link rel="icon"'):index.index('<script type="application/ld+json">')]
    header = index[index.index('<a class="skip"'):index.index('<main id="main">')]
    header = header.replace('<a href="/pillsheet/">', '<a href="/pillsheet/" aria-current="page">')
    footer = index[index.index('<footer class="site-footer">'):]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PillSheet Terms of Use &amp; Privacy Policy | MCS Strategies, LLC</title>
<meta name="description" content="Terms of Use and Privacy Policy for the PillSheet app by MCS Strategies, LLC.">
<link rel="canonical" href="https://mcs-strategies.com/pillsheet/privacy.html">
<meta name="theme-color" content="#0E3A58">
{icons}</head>
<body>
{header}<main id="main">
<section class="plain">
<div class="wrap narrow">
<h1>PillSheet: Terms of Use &amp; Privacy Policy</h1>
<p class="meta">Effective {consts['effective']} · <a href="/pillsheet/">PillSheet</a> · {html.escape(consts['company'])}</p>
{''.join(blocks)}
</div>
</section>
</main>

{footer}"""


def main() -> None:
    OUT.write_text(render())
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
