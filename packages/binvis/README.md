# `binvis`: Binary Files Visualization Toolkit

This package holds code for turning raw bytes into images using space-filling curves
and fast NumPy pipelines.

The `binvis` package provides tools for visualizing binary files as images using
space-filling curves. It includes a Python API along with CLI entry points for 
generating images from standalone binaries and specialized functions for visualizing
`.tar` files. The binary visualization is based on space-filling curves and fast
NumPy pipelines.

### Installation

Navigate to the package directory and build a package `.whl` file that can be installed
via pip:

```bash
python setup.py bdist_wheel
pip install <my-package>.whl
```

Alternatively, install in editable mode:

```bash
pip install -e .
```

Installing the package adds the following command-line entry points for 
visualizing binary files with explicit entry points for visualizing `tar`
files:
* `p2code-binvis-visualize-tar`
* `p2code-binvis-visualize-bin`
* `p2code-binvis-visualize-iter-tar`
* `p2code-binvis-visualize-iter-bin`

### Quick Start

#### Visualize a binary file via the Python API

```python
from binvis.binvis import visualize_binary

BIN_PATH = "<path-to-binfile-to-visualize>"
OUT_PATH = "<path-to-output-image>"

with open(BIN_PATH, "rb") as f:
    byte_array = f.read()

img = visualize_binary(
    byte_array=byte_array,
    size=256,
    color_map="class",
    layout_map="hilbert",
    layout_type="unrolled_n",
    color_block=None,
    show_progress=True,
)

img.save(OUT_PATH)
```

#### Visualize a binary file via the CLI

```bash
p2code-binvis-visualize-bin \
  --in_path /path/to/file.bin \
  --out_path /path/to/file.png \
  --color_map class \
  --layout_map hilbert \
  --layout_type unrolled_n \
  --size 256
```

### References

This implementation is inspired by Aldo Cortesi's original binary visualization
package based in python found here: ([scurve-python](https://github.com/cortesi/scurve-python)).
