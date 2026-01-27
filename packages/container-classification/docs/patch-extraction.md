# Patch extraction

The `container-classification` pipeline follows the ideas of Multiple Instance Learning (MIL).
Image representations of software containers are expected to be large in size, even when
subsampling has been applied. 

The container classification pipeline splits inputs into a set of non-overlapping patches, 
and the model is trained and evaluated on those patches.

Where to look in the code:
- `src/container_classification/dataset/imgproc.py` (slice generation)
- `src/container_classification/dataset/iterable_dataset.py` (patch extraction + WebDataset patching)
- `src/container_classification/dataset/utils.py` (mask-path and name helpers)


## How patch coordinates are generated


### `img_slicers_from_patch_size(img, patch_size)`

From `src/container_classification/dataset/imgproc.py`:

> Create image array `slice` objects from patch size.

Inputs:
- `img`: numpy image array with shape `(H, W, C)`.
- `patch_size`: `(patch_h, patch_w)`.

Output:
- A list of `(slice_h, slice_w)` pairs.

Important behavior on current implementation (easy to miss):

- Slicers are produced using `range(0, H + 1, patch_h)` and `range(0, W + 1, patch_w)`.
- If `H` (or `W`) is not divisible by the patch size, the remainder is ignored.

So the number of patches is:

```
floor(H / patch_h) * floor(W / patch_w)
```

Patch ordering:
- `patch_id` counts left-to-right inside a row, then top-to-bottom across rows
  (row-major order). This matches the slicer list comprehension ordering.


### `img_slicers_from_number_of_splits(img, n_row, n_col)`

Also in `imgproc.py`:

> Create image slicers from number of splits.

Inputs:
- `img`: numpy image array with shape `(H, W, C)`.
- `n_row`: Number of splits across the 'height' dimension. 
- `n_col`: Number of splits across the 'width' dimension.

Output:
- A list of `(slice_h, slice_w)` pairs.

NOTE: This function is currently not used by the main pipelines.


## Patch extraction for WebDataset pipelines

### `split_sample_into_patches(sample, task, patch_size, weights)`

From `src/container_classification/dataset/iterable_dataset.py`:

> Split input image into image patches.

Inputs:
- `sample`: `(img, img_msk, _json)` where `_json` includes `name` and `label`.
- `task`: `"classification"` or `"segmentation"`.
- `patch_size`: `(patch_h, patch_w)`.
- `weights`: two class weights.

Implementation details:
- WebDataset decoding yields RGB arrays; the function converts to BGR using
  `cv2.cvtColor(img, cv2.COLOR_RGB2BGR)`.
- For classification, patch labels are one-hot encoded via `label_to_tensor()`.

Output record structure (classification):

```
(img_name, patch_id, patch_tensor, one_hot_label_tensor, weights_tensor)
```


## Patch extraction for JSON/dir pipelines

The patch extraction functions apply the slicers acquired by the slicer generation
functions and split input images into patches. These functions also handle patch
labeling using information from the accompanying masks.

### `extract_patches_from_image_train(record, patch_size, weights)`

From `src/container_classification/dataset/iterable_dataset.py`:

> Extract patches from an (image-path, label) record.

Inputs:
- `record`: `(img_path, label)` where `label` is `0` (benign) or `1` (malevolent).
- `patch_size`: `(patch_h, patch_w)`.
- `weights`: two class weights, e.g. `[1.0, 256.0]`.

What it does:
- reads the image with `cv2.imread(img_path)` (BGR channel order)
- creates patch slices with `img_slicers_from_patch_size(...)`
- extracts patches into a list
- assigns patch labels:
  - benign image: all patch labels are `0`
  - malevolent image: loads a mask and marks a patch malevolent if `mask_patch.any()`

Mask convention:
- the mask path is derived with `_get_mask_path(img_path)`:
  `image.png` -> `image.mask.png`

Yielded record structure:

```text
img_name:     str   (filename without extension)
patch_id:     int
patch:        torch.FloatTensor with shape (3, patch_h, patch_w)
label:        torch.LongTensor with shape (1,) and value 0/1
weights:      torch.FloatTensor with shape (2,)
```

Note on label shape:
- The yielded `label` is a scalar 0/1 tensor (the code also contains a commented
  out one-hot label; see `# torch.FloatTensor(lbl)`).

### `extract_patches_from_image_path_infer(record, patch_size)`

This is the inference variant for an image path. It yields:

```
(img_name, patch_id, patch_tensor)
```

### `extract_patches_from_image_np_infer(img, patch_size)`

This is the inference variant for an in-memory numpy array. It yields:

```
(patch_id, patch_tensor)
```


## Preprocessing and normalization (current behavior)

There is an `_img_transforms()` helper that defines torchvision normalization,
but current implementation does not use it. So patch tensors contain raw 0-255
BGR pixel values as `float32`.


## Examples

Compute the expected number of patches and show the first few patch shapes:

```python
import cv2
from container_classification.dataset.imgproc import img_slicers_from_patch_size

img = cv2.imread("/data/images/sample.png")
slicers = img_slicers_from_patch_size(img, (256, 256))
print("patches:", len(slicers))
print("first patch shape:", img[slicers[0][0], slicers[0][1], :].shape)
```

Iterate over patches exactly as the inference pipeline does:

```python
from container_classification.dataset.iterable_dataset import extract_patches_from_image_path_infer

for img_name, patch_id, patch in extract_patches_from_image_path_infer(
    "/data/images/sample.png", patch_size=(256, 256)
):
    print(img_name, patch_id, patch.shape)
    if patch_id == 3:
        break
```
