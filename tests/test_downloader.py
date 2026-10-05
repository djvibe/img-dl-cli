import json
import unittest
from unittest.mock import patch

from downloader import ImageDownloader


class FakeAnchor:
    def __init__(self, metadata):
        self.metadata = metadata

    def get_attribute(self, name):
        return json.dumps(self.metadata) if name == "m" else None


class FakeDriver:
    def __init__(self, current_url="", anchors=None):
        self.current_url = current_url
        self.anchors = anchors or []

    def get(self, url):
        if "google.com" in url and not self.current_url:
            self.current_url = url

    def find_elements(self, by, selector):
        return self.anchors if selector == "a.iusc" else []

    def execute_script(self, script):
        return None

    def quit(self):
        return None


class ImageDownloaderTest(unittest.TestCase):
    def setUp(self):
        self.downloader = ImageDownloader("/tmp/img-dl-test", "/tmp/img-dl-test-logs")

    def test_google_captcha_is_explicit(self):
        driver = FakeDriver("https://www.google.com/sorry/index?continue=search")

        urls, status = self.downloader._google_image_urls(
            driver,
            "Goldie",
            "photo",
            5,
        )

        self.assertEqual([], urls)
        self.assertEqual("captcha", status)

    def test_bing_metadata_yields_original_image_urls(self):
        driver = FakeDriver(
            anchors=[
                FakeAnchor({
                    "murl": "https://images.example/goldie-one.jpg",
                    "purl": "https://example.test/goldie-profile",
                    "t": "Goldie portrait",
                }),
                FakeAnchor({
                    "murl": "https://images.example/goldie-two.webp",
                    "purl": "https://example.test/goldie-live",
                    "t": "Goldie performing",
                }),
            ]
        )

        candidates, diagnostics = self.downloader._bing_image_urls(driver, "Goldie", 2)

        self.assertEqual(
            [
                {
                    "url": "https://images.example/goldie-one.jpg",
                    "source_page": "https://example.test/goldie-profile",
                    "title": "Goldie portrait",
                },
                {
                    "url": "https://images.example/goldie-two.webp",
                    "source_page": "https://example.test/goldie-live",
                    "title": "Goldie performing",
                },
            ],
            candidates,
        )
        self.assertEqual(2, diagnostics["bing_cards"])
        self.assertEqual(2, diagnostics["bing_candidates"])
        self.assertEqual(0, diagnostics["bing_rejected_query"])

    def test_bing_metadata_rejects_unrelated_ad_results(self):
        driver = FakeDriver(
            anchors=[
                FakeAnchor({
                    "murl": "https://images.example/voltaren.jpg",
                    "purl": "https://example.test/arthritis-pain",
                    "t": "Voltaren arthritis pain gel",
                }),
            ]
        )

        candidates, diagnostics = self.downloader._bing_image_urls(
            driver,
            "Pacific Coliseum electronic music",
            2,
        )

        self.assertEqual([], candidates)
        self.assertEqual(0, diagnostics["bing_candidates"])
        self.assertGreater(diagnostics["bing_rejected_query"], 0)

    def test_failed_run_reports_provider_and_rejection_counts(self):
        driver = FakeDriver("https://www.google.com/sorry/index?continue=search")
        bing_diagnostics = {
            "bing_cards": 7,
            "bing_candidates": 0,
            "bing_rejected_invalid": 1,
            "bing_rejected_duplicate": 2,
            "bing_rejected_query": 4,
        }

        with patch.object(self.downloader, "_make_driver", return_value=driver):
            with patch.object(
                self.downloader,
                "_bing_image_urls",
                return_value=([], bing_diagnostics),
            ):
                with patch("downloader.time.sleep"):
                    result = self.downloader.download_images("Goldie", 2, 180, "photo")

        self.assertEqual("error", result["status"])
        self.assertEqual("captcha", result["google_status"])
        self.assertEqual(7, result["diagnostics"]["bing_cards"])
        self.assertEqual(4, result["diagnostics"]["bing_rejected_query"])
        self.assertIn(
            "google_status=captcha",
            self.downloader._diagnostics_line(result["diagnostics"]),
        )

    def test_file_type_uses_response_mime_or_magic_bytes(self):
        self.assertEqual("jpg", self.downloader._image_extension("image/jpeg", b"x"))
        self.assertEqual("png", self.downloader._image_extension("", b"\x89PNG\r\n\x1a\nx"))
        self.assertIsNone(self.downloader._image_extension("text/html", b"<html>"))

    def test_query_is_safe_as_a_directory_name(self):
        self.assertEqual("Goldie_Jungle_Daze", self.downloader._safe_name("Goldie / Jungle Daze"))


if __name__ == "__main__":
    unittest.main()
