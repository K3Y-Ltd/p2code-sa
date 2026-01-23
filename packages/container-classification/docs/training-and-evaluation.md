# Training and evaluation

Training and evaluation in the `container-classification` pipeline are *patch-based*,
i.e.:

- an input image is split into patches
- the model predicts labels for each patch
- evaluation can be reported per patch and aggregated back per image

Where to look in the code:
- `src/bin/train.py`
- `src/bin/evaluate.py`
- `src/container_classification/utils.py`


## Training: `bin.train` or `p2code-container-classifier-train`

### Configuration inputs

The training script expects a TOML file passed via:

```
--cfg_path /path/to/train_config.toml
```

The example configs in `cfgs/` show the supported keys. The ones that directly
control training are:

- `device`: `"cpu" | "cuda" | "xpu"`
- `train.model`: model key (e.g. `"resnet18"`)
- `train.epochs`: number of epochs
- `train.optim`: passed to `torch.optim.Adam(...)` (e.g. `lr`)
- `out.model_dir`: base output directory for checkpoints
- `dataset.*`: how data is loaded and patched (see `docs/data-layout-and-data-loading.md`)


### Available Models

In `src/bin/train.py`, `train.model` is mapped to a class (e.g. `ResNet18`).
These models are wrappers around `torchvision.models` backbones and return a
2-logit output per patch. The available models currently are the following:
- `"alexnet"`: AlexNet
- `"resnet18"`: ResNet18
- `"mobile_net"`: MobileNetV2
- `"squeeze_net"`: SqueezeNet
- `"vgg"`: VGG11
- `"efficient_net"`: EfficientNet
- `"shuffle_net"`: ShuffleNet
- `"resnext101"`: ResNext101


### What a batch contains

Under the hood, training and evaluation are patch-based, with the images 
converted to a stream of image patches. After patching, a typical training
batch consumed by the training loop is iterated as:

```python
for idx, (img_name, patch_id, image, label, weight) in enumerate(data_loader):
    ...
```

Patch labels are yielded as one-hot targets and are compatible with a 2-logit 
output during training/evaluation. The image name represented by `img_name`
variable is used for aggregating patches results per image. 


### Training loop: `train_epoch(...)`

Defined in `src/container_classification/utils.py`:

> Trains model for one epoch and logs training stats.

The key steps as implemented include :

1. `model.train()`
2. Forward pass: `logits = model.forward(image)`  → shape `(B, 2)`
3. Loss: `torch.nn.BCEWithLogitsLoss(weight=weight)(logits, label.squeeze(1))`
4. Probabilities: `probs = torch.sigmoid(logits)`
5. Patch prediction: `preds = torch.argmax(probs, 1)`
6. Patch truth: `trues = torch.argmax(label.squeeze(1), 1)`
7. Scheduler step at the end of the epoch

Logged metrics:
- `train_loss` (running average)
- `train_accuracy` (patch-level)
- confusion matrix via `wandb.plot.confusion_matrix(...)` (if `wandb` is enabled)

In current implementation a `BCEWithLogitsLoss(weight=weight)` is used with a per sample
assigned weight.


### Validation loop: `validate_epoch(...)`

Defined in `src/container_classification/utils.py`:

> Validates the model after each epoch and logs the metrics.

What it reports:

- Patch-level loss/accuracy over the validation/test loader
- Image-level accuracy by aggregating patch predictions per image

The image-level aggregation in current implementation follows the assumptions:

- An image is malevolent if any image patch is malevolent:
  - `y_preds_agg[img] = max(patch_preds)`
  - `y_trues_agg[img] = max(patch_trues)`
- The probability of an image being malevolent is the highest malevolent probability 
among patches:
  - `y_probs_agg[img] = max(patch_prob[1])`

Return value:

```
(y_preds_agg, y_trues_agg, y_probs_agg)
```


### Checkpoint format / Model saving

`model_save(model, optimizer, scheduler, epoch, save_path)` writes a `.pth` file
containing:

```python
{
  "state": model.state_dict(),
  "optimizer": optimizer.state_dict(),
  "scheduler": scheduler.state_dict(),
  "epoch": epoch,
}
```

This is the same format expected by `load_model(...)` used in evaluation and
inference.


### Example: run training

```bash
python -m bin.train --cfg_path cfgs/train_webd_cfg.toml
```

## Evaluation (`python -m bin.evaluate`)

`src/bin/evaluate.py` loads:

- a model checkpoint (via the `model` section in the config)
- one or more dataset splits (depending on `dataset.format`)

and writes a per-image CSV report.

CLI:

```bash
python -m bin.evaluate --cfg_path cfgs/evaluate_webd_cfg.toml
```

The resulting `csv` written per split includes the following columns: 

```
image_name,y_true,y_pred,malevolent_prob
```

Where:

`image_name`: The input image name.
`y_true`: Image-level true labels.
`y_pred`: Image-level predicted labels.
`malevolent_prob`: The probability for the image containing a malware taken 
as the maximum predicted probability across image patches.   
