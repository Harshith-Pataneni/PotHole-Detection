"""
Dataset Preparation & Stratified Split Pipeline
================================================
Combines:
1. Pothole images: sachinpatel21/pothole-image-dataset (618 positive images)
2. Normal road images: atulyakumar98/pothole-detection-dataset (352 negative images)

Performs:
- Image integrity validation (filters unreadable/corrupted files)
- MD5-based deduplication
- Stratified Train (70%), Validation (15%), Test (15%) split BEFORE any augmentation
- Output structure ready for PyTorch ImageFolder
"""

import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image
from sklearn.model_selection import train_test_split
import json

DEFAULT_POTHOLE_SRC = Path(os.path.expanduser(r"~/.cache/kagglehub/datasets/sachinpatel21/pothole-image-dataset/versions/2/pothole_image_data/Pothole_Image_Data"))
DEFAULT_NORMAL_SRC = Path(os.path.expanduser(r"~/.cache/kagglehub/datasets/atulyakumar98/pothole-detection-dataset/versions/4/normal"))

OUTPUT_DIR = Path("./ml/dataset")


def compute_md5(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_and_deduplicate(source_dir: Path, label: str):
    valid_files = []
    seen_hashes = set()
    corrupt_count = 0
    duplicate_count = 0

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    print(f"[{label.upper()}] Scanning {source_dir}...", flush=True)
    for idx, file_path in enumerate(source_dir.glob("*.*")):
        if file_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            continue

        # 1. Check integrity
        try:
            with Image.open(file_path) as img:
                img.verify()
            with Image.open(file_path) as img:
                img.convert("RGB")
        except Exception:
            corrupt_count += 1
            continue

        # 2. Check MD5 duplicate
        file_hash = compute_md5(file_path)
        if file_hash in seen_hashes:
            duplicate_count += 1
            continue
        seen_hashes.add(file_hash)

        valid_files.append((file_path, label))
        if idx % 100 == 0 and idx > 0:
            print(f"  Processed {idx} files in {label}...", flush=True)

    print(f"[{label.upper()}] Complete: {len(valid_files)} valid unique images (Removed: {duplicate_count} duplicates, {corrupt_count} corrupt).", flush=True)
    return valid_files


def prepare_dataset(
    pothole_src: Path = DEFAULT_POTHOLE_SRC,
    normal_src: Path = DEFAULT_NORMAL_SRC,
    output_dir: Path = OUTPUT_DIR,
    seed: int = 42
):
    print("=== Step 1: Validating & Profiling Source Datasets ===")
    potholes = validate_and_deduplicate(pothole_src, "pothole")
    normals = validate_and_deduplicate(normal_src, "normal")

    all_data = potholes + normals
    labels = [item[1] for item in all_data]

    print("\n=== Step 2: Stratified Splitting (70% Train, 15% Val, 15% Test) ===")
    # 70% train, 30% temp
    train_data, temp_data, train_labels, temp_labels = train_test_split(
        all_data, labels, test_size=0.30, random_state=seed, stratify=labels
    )
    # Split temp evenly into val (15%) and test (15%)
    val_data, test_data, val_labels, test_labels = train_test_split(
        temp_data, temp_labels, test_size=0.50, random_state=seed, stratify=temp_labels
    )

    splits = {
        "train": train_data,
        "val": val_data,
        "test": test_data
    }

    if output_dir.exists():
        print(f"Cleaning existing output directory: {output_dir}")
        shutil.rmtree(output_dir)

    split_summary = {}

    print("\n=== Step 3: Materializing Split Directory Structure ===")
    for split_name, items in splits.items():
        split_summary[split_name] = {"pothole": 0, "normal": 0, "total": len(items)}
        for src_path, label in items:
            dest_dir = output_dir / split_name / label
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / src_path.name
            shutil.copy2(src_path, dest_path)
            split_summary[split_name][label] += 1

    summary_file = output_dir / "dataset_manifest.json"
    with open(summary_file, "w") as f:
        json.dump(split_summary, f, indent=2)

    print("\n=== Dataset Preparation Complete ===")
    print(json.dumps(split_summary, indent=2))
    print(f"Manifest written to: {summary_file}")
    return split_summary


if __name__ == "__main__":
    prepare_dataset()
