import html
import json
import logging
import os
import re
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Download real web-photo candidates, with Google first and Bing fallback."""

    def __init__(self, download_path: str = "downloads", log_dir: str = "logs"):
        self.download_path = os.path.abspath(download_path)
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    @contextmanager
    def _safe_file_operation(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "temp_image")
        try:
            yield temp_file
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception as error:
                logger.error("Error cleaning temp files: %s", error)

    def download_images(
        self,
        query: str,
        num_images: int = 5,
        min_size_kb: int = 180,
        image_type: str = "photo",
    ) -> Dict:
        """Download high-resolution images using Google, then Bing if blocked."""
        driver = None
        downloaded_files: List[str] = []
        total_attempts = 0

        try:
            logger.info("Starting download for query: %s", query)
            search_dir = os.path.join(self.download_path, self._safe_name(query))
            os.makedirs(search_dir, exist_ok=True)

            driver = self._make_driver()
            google_urls, google_status = self._google_image_urls(
                driver,
                query,
                image_type,
                max(num_images * 8, 30),
            )

            if google_status != "ok":
                logger.warning("Google Images unavailable (%s); using Bing fallback.", google_status)

            downloaded_files, attempts = self._download_candidates(
                google_urls,
                query,
                search_dir,
                num_images,
                min_size_kb,
                source="google",
            )
            total_attempts += attempts

            if len(downloaded_files) < num_images:
                bing_urls = self._bing_image_urls(
                    driver,
                    query,
                    max((num_images - len(downloaded_files)) * 10, 40),
                )
                fallback_files, attempts = self._download_candidates(
                    bing_urls,
                    query,
                    search_dir,
                    num_images - len(downloaded_files),
                    min_size_kb,
                    source="bing",
                    start_index=len(downloaded_files),
                )
                downloaded_files.extend(fallback_files)
                total_attempts += attempts

            if not downloaded_files:
                return {
                    "status": "error",
                    "error": (
                        "Google Images was blocked or returned no qualifying files, "
                        "and the Bing fallback also returned no qualifying files."
                    ),
                    "downloaded": 0,
                    "files": [],
                    "attempts": total_attempts,
                }

            return {
                "status": "success",
                "downloaded": len(downloaded_files),
                "files": downloaded_files,
                "attempts": total_attempts,
                "google_status": google_status,
            }
        except Exception as error:
            logger.exception("Error in download_images: %s", error)
            return {
                "status": "error",
                "error": str(error),
                "downloaded": len(downloaded_files),
                "files": downloaded_files,
                "attempts": total_attempts,
            }
        finally:
            if driver:
                driver.quit()

    def _make_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 Chrome/126 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _google_image_urls(
        self,
        driver,
        query: str,
        image_type: str,
        limit: int,
    ) -> tuple[List[str], str]:
        params = {"q": query, "udm": "2"}
        if image_type == "photo":
            params["tbs"] = "itp:photo"

        driver.get("https://www.google.com/search?" + urllib.parse.urlencode(params))
        time.sleep(2)

        if "/sorry/" in driver.current_url:
            return [], "captcha"

        urls: List[str] = []
        seen = set()
        scrolls = 0

        while len(urls) < limit and scrolls < 8:
            images = driver.find_elements(
                "css selector",
                "img.YQ4gaf, img.rg_i, img.Q4LuWd, img.sFlh5c, img.iPVvYb",
            )

            for image in images:
                for attribute in ("src", "data-src"):
                    url = image.get_attribute(attribute)
                    if self._is_remote_image_url(url) and url not in seen:
                        seen.add(url)
                        urls.append(url)
                        break

                if len(urls) >= limit:
                    break

            if len(urls) >= limit:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            scrolls += 1

        return urls, "ok" if urls else "zero-results"

    def _bing_image_urls(self, driver, query: str, limit: int) -> List[Dict[str, str]]:
        driver.get(
            "https://www.bing.com/images/search?"
            + urllib.parse.urlencode({"q": query, "form": "HDRSC2"})
        )
        time.sleep(2)

        candidates: List[Dict[str, str]] = []
        seen = set()
        scrolls = 0

        while len(candidates) < limit and scrolls < 8:
            for anchor in driver.find_elements("css selector", "a.iusc"):
                raw = anchor.get_attribute("m")
                if not raw:
                    continue

                try:
                    metadata = json.loads(html.unescape(raw))
                except (TypeError, json.JSONDecodeError):
                    continue

                url = metadata.get("murl")
                if (
                    self._is_remote_image_url(url)
                    and url not in seen
                    and self._candidate_matches_query(metadata, query)
                ):
                    seen.add(url)
                    candidates.append(
                        {
                            "url": url,
                            "title": str(metadata.get("t") or ""),
                            "source_page": str(metadata.get("purl") or ""),
                        }
                    )

                if len(candidates) >= limit:
                    break

            if len(candidates) >= limit:
                break

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            scrolls += 1

        return candidates

    def _download_candidates(
        self,
        urls: List[Union[str, Dict[str, str]]],
        query: str,
        search_dir: str,
        wanted: int,
        min_size_kb: int,
        source: str,
        start_index: int = 0,
    ) -> tuple[List[str], int]:
        files: List[str] = []
        attempts = 0
        min_size_bytes = min_size_kb * 1024

        for candidate in urls:
            if len(files) >= wanted:
                break

            metadata = candidate if isinstance(candidate, dict) else {}
            url = metadata.get("url") if metadata else candidate
            if not isinstance(url, str):
                continue

            attempts += 1

            try:
                with self._safe_file_operation() as temp_file:
                    request = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (X11; Linux x86_64) "
                                "AppleWebKit/537.36 Chrome/126 Safari/537.36"
                            ),
                            "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8",
                            "Referer": (
                                "https://www.google.com/"
                                if source == "google"
                                else "https://www.bing.com/"
                            ),
                        },
                    )
                    with urllib.request.urlopen(request, timeout=15) as response:
                        data = response.read()
                        content_type = response.headers.get_content_type()

                    if len(data) < min_size_bytes:
                        continue

                    extension = self._image_extension(content_type, data)
                    if extension is None:
                        continue

                    with open(temp_file, "wb") as output:
                        output.write(data)

                    timestamp = datetime.now().strftime("%H%M%S%f")
                    number = start_index + len(files) + 1
                    filename = (
                        f"{self._safe_name(query)}_{source}_{timestamp}_{number}.{extension}"
                    )
                    path = os.path.join(search_dir, filename)
                    shutil.move(temp_file, path)
                    with open(f"{path}.json", "w", encoding="utf-8") as manifest:
                        json.dump(
                            {
                                "query": query,
                                "source": source,
                                "image_url": url,
                                "source_page": metadata.get("source_page"),
                                "title": metadata.get("title"),
                                "downloaded_at": datetime.now().astimezone().isoformat(),
                            },
                            manifest,
                            indent=2,
                        )
                    files.append(path)
                    logger.info(
                        "Downloaded image %s/%s from %s: %s",
                        number,
                        start_index + wanted,
                        source,
                        filename,
                    )
            except Exception as error:
                logger.debug("Candidate download failed (%s): %s", url, error)

        return files, attempts

    @staticmethod
    def _is_remote_image_url(url: Optional[str]) -> bool:
        return bool(url and re.match(r"^https?://", url) and "gstatic.com/images" not in url)

    @staticmethod
    def _safe_name(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
        return safe[:100] or "image"

    @staticmethod
    def _candidate_matches_query(candidate: Dict, query: str) -> bool:
        ignored = {
            "artist",
            "concert",
            "crowd",
            "event",
            "image",
            "live",
            "music",
            "photo",
            "press",
        }
        tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", query.lower())
            if len(token) >= 4 and token not in ignored
        ]
        if not tokens:
            return False

        haystack = " ".join(
            str(candidate.get(key) or "").lower()
            for key in ("t", "purl", "murl")
        )
        return any(token in haystack for token in tokens)

    @staticmethod
    def _image_extension(content_type: str, data: bytes) -> Optional[str]:
        content_type = (content_type or "").lower()
        if content_type in {"image/jpeg", "image/jpg"} or data.startswith(b"\xff\xd8\xff"):
            return "jpg"
        if content_type == "image/png" or data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if content_type == "image/webp" or (len(data) > 12 and data[8:12] == b"WEBP"):
            return "webp"
        if content_type == "image/gif" or data.startswith((b"GIF87a", b"GIF89a")):
            return "gif"
        return None
