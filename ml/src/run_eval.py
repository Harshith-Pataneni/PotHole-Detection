print("=== SCRIPT STARTED ===", flush=True)
import sys
import os
import json
import time
from pathlib import Path

# Add ml/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

print("Importing PyTorch and vision libraries...", flush=True)
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve
from PIL import Image

print("Importing project modules...", flush=True)
from dataset import create_dataloaders, get_transforms
from model import build_model
from explain import GradCAM, overlay_heatmap, estimate_visual_severity

print("All imports complete. Setting up device...", flush=True)

device = torch.device("cpu")
out_dir = Path("./ml/models/v1")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Data
print("Loading test data...", flush=True)
_, _, test_loader, classes, class_to_idx = create_dataloaders(
    dataset_dir="./ml/dataset", batch_size=16
)

# 2. Model
checkpoint_file = out_dir / "checkpoint.pt"
print(f"Loading checkpoint {checkpoint_file}...", flush=True)
ckpt = torch.load(checkpoint_file, map_location=device, weights_only=False)

model = build_model(num_classes=len(classes), pretrained=False, device=device)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()
print("Model loaded.", flush=True)

# 3. Evaluate Test Set
all_targets = []
all_preds = []
all_probs = []

print("Running test set predictions...", flush=True)
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

print(f"TEST ACCURACY:  {acc:.4f}", flush=True)
print(f"TEST PRECISION: {prec:.4f}", flush=True)
print(f"TEST RECALL:    {rec:.4f}", flush=True)
print(f"TEST F1-SCORE:  {f1:.4f}", flush=True)
print(f"TEST ROC-AUC:   {auc:.4f}", flush=True)
print(f"CONFUSION MATRIX: TP={tp}, FP={fp}, TN={tn}, FN={fn}", flush=True)

# 4. Save Plots
print("Saving confusion matrix plot...", flush=True)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes)
plt.title(f"Test Confusion Matrix (F1: {f1:.3f})")
plt.xlabel("Predicted Class")
plt.ylabel("True Class")
plt.tight_layout()
plt.savefig(out_dir / "confusion_matrix.png", dpi=180)
plt.close()

print("Saving ROC curve plot...", flush=True)
fpr, tpr, _ = roc_curve(all_targets, all_probs)
plt.figure(figsize=(6, 5))
plt.plot(fpr, tpr, color="#2563eb", lw=2, label=f"ROC (AUC = {auc:.3f})")
plt.plot([0, 1], [0, 1], color="#94a3b8", lw=1.5, linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(out_dir / "roc_curve.png", dpi=180)
plt.close()

# 5. Export clean weights
prod_weights = out_dir / "model.pt"
torch.save(model.state_dict(), prod_weights)
print(f"Exported model.pt to {prod_weights}", flush=True)

# 6. Sample Grad-CAM
print("Extracting sample Grad-CAM overlays...", flush=True)
sample_dir = out_dir / "sample_predictions"
sample_dir.mkdir(parents=True, exist_ok=True)
grad_cam = GradCAM(model, model.get_last_conv_layer())
_, eval_transform = get_transforms()

pothole_samples = list(Path("./ml/dataset/test/pothole").glob("*.*"))[:3]
normal_samples = list(Path("./ml/dataset/test/normal").glob("*.*"))[:3]
sample_records = []

for s_path in pothole_samples + normal_samples:
    img = Image.open(s_path).convert("RGB")
    tensor = eval_transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(tensor)
        prob = float(F.softmax(out, dim=1)[0, 1].item())
        is_p = prob >= 0.75
    hmap = grad_cam.generate_heatmap(tensor, class_idx=1)
    sev = estimate_visual_severity(prob, hmap, is_p)
    blended = overlay_heatmap(img, hmap)
    out_name = f"sample_{s_path.stem}.jpg"
    blended.save(sample_dir / out_name)
    sample_records.append({
        "file": s_path.name,
        "true_label": s_path.parent.name,
        "pothole_prob": round(prob, 4),
        "estimated_severity": sev["estimated_severity"]
    })

# 7. Metadata export
metadata = {
    "model_version": "v1",
    "model_type": "ResNet-50 Transfer Learning",
    "classes": classes,
    "class_to_idx": class_to_idx,
    "image_size": [224, 224, 3],
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
    "samples": sample_records
}

with open(out_dir / "metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("=== EVALUATION COMPLETE & ARTIFACT EXPORTED ===", flush=True)
