"""Google Images search and download, gated by the shared resolution check."""

import logging
import time
from typing import List

from selenium.webdriver.common.by import By

from . import driver_utils
from .config import (
    DEFAULT_MIN_RESOLUTION,
    GOOGLE_HIGH_RES_SELECTOR,
    GOOGLE_MAX_SCROLLS,
    GOOGLE_RESULTS_XPATH,
    PAGE_LOAD_PAUSE_SECONDS,
    SCROLL_PAUSE_SECONDS,
)
from .image_utils import load_and_save_if_valid

logger = logging.getLogger(__name__)


class GoogleImagesExtractor:
    """Searches Google Images for a query and downloads matching images."""

    def __init__(self, output_dir: str, min_resolution: int = DEFAULT_MIN_RESOLUTION) -> None:
        self.output_dir = output_dir
        self.min_resolution = min_resolution

    def extract(self, query: str, max_images: int = 20) -> List[str]:
        """
        Search Google Images for a query and download images passing the
        resolution quality gate.

        Returns:
            List of file paths for saved images.
        """
        logger.info("\n[Google Images] Searching: %s", query)
        results: List[str] = []
        driver = None

        try:
            driver = driver_utils.create_driver()
            driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch")
            time.sleep(PAGE_LOAD_PAUSE_SECONDS)

            for _ in range(GOOGLE_MAX_SCROLLS):
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(SCROLL_PAUSE_SECONDS)

            image_elements = driver.find_elements(By.XPATH, GOOGLE_RESULTS_XPATH)
            logger.info("  Found %d candidate images", len(image_elements))

            for i, element in enumerate(image_elements[:max_images], 1):
                img_url = self._resolve_image_url(driver, element)

                if not img_url:
                    logger.info("  [%d/%d] Skipped: no valid image URL", i, max_images)
                    continue

                filepath = load_and_save_if_valid(
                    img_url, self.output_dir, prefix=f"google_{i}", min_resolution=self.min_resolution
                )
                if filepath:
                    results.append(filepath)
                    logger.info("  [%d/%d] Saved image", i, max_images)
                else:
                    logger.info("  [%d/%d] Skipped: resolution too small", i, max_images)
        finally:
            driver_utils.quit_driver(driver)

        return results

    def _resolve_image_url(self, driver, element) -> str:
        """Get a usable image URL from a search result element, clicking
        through to a high-resolution version if the thumbnail src isn't
        directly usable."""
        img_url = element.get_attribute("src")

        if not img_url or not img_url.startswith("http"):
            driver.execute_script("arguments[0].click();", element)
            time.sleep(1)
            high_res = driver.find_elements(By.CSS_SELECTOR, GOOGLE_HIGH_RES_SELECTOR)
            if high_res:
                img_url = high_res[0].get_attribute("src")

        return img_url if img_url and img_url.startswith("http") else ""
