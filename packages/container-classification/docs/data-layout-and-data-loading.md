# Data layout and data loading

This package defines machine learning training pipelines that operate with RGB images 
extracted from tarball files of exported dockerized software containers. The input data
can be loaded based on the following formats: 

- `webdataset` : WebDataset shards - **preferred**
- `json` : JSON split files, i.e. explicit lists of the images along with their labels.
- `dir` : Directory paths indicating the different data splits.

Where to look in the code:
- `src/container_classification/dataset/iterable_dataset.py` (iterable datasets + WebDataset pipelines)
- `src/container_classification/dataset/utils.py` (path/label helpers)
- `src/bin/train.py` (training procedure)


## WebDataset format: `dataset.format = "webdataset"` / `"webdataset-multi"`

The WebDataset format is the preferred way of executing the `container-classification`
pipeline and is the format followed by the COSOCO dataset. For the WebDataset format
each sample includes the following information:

- `png`: the container image
- `mask.png`: a mask image used to derive patch labels (for malevolent)
- `json`: metadata that must include:
  - `name` (used as `img_name`)
  - `label` (string; `"benign"` is treated as class 0)

Loading data via the `webdataset` format is built in `build_wds_pipeline_data_from_shards()`:

1. List shard files in `shards_path`.
2. Select shards whose filename contains the split string (e.g. `"train"`).
3. Decode samples as RGB arrays.
4. Read each sample as a triple: `("png", "mask.png", "json")`.
5. Turn a single image into multiple patch records via `split_sample_into_patches()`.
6. Flatten the patch list into a stream of patch samples.


## JSON format: `dataset.format = "json"`

The so-called JSON format involves a root directory with RGB images
representing software containers and a JSON file with `name` and `label`
metadata:

```json
{"name": "benign-XXXX-IMG001", "label": "benign"}
```

In configs, JSON is used to point each split to a separate file:

```toml
[dataset]
format = "json"
path = "/data/images"

[dataset.json]
train = "/data/splits/train.json"
valid = "/data/splits/valid.json"
test  = "/data/splits/test.json"
```

Paths and labels are built dynamically as follows:

- Image path: `os.path.join(dataset.path, record["name"] + ".png")`
- Label encoding: `benign -> 0`, anything else -> `1`

Image masks are discovered using the image's name by the convention:
- image path: `/path/to/image.png` -> mask path: `/path/to/image.mask.png`


## Directory format: `dataset.format = "dir"`

Using the `dir` requires pointing to a root directory with RGB images
representing software containers. The labels are inferred via the image
name which must include label information such as `benign`. Different
directory paths indicate different data splits.

A typical layout is:

```
data_dir/
  train/
    benign-XXXX-CNTA0001.png
    ...
    malevolent-XXXX-CNTA0002.png
  valid/
    benign-XXXX-CNTA0100.png
    ...
    malevolent-XXXX-CNTA0101.png
  test/
    ...
```

Image masks are discovered using the image's name by the convention:
- image path: `/path/to/image.png` -> mask path: `/path/to/image.mask.png`


## Data-related Fields in Configuration Files

In scripts, dataset definition follow the same structure:

```toml
[dataset]
format = "webdataset"              # json | dir | webdataset | webdataset-multi
path = "/path/to/images-or-shards"

[dataset.kw]
task = "classification"            # classification | segmentation (WebDataset only)
patch_size = [256, 256]
weights = [1.0, 256.0]
```

Depending on `dataset.format`, one must also provide the corresponding section
in the configuration file (see example configs in `cfgs/`):

- WebDataset splits: `[dataset.splits]` or `splits = [...]` 
- JSON splits: `[dataset.json] train/valid/test = "...json"`
- directory splits: `[dataset.dir] train/valid/test = "..."`


## What a “sample” looks like in training/evaluation

Under the hood, training and evaluation are patch-based, with the images 
converted to a stream of image patches. After patching, a typical training
record consumed by the training loop is:

```
(img_name, patch_id, patch_tensor, label_tensor, weight_tensor)
```

This can be found in the functions `train_epoch()` and `validate_epoch()` 
in the `src/container_classification/utils.py` module.


## Dataset classes

All loading methods under the hood result in similar representations used by
the training and evaluation pipelines:

- `webdataset`: For the WebDataset format, the mechanics provided by the 
  `webdataset` package are used. The function `build_wds_pipeline_data_from_shards`
  builds a `webdataset.DataPipeline` that acts similar to an IterableDataset. 
  The instance is then loaded by a `webdataset.WebLoader` which acts similar to
  a `torch` `DataLoader`.

  The `webdataset.WebLoader` can be directly configured as follows:

  ```toml
  [dataset.webloader.train]
  batch_size = 256
  shuffle = false
  num_workers = 3
  drop_last = false
  ```

- `json`, `dir`: For the JSON and the Directory format, the paths and labels are
  used along with an image splitter to create a `torch` `IterableDataset`, then 
  converted as an `IterDataPipe` and passed to a `torch` `DataLoader`. The `DataLoader`
  can be directly configured as follows:

  ```toml
  [dataset.dataloader.train]
  batch_size = 256
  shuffle = true
  num_workers = 2
  drop_last = false
  ```


## Practical Gotchas (from current code)

- Patch extraction assumes image sizes divisible by `patch_size`; otherwise the
  remainder is ignored (details in `docs/patch-extraction.md`).

- Patch labels are currently yielded as one-hot targets and are compatible with
  a 2-logit output during training/evaluation.
