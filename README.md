# NutriVision Dataset Pipeline

## A Data Curation Pipeline for Training Food Recognition Models on Underrepresented Cuisines

---

## Overview

No dataset existed for North African dishes — not in Food-101, Recipe1M, or anywhere else. Without one, training a YOLOv11 detector for NutriVision wasn't possible.

**This pipeline solves the problem**: it automates image and video-frame collection from the web, then filters and samples that raw data down to a clean, diverse training set — turning a process that would otherwise take weeks of manual collection into one that runs in minutes and yields a meaningfully higher-quality result.

The trained model and the NutriVision app itself live in a separate repo; this one covers data collection and curation only.

---

## Who Would Benefit from This Tool

- **Computer vision / ML engineers** who need to bootstrap an image dataset for a class of objects with little existing coverage (niche cuisines, regional products, underrepresented categories in general).
- **Researchers building food-recognition or nutrition-tracking models** for cuisines outside the usual Western-food-dataset defaults.
- **Anyone assembling a training set from web video**, who wants a starting point for frame sampling that doesn't just dump near-duplicate frames into the dataset.
- **Students/practitioners learning dataset curation**, since the resolution and sampling controls here are a small, readable example of the kind of quality gating real datasets need.

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-source scraping** | Pulls candidate images from Google Images and candidate frames from YouTube videos for a given search query. |
| **Resolution gate** | Every image/frame is checked against a minimum resolution (400×400px) before being saved; anything smaller is discarded, not upscaled. |
| **Uniform temporal frame sampling** | YouTube frames are sampled at evenly spaced intervals across a video's full duration, not from a fixed offset — reducing near-duplicate frames and overfitting risk. |
| **Automatic scrolling** | Both extractors scroll their target page to load more results before extracting, rather than relying on the initial page load. |
| **Unique, collision-free filenames** | Every saved file gets a UUID suffix, so repeated runs never overwrite prior results. |
| **Simple aggregation API** | `extract_all()` runs every configured platform and reports per-platform and total image counts in one call. |

---

## Technologies Used

| Component | Tool | Purpose |
|---|---|---|
| Browser automation | Selenium / SeleniumBase | Drive search and scroll behavior on YouTube and Google Images |
| Video download | yt-dlp | Pull full-resolution source video prior to frame extraction |
| Frame extraction | OpenCV | Uniform temporal sampling from downloaded video |
| Image validation | Pillow | Resolution gate, format normalization to JPEG |
| HTTP | Requests | Direct image downloads from URLs |

---

## Project Background

I built this because NutriVision hit a wall no existing dataset could solve: Food-101, Recipe1M, and every common food-recognition dataset skip North African cuisine entirely. With no dataset to start from, I had to build the data collection process myself.

---

## Technical Details

### Resolution Gate

```python
def _save_image(self, image_data, prefix="image", min_resolution=400):
    ...
    if img.width < min_resolution or img.height < min_resolution:
        return None  # discarded, not upscaled
```

### Uniform Frame Sampling

```python
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
interval = max(1, total_frames // frames_per_video)

for f in range(frames_per_video):
    cap.set(cv2.CAP_PROP_POS_FRAMES, interval * f)
    ...
```

### Pipeline Flow

```
                    ┌─────────────────┐
                    │  Search Query    │
                    │ "Thieboudienne"  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
      ┌───────────────┐             ┌───────────────┐
      │ Google Images │             │   YouTube      │
      │   Extractor   │             │   Extractor    │
      └───────┬───────┘             └───────┬───────┘
              │                             │
              ▼                             ▼
      ┌───────────────┐             ┌───────────────┐
      │ Download full-│             │ Download video │
      │ res candidates │             │ (yt-dlp)       │
      └───────┬───────┘             └───────┬───────┘
              │                             │
              │                             ▼
              │                     ┌───────────────┐
              │                     │ Uniform frame  │
              │                     │ sampling across │
              │                     │ full duration   │
              │                     └───────┬───────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
                  ┌───────────────────────┐
                  │ Resolution gate        │
                  │ (≥400×400, else drop)  │
                  └──────────┬────────────┘
                             ▼
                  ┌───────────────────────┐
                  │ Saved to output dir    │
                  │ with unique filenames  │
                  └───────────────────────┘
```

### Roadmap: Further Data Science Extensions

The current pipeline handles acquisition and basic quality gating. The next layer of work is squarely dataset-science territory:

- **Near-duplicate detection across sources**, not just within a single video — e.g. perceptual hashing to catch the same photo re-uploaded across multiple Google Images results.
- **Per-class dataset statistics** — image count, resolution distribution, and aspect-ratio spread per dish, to catch class imbalance before it reaches training.
- **Stratified train/val/test split** by dish class, so evaluation numbers reflect true per-class performance.
- **Basic EDA notebook** — sample grids per class, resolution histograms, a quick pass to eyeball mislabeled images before annotation.

---

## Installation

```bash
git clone https://github.com/yourusername/nutrivision-dataset-pipeline.git
cd nutrivision-dataset-pipeline

pip install selenium seleniumbase yt-dlp opencv-python pillow requests
```

Chrome must be installed locally, since Selenium drives a real browser session.

---

## Output Examples

### Usage

```python
from YoutubeFrameExtractor import MediaExtractor

extractor = MediaExtractor(output_dir="thieboudienne_raw")

results = extractor.extract_all(
    query="Thieboudienne",
    platforms=["google", "youtube"],
    max_videos=5,
    frames_per_video=3,   # sampled uniformly across each video, not consecutively
    max_images=20,        # only images passing the 400px resolution gate are kept
)
```

### Example Run

```
[Google Images] Searching: Thieboudienne
  Found 25 images
  [1/20] ✓ Saved image
  [2/20] ✓ Saved image
  [3/20] ✗ Resolution too small

[YouTube] Searching: Thieboudienne
  Found 15 videos
  [1/5] Processing video...
    ✓ Saved 3 frames
  [2/5] Processing video...
    ✓ Saved 3 frames
  [3/5] Processing video...
    Skipping: Resolution 320x240 too small

============================================================
EXTRACTION COMPLETE!
============================================================
Google      : 18 images
Youtube     : 12 images
------------------------------------------------------------
TOTAL IMAGES: 30
Saved in: thieboudienne_raw/
============================================================
```

### Folder Structure

```
thieboudienne_raw/
├── google_1_7c3d9e.jpg
├── google_2_a91f4c.jpg
├── yt_abc123_4f8a2b.jpg
├── yt_abc123_9d0e1a.jpg
└── yt_def456_2b5a7f.jpg
```

---

## License

MIT License.
