"""YouTube video discovery, download, and uniform frame sampling."""

import logging
import os
import time
from typing import List

from selenium.webdriver.common.by import By

from . import driver_utils
from .config import (
    DEFAULT_MIN_RESOLUTION,
    PAGE_LOAD_PAUSE_SECONDS,
    SCROLL_PAUSE_SECONDS,
    TEMP_VIDEO_FILENAME,
    YOUTUBE_MAX_SCROLLS,
)
from .frame_sampling import sample_frame_indices

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Finds YouTube videos for a query and extracts uniformly sampled frames."""

    def __init__(self, output_dir: str, min_resolution: int = DEFAULT_MIN_RESOLUTION) -> None:
        self.output_dir = output_dir
        self.min_resolution = min_resolution

    def extract(
        self,
        query: str,
        max_videos: int = 5,
        frames_per_video: int = 3,
    ) -> List[str]:
        """
        Search YouTube for a query, download matching videos, and save
        uniformly sampled frames from each.

        Returns:
            List of file paths for saved frames.
        """
        logger.info("\n[YouTube] Searching: %s", query)
        results: List[str] = []
        driver = None

        try:
            driver = driver_utils.create_driver()
            video_urls = self._collect_video_urls(driver, query, max_videos)
            logger.info("  Found %d videos", len(video_urls))
        finally:
            driver_utils.quit_driver(driver)

        for i, url in enumerate(video_urls, 1):
            logger.info("  [%d/%d] Processing video...", i, len(video_urls))
            try:
                frames = self._process_video(url, frames_per_video)
                results.extend(frames)
                logger.info("    Saved %d frames", len(frames))
            except Exception:
                logger.exception("    Error processing video %s", url)

        return results

    def _collect_video_urls(self, driver, query: str, max_videos: int) -> List[str]:
        """Search YouTube and scroll to collect candidate video URLs."""
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(PAGE_LOAD_PAUSE_SECONDS)

        urls = set()
        last_height = 0

        for _ in range(YOUTUBE_MAX_SCROLLS):
            for el in driver.find_elements(By.CSS_SELECTOR, "a#video-title"):
                href = el.get_attribute("href")
                if href and "/watch?v=" in href:
                    urls.add(href.split("&")[0])

            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(SCROLL_PAUSE_SECONDS)

            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return list(urls)[:max_videos]

    def _process_video(self, url: str, frames_per_video: int) -> List[str]:
        """Download a single video and extract uniformly sampled frames from it."""
        import cv2
        import uuid
        from yt_dlp import YoutubeDL

        temp_video_path = os.path.join(self.output_dir, TEMP_VIDEO_FILENAME)
        saved_frames: List[str] = []

        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": temp_video_path,
            "quiet": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        cap = cv2.VideoCapture(temp_video_path)
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if width < self.min_resolution or height < self.min_resolution:
                logger.info("    Skipping: resolution %dx%d too small", width, height)
                return []

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_id = url.split("=")[-1][:8]

            for frame_index in sample_frame_indices(total_frames, frames_per_video):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if ret:
                    frame_path = os.path.join(
                        self.output_dir, f"yt_{video_id}_{uuid.uuid4().hex[:6]}.jpg"
                    )
                    cv2.imwrite(frame_path, frame)
                    saved_frames.append(frame_path)
        finally:
            cap.release()
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

        return saved_frames

