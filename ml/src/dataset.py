"""
Dataset & DataLoader Pipeline
==============================
Implements data augmentation, preprocessing, and standard PyTorch DataLoaders.
Augmentation is strictly isolated to training data to prevent leakage.
"""

from pathlib import Path
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

IMAGE_SIZE = (224, 224)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms():
    """
    Returns train and evaluation transforms.
    Train includes geometric and photometric augmentations.
    Val/Test include only deterministic resize and normalization.
    """
    train_transform = transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    eval_transform = transforms.Compose([
        transforms.Resize(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

    return train_transform, eval_transform


def create_dataloaders(dataset_dir: str = "./ml/dataset", batch_size: int = 16, num_workers: int = 0):
    """
    Builds DataLoaders for train, val, and test splits.
    Classes:
      0: normal
      1: pothole
    """
    base_dir = Path(dataset_dir)
    train_transform, eval_transform = get_transforms()

    train_ds = datasets.ImageFolder(base_dir / "train", transform=train_transform)
    val_ds = datasets.ImageFolder(base_dir / "val", transform=eval_transform)
    test_ds = datasets.ImageFolder(base_dir / "test", transform=eval_transform)

    print(f"DataLoaders created. Class mapping: {train_ds.class_to_idx}")
    print(f"Split sizes - Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, test_loader, train_ds.classes, train_ds.class_to_idx
