# Inference

Inference answers the question: “given a software container RGB image, is the 
container benign or malware compromised?”. Internally, the pipeline still works
on patches; the final output is an aggregated per-image verdict.

Where to look in the code:
- `src/bin/infer.py` (CLI wrapper)
- `src/container_classification/infer.py` (inference utilities and aggregation)
- `src/container_classification/dataset/iterable_dataset.py` (patch extraction for inference)


## CLI usage: / `python -m bin.infer`

Arguments (see `src/bin/infer.py`):

```
--model_path   Path to a .pth checkpoint (required)
--model_type   Model key (default: alexnet)
--image_path   Path to a PNG image (default: ./data/)
--device       cpu | cuda | xpu (default: cpu)
```

Example:

```bash
p2code-container-classifier-infer \
  --model_path /path/to/model.pth \
  --model_type resnet18 \
  --image_path /path/to/image.png \
  --device cpu
```

Alternatively use the inference script `src/bin/infer.py`.

Implementation note:
- The CLI currently uses a fixed patch size of `[256, 256]`.


## What comes out

`src/container_classification/infer.py::infer(...)` returns a dict:

```json
{"class": "benign|malevolent", "probability": 0.0}
```

The class label is one of:
- `"benign"`
- `"malevolent"`

The probability is the aggregated score returned by the inference code
(details below).


## The inference pipeline

### 1. Create a patch loader: `initialize_data_loader_infer(paths, patch_size)`

From `src/container_classification/infer.py`:

> Initialize DataLoader for an inference iterable dataset.

Inputs:
- `paths`: a single image path or a list of image paths.
- `patch_size`: list `[patch_h, patch_w]`.

Output:
- a `torch.utils.data.DataLoader` that yields `(img_name, patch_id, patch_tensor)`
  batches.

Hard-coded loader settings:
- `batch_size=64`
- `num_workers=1`
- `shuffle=False`


### 2. Load a model checkpoint: `load_model(model_path, model_type, device="cpu")`

From `src/container_classification/infer.py`:

> Load model from `pt` file.

Inputs:
- `model_path`: checkpoint path.
- `model_type`: one of `alexnet`, `resnet18`, `mobile_net`, `squeeze_net`,
  `vgg`, `efficient_net`, `shuffle_net`.
- `device`: passed to `torch.load(..., map_location=device)` and used for `model.to(device)`.

Checkpoint assumption:
- the file is a dict with a `state` key that holds the model state dict; this matches
  `model_save(...)` used during training.


### 3. Patch prediction and aggregation: `infer(model, data_loader, device="cpu")`

From `src/container_classification/infer.py`:

> Classify single image record of dockerized container.

Per batch:
- forward pass to get logits
- apply `sigmoid` to get per-class probabilities
- derive per-patch predictions by thresholding the *malevolent* probability
using the helper function `get_predictions_from_threshold_probabilities`

Image-level aggregation (as implemented):

- `img_pred = max(patch_preds)`
- If `img_pred == 1` (malevolent):
  - `img_prob = max(probabilities_of_patches_predicted_malevolent)`
- If `img_pred == 0` (benign):
  - `img_prob = mean(probabilities_of_patches_predicted_benign)`


**NOTE**: Current implementation that supports specific use case of P2CODE Software 
Attestation, performs single-image inference. So if multiple paths are passed, they
are ignored. This happens inside `_parse_result_for_incode_sa(...)`.


## Minimal programmatic example

```python
from container_classification.infer import (
    load_model,
    infer,
    initialize_data_loader_infer,
)
from container_classification.utils import validate_device

device = validate_device("cpu")

model = load_model("/path/to/model.pth", "resnet18", device=device.type)

loader = initialize_data_loader_infer("/path/to/image.png", [256, 256])

result = infer(model=model, data_loader=loader, device=device.type)

print(result)
```


## Tips for practical use

- The malevolent detector threshold can be varied in case you want a less or more strict detector.
  Currently the threshold is hard-coded used inside `infer` function.
- Ensure your image dimensions are compatible with the patch size; patching
  ignores remainder pixels if the size is not divisible (see `docs/patch-extraction.md`).
