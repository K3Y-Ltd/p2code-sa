# Dependency: `binvis` (tar → image)

The inference pipeline relies on `binvis` to create a deterministic visual
representation of a container filesystem export (`.tar`). This image becomes
the input to the classifier.

## Where it happens in the code

- Tar → image conversion: `src/inference_pipeline/utils.py::make_image`

The `make_image(tar_path: str) -> str` function:

1. Calls the `binvis.binvis_iter.visualize_binary_iter(...)` function
with a hardcoded argument set of visualization parameters:

```
layout_map="hilbert",
layout_type="unrolled",
color_block=None,
show_progress=True,
color_map=["class", "magnitude", "structure"],
chunk_size=512 * 512,
size=1024,
step=30,
```
2. Saves the resulting image next to the tar file:
   - `/path/to/container.tar` → `/path/to/container.png`
3. Returns the image path.

## Why this is useful

The intent is to reduce a variable-size byte artifact (tar archive) into a
fixed-size RGB image where different color channels can encode different views
of the byte stream. This makes downstream classification possible using common
computer vision backbones.

## Installation note

This package does not vendor `binvis`. In the monorepo, install it with:

```bash
pip install -e packages/binvis
```

If you deploy inference-pipeline independently, ensure `binvis` is available in
the environment (as a wheel or as a dependency).
