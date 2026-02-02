# Dependency: `container-classification` (image → verdict)

After a container tarball is converted into an RGB image, the service
uses the `container-classification` package to run patch-based inference
and return the prediction results.


## Where it happens in the code

- Model loading: `src/inference_pipeline/api/app.py::app_load_models`
- Inference: `src/inference_pipeline/utils.py::run_inference`
- Underlying helpers imported from `container_classification.infer`:
  - `load_model`
  - `initialize_data_loader_infer`
  - `infer`


## Checkpoint expectations

The service expects PyTorch checkpoints saved in the format produced by the
training code in `container-classification`:

```python
{
  "state": model.state_dict(),
  "optimizer": ...,
  "scheduler": ...,
  "epoch": ...
}
```

Only the `state` key is used by the service. The config specifies a directory
and a list of checkpoint filenames:

```yaml
models:
  path: "/usr/src/p2code"
  files:
    - "alexnet_container_classifier_1.pth"
    - "alexnet_container_classifier_2.pth"
    - "alexnet_container_classifier_3.pth"
    - "alexnet_container_classifier_4.pth"
```

The models are assigned to application areas based on their given order and mapped 
to keys `1..N`. Then the request query param `aa=<int>` selects `models[aa]`.


## Inference behavior (high level)

`run_inference(image_path, model)`:

1. Uses `initialize_data_loader_infer(image_path, patch_size=[256, 256])`.
2. Calls `infer(model=model, data_loader=..., device="cpu")`.
3. Returns a dict like:
   `{"class": "benign|malevolent", "probability": 0.0}`

Practical note:
- Even if the API server runs on a machine with a GPU, the current helper call
  uses `device="cpu"` for inference.


## Installation note

In the monorepo, install with:

```bash
pip install -e packages/container-classification
```

For deeper details on patching and aggregation, see:
- `packages/container-classification/docs/inference.md`
- `packages/container-classification/docs/patch-extraction.md`
