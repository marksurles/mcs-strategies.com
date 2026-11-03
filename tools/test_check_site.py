"""Unit tests for check_site: each test builds a tiny throwaway site, no network."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_site import check  # noqa: E402

HEAD = ('<head><title>T</title><meta name="description" content="d">'
        '<meta name="viewport" content="w"></head>')
CHROME = '<header class="site-header"><a href="/">h</a></header>'
FOOT = '<footer class="site-footer">f</footer>'


def site(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for name, body in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"<html>{HEAD}<body>{CHROME}{body}{FOOT}</body></html>")
    return root


class CheckSite(unittest.TestCase):
    def test_clean_site_passes(self):
        root = site({"index.html": '<a href="/b.html#x">b</a>', "b.html": '<p id="x">x</p>'})
        self.assertEqual(check(root), [])

    def test_broken_link_and_missing_anchor(self):
        root = site({"index.html": '<a href="/nope.html">n</a><a href="/b.html#y">b</a>',
                     "b.html": "<p>x</p>"})
        out = " ".join(check(root))
        self.assertIn("broken link /nope.html", out)
        self.assertIn("missing anchor /b.html#y", out)

    def test_banned_text_and_private_email(self):
        root = site({"index.html": "<p>TODO " + "mark" + "@" + "mcs-strategies.com</p>"})
        self.assertEqual(len(check(root)), 2)

    def test_docs_folder_is_not_part_of_site(self):
        root = site({"index.html": "<p>ok</p>", "docs/notes.html": "<p>TODO</p>"})
        self.assertEqual(check(root), [])

    def test_header_drift_detected(self):
        root = site({"index.html": "<p>a</p>"})
        (root / "b.html").write_text(f"<html>{HEAD}<body><header class=\"site-header\">other</header>{FOOT}</body></html>")
        self.assertTrue(any("differs" in p for p in check(root)))

    def test_privacy_out_of_sync(self):
        root = site({"index.html": "<p>a</p>", "pillsheet/privacy.html": "<p>old</p>"})
        self.assertTrue(any("out of sync" in p for p in check(root, lambda: "new")))


if __name__ == "__main__":
    unittest.main()
