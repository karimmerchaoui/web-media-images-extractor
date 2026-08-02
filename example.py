"""Example usage of the media_extractor package."""

from media_extractor import MediaExtractor

if __name__ == "__main__":
    extractor = MediaExtractor(output_dir="my_media")

    results = extractor.extract_all(
        query="Thieboudienne",
        platforms=["google", "youtube"],
        max_videos=5,
        frames_per_video=3,
        max_images=20,
    )
