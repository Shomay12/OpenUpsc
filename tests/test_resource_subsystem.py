"""Resource Subsystem Unit & Contract Tests (resource_agent).

Validates UPSC_FREE_RESOURCES_MASTER.md parsing, catalog validation,
idempotent resource enrichment, YouTube playlist/video extraction, and URL hygiene.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from backend import resource_engine as re_mod

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"


class TestResourceSubsystem(unittest.TestCase):
    """Independent verification of the Resource & Curriculum subsystem."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.master_guide = re_mod.parse_master_guide()
        cls.resources_json = json.loads((DATA_DIR / "resources.json").read_text(encoding="utf-8"))

    def test_parse_master_guide_completeness(self) -> None:
        mg = self.master_guide
        parts = mg.get("parts") or []
        self.assertEqual(len(parts), 11, "Master guide must contain all 11 parts.")
        self.assertEqual([p["part_number"] for p in parts], list(range(1, 12)))

        total_unique_links = int(mg.get("meta", {}).get("total_links", 0))
        self.assertGreaterEqual(
            total_unique_links,
            330,
            f"Expected >= 330 unique verified links in master guide, got {total_unique_links}.",
        )

        # Recursively verify every parsed 'url' field across the entire master_guide payload
        all_urls: list[str] = []

        def _collect_urls(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "url" and isinstance(value, str):
                        all_urls.append(value)
                    else:
                        _collect_urls(value)
            elif isinstance(node, list):
                for item in node:
                    _collect_urls(item)

        _collect_urls(mg)
        unique_urls = set(all_urls)
        self.assertGreaterEqual(len(unique_urls), 330)
        for url in unique_urls:
            self.assertTrue(re_mod.is_valid_http_url(url), f"Invalid URL in master guide: {url!r}")
            self.assertNotIn(" & ", url, f"Composite '&' URL detected: {url!r}")

    def test_csat_entries_split_and_clean(self) -> None:
        csat_kit = self.master_guide.get("csat_kit") or []
        self.assertGreaterEqual(len(csat_kit), 14, "Split CSAT entries should yield >= 14 clean items.")
        for entry in csat_kit:
            url = entry.get("url", "")
            self.assertTrue(re_mod.is_valid_http_url(url), f"Invalid CSAT URL: {url!r}")
            self.assertNotIn(" & ", url)
            self.assertTrue(str(entry.get("title") or "").strip())

    def test_part10_optionals_cross_refs_resolved(self) -> None:
        optionals = self.master_guide.get("optionals") or []
        self.assertGreaterEqual(len(optionals), 5, "Expected >= 5 Optional subjects in Part 10.")
        for opt in optionals:
            self.assertTrue(str(opt.get("subject") or "").strip())
            academic = opt.get("academic_links") or []
            videos = opt.get("video_links") or []
            self.assertGreater(
                len(academic) + len(videos),
                0,
                f"Optional subject {opt.get('subject')!r} has no resolved links.",
            )
            for link in academic + videos:
                url = link.get("url", "")
                self.assertTrue(
                    re_mod.is_valid_http_url(url),
                    f"Unresolved or invalid optional cross-ref URL in {opt.get('subject')}: {url!r}",
                )

    def test_validate_catalog_passes_cleanly(self) -> None:
        report = re_mod.validate_catalog()
        self.assertTrue(report.get("valid"), f"Catalog validation failed: {report.get('errors')}")
        self.assertEqual(report.get("errors"), [])
        self.assertEqual(report.get("warnings"), [])
        stats = report.get("stats") or {}
        self.assertGreaterEqual(stats.get("resources_count", 0), 330)
        self.assertEqual(stats.get("master_guide_parts"), 11)
        self.assertGreaterEqual(stats.get("roadmaps_count", 0), 8)
        self.assertGreaterEqual(stats.get("ncert_books_count", 0), 36)

    def test_build_enriched_resources_idempotency_and_original_ids(self) -> None:
        # Original curated IDs (non-master-prefixed) currently in resources.json
        curated_orig = [r for r in self.resources_json if not str(r.get("id", "")).startswith("res-mg-")]
        self.assertEqual(
            len(curated_orig),
            64,
            f"Expected 64 original curated resource IDs to be preserved, found {len(curated_orig)}.",
        )
        orig_ids = {r["id"] for r in curated_orig}

        first_pass = re_mod.build_enriched_resources(curated_orig, self.master_guide)
        second_pass = re_mod.build_enriched_resources(first_pass, self.master_guide)

        first_ids = [r["id"] for r in first_pass]
        second_ids = [r["id"] for r in second_pass]

        self.assertEqual(len(first_ids), len(set(first_ids)), "Duplicate IDs in first enrichment pass.")
        self.assertEqual(first_ids, second_ids, "build_enriched_resources() is not idempotent.")
        self.assertEqual(len(first_pass), len(second_pass))
        self.assertTrue(
            orig_ids.issubset(set(first_ids)),
            f"Missing original curated IDs after enrichment: {orig_ids - set(first_ids)}",
        )
        self.assertEqual(len(first_pass), len(self.resources_json))

    def test_url_validator_rejects_malicious_and_malformed_urls(self) -> None:
        invalid_samples = [
            None,
            "",
            "   ",
            "javascript:alert(1)",
            "JAVASCRIPT:void(0)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "file:///etc/passwd",
            "ftp://example.com/resource.pdf",
            "https://example.com/path with spaces",
            "https://ncert.nic.in/a & https://ncert.nic.in/b",
            "https://example.com/foo&bar",
            "https://example.com/?next=https://other.com",
            "https://user@example.com/test",
            "not-a-url",
            "https://",
        ]
        for bad in invalid_samples:
            self.assertFalse(
                re_mod.is_valid_http_url(bad),  # type: ignore[arg-type]
                f"Expected is_valid_http_url to reject {bad!r}",
            )

        valid_samples = [
            "https://www.upsc.gov.in/",
            "https://ncert.nic.in/textbook.php?fess1=0-10",
            "https://www.youtube.com/playlist?list=PLTWYSxOsBjqH2xjccBt1sxN3X9HwmI8VK",
            "http://example.org/docs?a=1&b=2",
        ]
        for good in valid_samples:
            self.assertTrue(re_mod.is_valid_http_url(good), f"Expected valid URL: {good!r}")

    def test_youtube_playlist_and_video_id_extraction(self) -> None:
        self.assertEqual(
            re_mod.extract_youtube_playlist_id(
                "https://www.youtube.com/playlist?list=PLTWYSxOsBjqH2xjccBt1sxN3X9HwmI8VK"
            ),
            "PLTWYSxOsBjqH2xjccBt1sxN3X9HwmI8VK",
        )
        self.assertEqual(
            re_mod.extract_youtube_playlist_id(
                "https://m.youtube.com/watch?v=dQw4w9WgXcQ&list=PLYSuG-KZy7JBUCNntVK7gzDHGUzGrQW2x"
            ),
            "PLYSuG-KZy7JBUCNntVK7gzDHGUzGrQW2x",
        )
        self.assertIsNone(
            re_mod.extract_youtube_playlist_id("https://example.com/playlist?list=PLTWYSxOsBjqH2xjccBt1sxN3X9HwmI8VK")
        )
        self.assertIsNone(re_mod.extract_youtube_playlist_id("https://www.youtube.com/playlist?list=short"))
        self.assertIsNone(re_mod.extract_youtube_playlist_id("javascript:alert(1)"))

        self.assertEqual(
            re_mod.extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            re_mod.extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ?t=42"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            re_mod.extract_youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertEqual(
            re_mod.extract_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertIsNone(re_mod.extract_youtube_video_id("https://www.youtube.com/watch?v=too_short"))
        self.assertIsNone(re_mod.extract_youtube_video_id("https://vimeo.com/dQw4w9WgXcQ"))


if __name__ == "__main__":
    unittest.main()
