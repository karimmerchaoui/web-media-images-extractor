"""Shared configuration constants for the media extraction pipeline."""

DEFAULT_OUTPUT_DIR = "media_frames"
DEFAULT_MIN_RESOLUTION = 400  # px, minimum width/height to keep an image
JPEG_QUALITY = 85

YOUTUBE_MAX_SCROLLS = 20
GOOGLE_MAX_SCROLLS = 5
SCROLL_PAUSE_SECONDS = 1.5
PAGE_LOAD_PAUSE_SECONDS = 2

TEMP_VIDEO_FILENAME = "temp_video.mp4"
GOOGLE_HIGH_RES_SELECTOR = "img.n3VNCb"
GOOGLE_RESULTS_XPATH = '//*[@id="rso"]/div/div/div/div/div[1]/div'
