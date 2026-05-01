## Context

Article header image selection uses a first-match algorithm with URL pattern filtering and dimension/orientation validation. The minimum width constant `MIN_IMAGE_WIDTH` in `image_utils.py` was set to 1000px, which rejected valid content images in the 800–999px range.

## Goals / Non-Goals

**Goals:**
- Accept landscape images ≥ 800px wide (down from 1000px)
- Update tests to assert on the new threshold

**Non-Goals:**
- Changing the selection algorithm (still first-match)
- Modifying height threshold (stays at 400px)
- Retroactively re-scraping existing articles

## Decisions

**Lower `MIN_IMAGE_WIDTH` to 800** — The 1000px threshold was arbitrary. 800px is still large enough to avoid obvious thumbnails while accepting high-quality editorial images (e.g., 900×600px TYPO3-processed images). No alternative thresholds were seriously considered; 800 is a well-established "HD-ready" baseline.

## Risks / Trade-offs

- [Some smaller images admitted] → Mitigated by keeping the 400px height floor and landscape requirement; very small images remain excluded.
- [Retroactive mismatch] → Existing articles keep their current stored image; the change only affects future scrapes.
