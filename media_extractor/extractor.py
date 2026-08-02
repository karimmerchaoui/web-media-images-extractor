"""Top-level orchestration: runs the requested platform extractors and
reports a combined summary."""

import logging
import os
from typing import Dict, List, Optional

from .config import DEFAULT_MIN_RESOLUTION, DEFAULT_OUTPUT_DIR
from .google_extractor import GoogleImagesExtractor
from .youtube_extractor import YouTubeExtractor

logger = logging.getLogger(__name__)


class MediaExtractor:
    """Extracts candidate training images from YouTube and Google Images."""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        min_resolution: int = DEFAULT_MIN_RESOLUTION,
    ) -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.youtube = YouTubeExtractor(output_dir, min_resolution=min_resolution)
        self.google = GoogleImagesExtractor(output_dir, min_resolution=min_resolution)

    def extract_all(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, List[str]]:
        """
        Run extraction across the requested platforms and report a summary.

        Args:
            query: Search term.
            platforms: Subset of {'youtube', 'google'} to run. Defaults to both.
            **kwargs: Platform-specific options (max_videos, frames_per_video,
                max_images).

        Returns:
            Mapping of platform name to list of saved file paths.
        """
        if platforms is None:
            platforms = ["youtube", "google"]

        all_results: Dict[str, List[str]] = {}

        if "youtube" in platforms:
            all_results["youtube"] = self.youtube.extract(
                query,
                max_videos=kwargs.get("max_videos", 5),
                frames_per_video=kwargs.get("frames_per_video", 3),
            )

        if "google" in platforms:
            all_results["google"] = self.google.extract(
                query,
                max_images=kwargs.get("max_images", 20),
            )

        self._log_summary(all_results)
        return all_results

    def _log_summary(self, all_results: Dict[str, List[str]]) -> None:
        """Log a summary of results across all extracted platforms."""
        logger.info("\n%s", "=" * 60)
        logger.info("EXTRACTION COMPLETE")
        logger.info("%s", "=" * 60)

        total = 0
        for platform, results in all_results.items():
            count = len(results)
            total += count
            logger.info("%-10s: %d images", platform.capitalize(), count)

        logger.info("%s", "-" * 60)
        logger.info("TOTAL IMAGES: %d", total)
        logger.info("Saved in: %s/", self.output_dir)
        logger.info("%s", "=" * 60)
