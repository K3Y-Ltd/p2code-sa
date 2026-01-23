import torch

try:
    import wandb
except ImportError:
    print("`wandb` was not found. `wandb` functionalities will be disabled.")


def train_epoch(training_kw, data_loader, model, optimizer, scheduler, epoch, device):
    """
    Trains model for one epoch and logs training stats.

    Parameters
    ----------
    training_kw : Dict
        Model training keyword arguments.
    data_loader : torch.utils.data.DataLoader
        A `pytorch` dataloader.
    model : torch.nn.Module,
        A pytorch model.
    optimizer : torch.optim
        A `pytorch` optimizer.
    scheduler : torch.optim.lr_scheduler
        A `pytorch` learning rate scheduler.
    epoch : int
        Current training epoch.
    device : torch.device
        Device to use, i.e. cuda or cpu.

    Returns
    -------
    None
        Performs model training. Logs training metrics to `wandb` logger.
    """
    # switch into training mode and initialize statistics
    model.train()

    batch_size = training_kw["batch_size"]
    epochs = training_kw["epochs"]

    running_corrects, running_loss = 0, 0.0

    y_preds, y_trues = [], []

    for idx, (img_name, patch_id, image, label, weight) in enumerate(data_loader):

        # zero gradients and mount data on device
        optimizer.zero_grad()
        image = image.to(device.type)
        label = label.to(device.type)
        weight = weight.to(device.type)

        # make predictions, compute loss, compute gradients, update weights
        logits = model.forward(image)

        loss = torch.nn.BCEWithLogitsLoss(weight=weight)(logits, label.squeeze(1))
        loss.backward()
        optimizer.step()

        # extract probabilities and measure metrics
        probs = torch.sigmoid(logits)
        preds = torch.argmax(probs, 1)

        trues = torch.argmax(label.squeeze(1), 1)

        running_corrects += (preds == trues).sum()
        running_acc = running_corrects.item() / ((idx + 1) * batch_size)
        running_loss += loss.item() / (idx + 1)

        # NOTE: Fix this in future versions, memory grows with the length of the lists
        y_preds.extend(preds.tolist())
        y_trues.extend(trues.tolist())

        print(
            "[TRAIN] [EPOCH:{}/{} ] [IDX: {}/{}] Loss: {:.4f} Accuracy: {:.4f}\t".format(
                epoch, epochs, idx + 1, "UNK", loss.item(), running_acc
            )
        )

    # Log i.e. loss function and epoch metrics
    try:
        cm = wandb.plot.confusion_matrix(
            y_true=y_trues, preds=y_preds, class_names=["B", "M"]
        )
    except Exception as e:
        cm = None

    train_metrics = {
        "train_loss": running_loss,
        "train_accuracy": running_acc,
        "confusion": cm,
    }

    try:
        wandb.log(train_metrics, step=epoch)
    except Exception as e:
        print("Logging with `wandb` failed: {}".format(e))

    scheduler.step()


def validate_epoch(valid_kw, data_loader, model, epoch, device, split="valid"):
    """
    Validates the model after each epoch and logs the metrics.

    Parameters
    ----------
    valid_kw : Dict
        Model validation keyword arguments.
    data_loader : torch.utils.data.DataLoader
        A `pytorch` dataloader.
    model : torch.nn.Models
        A `pytorch` model.
    epoch : int
        Current epoch.
    device : torch.device
        Device to validate on i.e. 'cpu' or 'cuda'.
    split : {'valid', 'test'}
        Whether the split is a validation or a testing split. This parameter
        adjusts the messages and wandb-logs accordingly.

    Returns
    -------
    None
        Performs model validation. Logs validation metrics to `wandb` logger.
    """
    # switch into eval mode
    model.eval()

    batch_size = valid_kw["batch_size"]
    epochs = valid_kw["epochs"]

    running_corrects, running_loss = 0, 0.0

    y_probs, y_preds, y_trues = {}, {}, {}

    with torch.no_grad():

        # Iterate over each image separately
        for idx, (img_names, patch_ids, image, label, weight) in enumerate(data_loader):

            # mount data on gpu
            image = image.to(device)
            label = label.to(device)
            weight = weight.to(device)

            # make predictions
            scores = model.forward(image)

            loss = torch.nn.BCEWithLogitsLoss(weight=weight)(scores, label.squeeze(1))

            # extract probabilities and measure metrics
            probs = torch.sigmoid(scores)

            preds = torch.argmax(probs, 1)
            trues = torch.argmax(label.squeeze(1), 1)

            # Accuracy per patch
            running_corrects += (preds == trues).sum()
            running_acc = running_corrects.item() / ((idx + 1) * batch_size)
            running_loss += loss.item() / (idx + 1)

            # Accuracy per image
            for img_name, patch_id, pred in zip(img_names, patch_ids, preds.tolist()):

                if img_name not in y_preds:
                    y_preds[img_name] = {patch_id.item(): pred}
                else:
                    y_preds[img_name].update({patch_id.item(): pred})

            for img_name, patch_id, prob in zip(img_names, patch_ids, probs.tolist()):

                if img_name not in y_probs:
                    y_probs[img_name] = {patch_id.item(): prob}
                else:
                    y_probs[img_name].update({patch_id.item(): prob})

            for img_name, patch_id, true in zip(img_names, patch_ids, trues.tolist()):
                if img_name not in y_trues:
                    y_trues[img_name] = {patch_id.item(): true}
                else:
                    y_trues[img_name].update({patch_id.item(): true})

            print(
                "[{}][PATCHES] [EPOCH:{}/{}] Loss: {:.4f} Accuracy: {:.4f}\t".format(
                    split.upper(), epoch, epochs, loss.item(), running_acc
                )
            )

    # Accuracy per image
    y_preds_agg = {img_name: max(preds.values()) for img_name, preds in y_preds.items()}
    y_trues_agg = {img_name: max(trues.values()) for img_name, trues in y_trues.items()}
    y_probs_agg = {
        img_name: max([prob[1] for prob in probs.values()])
        for img_name, probs in y_probs.items()
    }

    overall_acc = sum([y_preds_agg[k] == y_trues_agg[k] for k in y_preds_agg.keys()])
    overall_acc = overall_acc / len(y_preds_agg)

    print(
        "[{}][IMAGES] [EPOCH:{}/{}] Accuracy: {:.4f}\t".format(
            split.upper(), epoch, epochs, overall_acc
        )
    )

    # Log i.e. loss function and epoch metrics
    y_trues_lst = list(y_trues_agg.values())
    y_preds_lst = list(y_preds_agg.values())
    try:
        cm = wandb.plot.confusion_matrix(
            y_true=y_preds_lst, preds=y_trues_lst, class_names=["B", "M"]
        )
    except Exception as e:
        cm = None

    _metrics = {
        "_loss": running_loss,
        "_accuracy_patches": running_acc,
        "_accuracy_overall": overall_acc,
        "_cm": cm,
    }

    _metrics = {split + k: v for k, v in _metrics.items()}

    try:
        wandb.log(_metrics, step=epoch)
    except Exception as e:
        print("Logging with `wandb` failed: {}".format(e))

    return y_preds_agg, y_trues_agg, y_probs_agg


def model_save(model, optimizer, scheduler, epoch, save_path):
    """
    Saves model, optimizer and scheduler history at some specific epoch.

    Parameters
    ----------
    model : torch.nn.Module.
        An instantiation of a pytorch model.
    optimizer : torch.optim
        A `pytorch` optimizer.
    scheduler : torch.optim.lr_scheduler
        A `pytorch` learning rate scheduler.
    epoch : int
        Current epoch in training loop.
    save_path : str
        Save path to store model.

    Returns
    -------
    None
        Saves model state along with optimizer, scheduler history etc.
    """
    save_dict = {
        "state": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "epoch": epoch,
    }

    torch.save(save_dict, save_path)


def validate_device(device):
    """
    Validate device argument.
    """
    if device == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    elif device == "xpu" and hasattr(torch, "xpu"):
        return torch.device("xpu" if torch.xpu.is_available() else "cpu")

    else:
        return torch.device("cpu")
