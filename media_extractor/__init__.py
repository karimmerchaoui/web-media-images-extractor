"""
media_extractor: a small dataset-collection pipeline for building training
image sets from YouTube and Google Images, with a resolution quality gate
and uniform temporal frame sampling built in.
"""

import logging

from .extractor import MediaExtractor

logging.basicConfig(level=logging.INFO, format="%(message)s")

__all__ = ["MediaExtractor"]
__version__ = "0.2.0"
