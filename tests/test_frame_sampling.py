import pytest

from media_extractor.frame_sampling import compute_sample_interval, sample_frame_indices


def test_compute_sample_interval_basic():
    assert compute_sample_interval(total_frames=300, frames_per_video=3) == 100


def test_compute_sample_interval_never_below_one():
    # Fewer total frames than requested samples must not produce interval 0.
    assert compute_sample_interval(total_frames=2, frames_per_video=5) == 1


def test_compute_sample_interval_rejects_non_positive_frames_per_video():
    with pytest.raises(ValueError):
        compute_sample_interval(total_frames=300, frames_per_video=0)


def test_sample_frame_indices_spread_evenly_across_duration():
    indices = sample_frame_indices(total_frames=300, frames_per_video=3)
    assert indices == [0, 100, 200]


def test_sample_frame_indices_starts_at_zero():
    indices = sample_frame_indices(total_frames=90, frames_per_video=4)
    assert indices[0] == 0


def test_sample_frame_indices_returns_requested_count():
    indices = sample_frame_indices(total_frames=1000, frames_per_video=5)
    assert len(indices) == 5


def test_sample_frame_indices_never_exceed_total_frames():
    # Regression guard: sampled indices must stay within the video's actual
    # frame range even for short videos with few frames.
    indices = sample_frame_indices(total_frames=10, frames_per_video=3)
    assert all(0 <= i < 10 for i in indices)
