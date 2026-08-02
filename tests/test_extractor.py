from unittest.mock import patch

from media_extractor.extractor import MediaExtractor


def test_extract_all_runs_both_platforms_by_default(tmp_path):
    extractor = MediaExtractor(output_dir=str(tmp_path))

    with patch.object(extractor.youtube, "extract", return_value=["a.jpg"]) as yt_mock, \
         patch.object(extractor.google, "extract", return_value=["b.jpg", "c.jpg"]) as g_mock:
        results = extractor.extract_all("thieboudienne")

    yt_mock.assert_called_once()
    g_mock.assert_called_once()
    assert results == {"youtube": ["a.jpg"], "google": ["b.jpg", "c.jpg"]}


def test_extract_all_skips_platforms_not_requested(tmp_path):
    extractor = MediaExtractor(output_dir=str(tmp_path))

    with patch.object(extractor.youtube, "extract") as yt_mock, \
         patch.object(extractor.google, "extract", return_value=[]) as g_mock:
        results = extractor.extract_all("thieboudienne", platforms=["google"])

    yt_mock.assert_not_called()
    g_mock.assert_called_once()
    assert "youtube" not in results
    assert results["google"] == []


def test_extract_all_forwards_platform_specific_kwargs(tmp_path):
    extractor = MediaExtractor(output_dir=str(tmp_path))

    with patch.object(extractor.youtube, "extract", return_value=[]) as yt_mock, \
         patch.object(extractor.google, "extract", return_value=[]) as g_mock:
        extractor.extract_all(
            "thieboudienne",
            max_videos=2,
            frames_per_video=7,
            max_images=42,
        )

    yt_mock.assert_called_once_with("thieboudienne", max_videos=2, frames_per_video=7)
    g_mock.assert_called_once_with("thieboudienne", max_images=42)


def test_extract_all_creates_output_directory(tmp_path):
    output_dir = tmp_path / "nested" / "output"
    MediaExtractor(output_dir=str(output_dir))
    assert output_dir.exists()
