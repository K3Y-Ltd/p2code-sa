# Python API

The `binvis` package offers a python API to programmatically convert binary 
files to images. The functions are offered in two variants, an in-memory and
a streaming variant that can be found in the corresponding modules:

* `binvis.binvis`
* `binvis.binvis_iter`

The streaming variant (with the `iter` suffix) avoids loading large binaries
into memory and parses them in chunks. Each module offers:

* functionality for visualizing binary files,
* functionality for visualizing masks given a list of spans represented as list
of index tuples of type `List[Tuple[int, int]]


### In-memory API

The in-memory API includes the following two functions:
* `binvis.binvis.visualize_binary`
* `binvis.binvis.build_mask_from_spans`

#### `visualize_binary`

The function `visualize_binary` creates a `PIL.Image` from a byte array.

Key arguments:
- `byte_array`: `bytes` or `bytearray` content to visualize.
- `size`: output image width in pixels.
- `color_map`: a string (single map) or list (multiple maps -> channels).
- `layout_map`: pixel layout curve (`hilbert`, `zigzag`).
- `layout_type`: `square`, `unrolled`, or `unrolled_n`.
- `step`: sampling step for the `unrolled` layout.

#### `build_mask_from_spans`

The function `build_mask_from_spans` creates a `PIL.Image` from a list of
byte spans typically used to highlight diffs.

Key arguments:
- `n_bytes`: total size of the target binary.
- `spans`: list of `(start, end)` byte offsets.

The arguments `size`, `layout_map`, `layout_type`, `step` hold the same 
semantics as above.

#### Examples

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


### Streaming API

The streaming API includes the following two functions:
* `binvis.binvis_iter.visualize_binary_iter`
* `binvis.binvis_iter.build_iter_mask_from_spans`

These functions avoids loading large binaries into memory. The API reads
data in chunks and mirrors the non-iterative functions.
 
#### `visualize_binary_iter`

The function `visualize_binary_iter` creates a `PIL.Image` from a file path 
using chunked reads.

Key arguments:
- `path`: path to the binary file.
- `chunk_size`: max bytes read per chunk (default: `512 * 512`).
- `size`, `color_map`, `layout_map`, `layout_type`, `step`: same semantics as above.


#### `build_iter_mask_from_spans`

Creates a mask image from byte spans using the streaming backend.

Key arguments:
- `n_bytes`, `spans`, `chunk_size`, `size`, `layout_map`, `layout_type`, `step`.

Notes:
- `layout_map` values are limited to `hilbert` and `zigzag` in the Numpy backend.
- `color_map` may be a string or a list of colormap names. When a list is used,
  the output image encodes each colormap in a different color channel.
- `color_block` is currently a no-op in the implementation.

#### Examples

```python
from binvis.binvis_iter import visualize_binary_iter

BIN_PATH = "<path-to-binfile-to-visualize>"
OUT_PATH = "<path-to-output-image>"

img = visualize_binary_iter(
    path=BIN_PATH,
    size=256,
    color_map=["class", "magnitude", "structure"],
    layout_map="hilbert",
    layout_type="unrolled",
    chunk_size=512 * 512,
)

img.save(OUT_PATH)
```