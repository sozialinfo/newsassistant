## 1. Implementation

- [x] 1.1 Lower `MIN_IMAGE_WIDTH` from 1000 to 800 in `image_utils.py`

## 2. Tests

- [x] 2.1 Update test `test_accepts_valid_landscape_jpeg` to use 800px minimum (was 1000px)
- [x] 2.2 Update test `test_rejects_small_image` to use an image below 800px (e.g. 700px wide)
- [x] 2.3 Add test confirming a 900×600 image is now accepted (the real-world case)
