"""
Uniform temporal frame sampling.

Consecutive video frames are near-duplicates rather than genuinely new
training samples. Sampling at uniform intervals across a video's full
duration instead spreads samples across different angles, lighting, and
plating stages, reducing near-duplicate frames reaching the dataset and
the risk of the model overfitting to one visual context per video.
"""

from typing import List


def compute_sample_interval(total_frames: int, frames_per_video: int) -> int:
    """
    Compute the frame-index step size for uniform sampling.

    Args:
        total_frames: Total number of frames in the source video.
        frames_per_video: Desired number of samples from this video.

    Returns:
        The interval (in frames) between samples. Always at least 1.

    Raises:
        ValueError: If frames_per_video is not a positive integer.
    """
    if frames_per_video <= 0:
        raise ValueError("frames_per_video must be a positive integer")
    return max(1, total_frames // frames_per_video)


def sample_frame_indices(total_frames: int, frames_per_video: int) -> List[int]:
    """
    Compute the frame indices to sample, evenly spaced across the video.

    Args:
        total_frames: Total number of frames in the source video.
        frames_per_video: Desired number of samples from this video.

    Returns:
        A list of frame indices of length `frames_per_video`, starting at 0
        and spaced by the uniform sampling interval.
    """
    interval = compute_sample_interval(total_frames, frames_per_video)
    return [interval * i for i in range(frames_per_video)]
