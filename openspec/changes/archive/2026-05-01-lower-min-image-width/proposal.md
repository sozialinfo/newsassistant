## Why

The minimum image width threshold of 1000px was rejecting valid content images. For example, a 900×600px article image was skipped in favour of a less relevant 1164×450px image simply because the preferred image was 100px too narrow. The 1000px bar is too aggressive and causes worse image selections.

## What Changes

- Lower `MIN_IMAGE_WIDTH` from 1000 to 800 pixels in `image_utils.py`
- Update any tests that assert on the old threshold

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `image-selection`: Minimum width requirement relaxed from 1000px to 800px — images ≥ 800px wide (and still landscape, ≥ 400px tall) are now accepted as header images.

## Impact

- `addons/newsassistant_website/models/image_utils.py` — constant change
- `addons/newsassistant_website/tests/` — test assertions updated
