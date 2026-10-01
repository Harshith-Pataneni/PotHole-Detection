"""
Final Evaluation & Model Artifact Export
=========================================
Runs strictly on the hold-out TEST split (which was never seen during training or model selection).
Computes:
- Confusion Matrix, Accuracy, Precision, Recall, F1-Score, ROC-AUC
- Plots and saves confusion matrix and ROC curves
- Extracts sample Grad-CAM inference visualizations
- Exports clean production artifact: model.pt and metadata.json
"""

import os
import json
import time
from datetime import datetime, timezone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, roc_curve
)
from PIL import Image

from dataset import create_dataloaders, get_transforms
from model import build_model
from explain import GradCAM, overlay_heatmap, estimate_visual_severity


def run_evaluation(
    checkpoint_path: str = "./ml/models/v1/checkpoint.pt",
    output_dir: str = "./ml/models/v1"
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"=== Running Final Hold-Out Evaluation on device: {device} ===")

    _, _, test_loader, classes, class_to_idx = create_dataloaders(
        dataset_dir="./ml/dataset", batch_size=16
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load Model Checkpoint
    print(f"Loading checkpoint from {checkpoint_path}...", flush=True)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = build_model(num_classes=len(classes), pretrained=False, device=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    print("Model loaded successfully. Evaluating on hold-out test set...", flush=True)

    # 2. Inference on Test Set
    all_targets = []
    all_preds = []
    all_probs = []

    with torch.no_grad():
        for images, targets in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = F.softmax(outputs, dim=1)

            pothole_probs = probs[:, 1].cpu().numpy()
            preds = torch.argmax(outputs, dim=1).cpu().numpy()

            all_targets.extend(targets.numpy())
            all_preds.extend(preds)
            all_probs.extend(pothole_probs)

    all_targets = np.array(all_targets)
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)

    # 3. Compute Metrics
    acc = float(accuracy_score(all_targets, all_preds))
    prec = float(precision_score(all_targets, all_preds, zero_division=0))
    rec = float(recall_score(all_targets, all_preds, zero_division=0))
    f1 = float(f1_score(all_targets, all_preds, zero_division=0))
    try:
        auc = float(roc_auc_score(all_targets, all_probs))
    except Exception:
        auc = 0.0

    cm = confusion_matrix(all_targets, all_preds)
    tn, fp, fn, tp = cm.ravel()

    print("\n--- TEST SET METRICS ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print(f"ROC-AUC:   {auc:.4f}")
    print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")

    # 4. Save Confusion Matrix Plot
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=classes, yticklabels=classes)
    plt.title("Hold-Out Test Set Confusion Matrix")
    plt.xlabel("Predicted Class")
    plt.ylabel("True Class")
    plt.tight_layout()
    cm_path = out_path / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close()

    # 5. Save ROC Curve
    fpr, tpr, _ = roc_curve(all_targets, all_probs)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=1.5, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic (ROC)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    roc_path = out_path / "roc_curve.png"
    plt.savefig(roc_path, dpi=200)
    plt.close()

    # 6. Generate Sample Visual Predictions with Grad-CAM
    sample_dir = out_path / "sample_predictions"
    sample_dir.mkdir(parents=True, exist_ok=True)
    grad_cam = GradCAM(model, model.get_last_conv_layer())
    _, eval_transform = get_transforms()

    test_images_pothole = list(Path("./ml/dataset/test/pothole").glob("*.*"))[:4]
    test_images_normal = list(Path("./ml/dataset/test/normal").glob("*.*"))[:4]
    sample_candidates = test_images_pothole + test_images_normal

    sample_meta = []
    for img_path in sample_candidates:
        orig_img = Image.open(img_path).convert("RGB")
        tensor_img = eval_transform(orig_img).unsqueeze(0).to(device)

        # Forward
        with torch.no_grad():
            logits = model(tensor_img)
            probs = F.softmax(logits, dim=1)
            pothole_conf = float(probs[0, 1].item())
            is_pothole = pothole_conf >= 0.50

        # Grad-CAM heatmap
        heatmap = grad_cam.generate_heatmap(tensor_img, class_idx=1)
        severity_info = estimate_visual_severity(pothole_conf, heatmap, is_pothole)
        blended_img = overlay_heatmap(orig_img, heatmap)

        save_name = f"sample_{img_path.stem}.jpg"
        blended_img.save(sample_dir / save_name)

        sample_meta.append({
            "original_file": img_path.name,
            "true_class": img_path.parent.name,
            "predicted_pothole_prob": round(pothole_conf, 3),
            "is_pothole": is_pothole,
            "estimated_severity": severity_info["estimated_severity"],
            "saved_overlay": save_name
        })

    # 7. Export Production Artifacts
    # Save clean model weights (state dict)
    prod_weights_file = out_path / "model.pt"
    torch.save(model.state_dict(), prod_weights_file)
    print(f"Clean production model weights exported to: {prod_weights_file}")

    metadata = {
        "model_version": "v1",
        "model_type": "ResNet-50 Transfer Learning Classifier",
        "framework": "PyTorch / Torchvision",
        "classes": classes,
        "class_to_idx": class_to_idx,
        "input_size": [224, 224, 3],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "training_date": datetime.now(timezone.utc).isoformat(),
        "recommended_pothole_threshold": 0.75,
        "evaluation_metrics": {
            "test_accuracy": round(acc, 4),
            "test_precision": round(prec, 4),
            "test_recall": round(rec, 4),
            "test_f1": round(f1, 4),
            "test_roc_auc": round(auc, 4),
            "confusion_matrix": {
                "true_positive": int(tp),
                "false_positive": int(fp),
                "true_negative": int(tn),
                "false_negative": int(fn)
            },
            "test_set_size": len(test_loader.dataset)
        },
        "explainability": "Grad-CAM on layer4 final conv block",
        "sample_inferences": sample_meta
    }

    meta_file = out_path / "metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Production metadata exported to: {meta_file}")
    return metadata


if __name__ == "__main__":
    run_evaluation()
