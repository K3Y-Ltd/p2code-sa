# CLI

The `binvis` package offers the following command-line entry points for 
visualizing binary files:
* `p2code-binvis-visualize-tar`
* `p2code-binvis-visualize-bin`
* `p2code-binvis-visualize-iter-tar`
* `p2code-binvis-visualize-iter-bin`

The methods are split between the regular and the `iter` variants. The 
`iter` variants are based on a `numpy` implementation and faster and safer
with respect to memory costs.   

### Visualize a single binary file

```bash
p2code-binvis-visualize-bin \
  --in_path /path/to/file.bin \
  --out_path /path/to/file.png \
  --color_map class \
  --layout_map hilbert \
  --layout_type unrolled \
  --size 256
```

### Visualize `.tar` files

```bash
p2code-binvis-visualize-tar \
  --tar_folder /path/to/tarfiles \
  --out_folder /path/to/images \
  --color_map class magnitude structure \
  --layout_map hilbert_n \
  --layout_type unrolled \
  --size 1024 \
  --cores 4
```

On can also use `--tar_meta_path` instead of `--tar_folder` to load the tar
list and per-file diffs from a JSON file with appropriate metadata. When 
`--tar_meta_path` is provided, the tool will also generate mask images for 
any diff spans available. 

The argument `--tar_meta_path` expects a JSON file with the following schema:
```json
[
  {
    "name": "malevolent-aa1-INCODE001-1.tar",
    "path": "/src/aa1/malevolent-aa1-INCODE001-1.tar",
    "label": "malevolent",
    "image__size": 1083059177,
    "diffs": {
        "Adds": [
            {
                "Name": "/var/spool/cron/crontabs/root",
                "Size": 265
            }
        ],
        "Dels": null,
        "Mods": null
    },
    "packages": [],
    "malwares": [
        {
            "sha256_hash": "94b8e3e6571d018e6b2f2027539be086226da9452309d4178f93b1000e7054b6",
            "file_type_guess": "elf",
            "signature": "CoinMiner",
            "tags": "CoinMiner|elf|Miner"
        }
    ]
  },
...
]
``` 


If `--upload-to-cloud` is set, uploads use `incode_cloud.google_storage`. If the
dependency is missing, uploads are skipped.

# Colormaps

The `color_map` argument controls how bytes are colored in the output image.
Available colormaps in the main (non-iterative) path are:
- `class`: 4 classes based on byte value (0x00, 0xFF, printable ASCII, other).
- `magnitude`: grayscale mapped directly from byte value.
- `entropy`: entropy-based color from a sliding window around each byte.
- `hilbert`: Hilbert-curve-based color mapping (experimental).
- `structure`: `.tar` structure-based mapping (useful only for `.tar` data).

# Layout Types

The `layout_type` argument controls output image height and aspect ratio:
- `square` builds an image of dimensions `(size, size)`.
- `unrolled` builds an image of dimensions `(size, size * 4)`.
- `unrolled_n` builds an image of dimensions `(size, size * n)` where `n`
  depends on the number of squares required to fit all data.

