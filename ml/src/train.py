"""
Model Training Pipeline
=======================
Trains the ResNet-50 Pothole Classifier with:
- Class-weighted CrossEntropyLoss for class imbalance handling
- AdamW optimizer with cosine/plateau learning rate scheduling
- Validation monitoring, checkpointing, and early stopping
"""

import os
import time
from pathlib import Path
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.metrics import f1_score, accuracy_score

from dataset import create_dataloaders
from model import build_model


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_targets = []

    for images, targets in loader:
        images = images.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.cpu().numpy())

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_targets, all_preds)
    epoch_f1 = f1_score(all_targets, all_preds, average="binary")
    return epoch_loss, epoch_acc, epoch_f1


def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            targets = targets.to(device)

            outputs = model(images)
            loss = criterion(outputs, targets)

            running_loss += loss.item() * images.size(0)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())

    val_loss = running_loss / len(loader.dataset)
    val_acc = accuracy_score(all_targets, all_preds)
    val_f1 = f1_score(all_targets, all_preds, average="binary")
    return val_loss, val_acc, val_f1


def run_training(
    epochs: int = 6,
    batch_size: int = 16,
    lr: float = 1e-4,
    patience: int = 4,
    output_dir: str = "./ml/models/v1"
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"=== Starting Training on device: {device} ===")

    train_loader, val_loader, _, classes, class_to_idx = create_dataloaders(
        dataset_dir="./ml/dataset", batch_size=batch_size
    )

    # Calculate class weights: [normal, pothole]
    # In train set: 244 normal, 427 pothole
    num_normal = 244
    num_pothole = 427
    total = num_normal + num_pothole
    weight_normal = total / (2.0 * num_normal)
    weight_pothole = total / (2.0 * num_pothole)
    class_weights = torch.tensor([weight_normal, weight_pothole], dtype=torch.float).to(device)
    print(f"Class weights (normal: {weight_normal:.3f}, pothole: {weight_pothole:.3f})")

    criterion = nn.CrossEntropyLoss(weight=class_weights)
    model = build_model(num_classes=len(classes), freeze_backbone=False, device=device)

    # Use differential learning rates: lower for backbone, higher for head
    backbone_params = [p for n, p in model.named_parameters() if "backbone.fc" not in n]
    head_params = [p for n, p in model.named_parameters() if "backbone.fc" in n]

    optimizer = AdamW([
        {"params": backbone_params, "lr": lr * 0.2},
        {"params": head_params, "lr": lr}
    ], weight_decay=1e-4)

    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    save_path = Path(output_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    best_checkpoint_file = save_path / "checkpoint.pt"

    best_val_f1 = -1.0
    epochs_no_improve = 0

    history = []

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc, train_f1 = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_f1 = validate(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        scheduler.step(val_f1)

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) | "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} F1: {train_f1:.3f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} F1: {val_f1:.3f}",
            flush=True
        )

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "train_f1": train_f1,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "val_f1": val_f1
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            epochs_no_improve = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_f1": val_f1,
                "val_acc": val_acc,
                "classes": classes,
                "class_to_idx": class_to_idx
            }, best_checkpoint_file)
            print(f"  -> Checkpoint saved with Best Val F1: {best_val_f1:.4f}", flush=True)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping triggered after {patience} epochs without improvement.", flush=True)
                break

    print(f"\n=== Training Complete. Best Val F1: {best_val_f1:.4f} ===")
    return best_checkpoint_file, history


if __name__ == "__main__":
    run_training()
