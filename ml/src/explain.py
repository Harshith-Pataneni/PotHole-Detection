"""
Explainability & Rule-Based Severity Estimation
================================================
Implements Grad-CAM (Gradient-weighted Class Activation Mapping) for ResNet50
and a transparent, scientifically honest rule-based visual severity estimator.

NOTE ON ML HONESTY:
The underlying dataset only provides binary image-level labels ('pothole' vs 'normal').
Severity is NOT an ML ground-truth class, but an estimated visual heuristic combining:
1. Model prediction confidence
2. Grad-CAM defect surface area coverage ratio
3. Peak activation intensity
"""

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import matplotlib.cm as cm


class GradCAM:
    """
    Grad-CAM implementation for PyTorch CNN architectures.
    Hooks into the final convolutional layer.
    """
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None

        # Register forward and backward hooks
        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_full_backward_hook(self._backward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: int = 1) -> np.ndarray:
        """
        Generates 2D normalized heatmap [0, 1] for the specified class index.
        """
        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        logits = self.model(input_tensor)
        target_score = logits[:, class_idx]

        # Backward pass to obtain gradients
        target_score.backward(retain_graph=True)

        # Global average pooling of gradients: [B, C, 1, 1]
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])

        # Weight activations by gradients
        weighted_activations = torch.zeros_like(self.activations[0])
        for i, weight in enumerate(pooled_gradients):
            weighted_activations[i, :, :] = self.activations[0, i, :, :] * weight

        # ReLU on sum of weighted activations
        heatmap = torch.sum(weighted_activations, dim=0).cpu().numpy()
        heatmap = np.maximum(heatmap, 0)

        # Normalize to [0, 1]
        max_val = np.max(heatmap)
        if max_val > 0:
            heatmap = heatmap / max_val
        else:
            heatmap = np.zeros_like(heatmap)

        return heatmap


def overlay_heatmap(original_image: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> Image.Image:
    """
    Resizes 2D heatmap to original image dimensions and creates a colormap overlay.
    """
    orig_w, orig_h = original_image.size
    heatmap_pil = Image.fromarray(np.uint8(255 * heatmap)).resize((orig_w, orig_h), resample=Image.Resampling.BILINEAR)
    heatmap_norm = np.array(heatmap_pil) / 255.0

    # Apply 'jet' or 'inferno' colormap
    colormap = cm.get_cmap("inferno")
    heatmap_colored = colormap(heatmap_norm)[:, :, :3]  # Drop alpha channel
    heatmap_colored = np.uint8(heatmap_colored * 255)

    heatmap_overlay_pil = Image.fromarray(heatmap_colored).convert("RGBA")
    original_rgba = original_image.convert("RGBA")

    # Blend images
    blended = Image.blend(original_rgba, heatmap_overlay_pil, alpha=alpha)
    return blended.convert("RGB")


def estimate_visual_severity(confidence: float, heatmap: np.ndarray, is_pothole: bool) -> dict:
    """
    Transparent, documented heuristic for estimating visual pothole severity.

    Formula:
    - Coverage Ratio: Fraction of spatial feature map with high activation (> 0.40)
    - Peak Intensity: Max activation value [0, 1]
    - Heuristic Score = (Confidence * 0.40) + (Coverage * 0.45) + (Peak * 0.15)

    Classification Bands:
    - Score >= 0.70  -> CRITICAL
    - Score >= 0.50  -> HIGH
    - Score >= 0.32  -> MEDIUM
    - Score < 0.32   -> LOW
    """
    if not is_pothole or confidence < 0.50:
        return {
            "estimated_severity": "LOW",
            "severity_score": 0.1,
            "coverage_ratio": 0.0,
            "heuristic_breakdown": "Image not verified as pothole or below threshold."
        }

    coverage_ratio = float(np.mean(heatmap > 0.40))
    peak_intensity = float(np.max(heatmap)) if heatmap.size > 0 else 0.0

    severity_score = (confidence * 0.40) + (coverage_ratio * 0.45) + (peak_intensity * 0.15)
    severity_score = min(max(severity_score, 0.0), 1.0)

    if severity_score >= 0.70:
        severity = "CRITICAL"
    elif severity_score >= 0.50:
        severity = "HIGH"
    elif severity_score >= 0.32:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "estimated_severity": severity,
        "severity_score": round(severity_score, 3),
        "coverage_ratio": round(coverage_ratio, 3),
        "peak_intensity": round(peak_intensity, 3),
        "heuristic_breakdown": f"Weighted composite of confidence ({confidence:.2f}), Grad-CAM coverage ({coverage_ratio:.2f}), and peak intensity ({peak_intensity:.2f})"
    }
