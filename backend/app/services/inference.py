"""
Machine Learning Inference Engine
=================================
Loads the versioned PyTorch ResNet-50 model artifact and runs low-latency inference.
Generates:
- Probability score & classification ('pothole' vs 'normal')
- Grad-CAM spatial activation heatmap
- Transparent rule-based visual severity estimation
- Blended visualization overlay
"""

import sys
import json
import base64
import io
from pathlib import Path
from typing import Dict, Any, Tuple
import torch
import torch.nn.functional as F
from PIL import Image

# Ensure ml/src is importable
ml_src_path = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "src"
if str(ml_src_path) not in sys.path:
    sys.path.append(str(ml_src_path))

try:
    from model import build_model
    from dataset import get_transforms
    from explain import GradCAM, overlay_heatmap, estimate_visual_severity
except ImportError:
    # Fallback if running from different root
    build_model = None
    get_transforms = None
    GradCAM = None
    overlay_heatmap = None
    estimate_visual_severity = None

from app.config import settings
from app.core.logging import logger


class MLInferenceService:
    def __init__(self):
        self.device = torch.device(settings.DEVICE if torch.cuda.is_available() and settings.DEVICE == "cuda" else "cpu")
        self.model = None
        self.grad_cam = None
        self.eval_transform = None
        self.metadata: Dict[str, Any] = {}
        self.model_version = settings.MODEL_VERSION
        self.confidence_threshold = settings.POTHOLE_CONFIDENCE_THRESHOLD
        self._load_model()

    def _load_model(self):
        weights_path = Path(settings.MODEL_WEIGHTS_PATH)
        meta_path = Path(settings.MODEL_METADATA_PATH)

        if not weights_path.exists():
            logger.warning(f"Model weights not found at {weights_path}. Model will be loaded dynamically once trained.")
            return

        try:
            # Load metadata
            if meta_path.exists():
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                    self.model_version = self.metadata.get("model_version", self.model_version)
                    self.confidence_threshold = self.metadata.get("recommended_pothole_threshold", self.confidence_threshold)

            # Build model and load weights
            classes = self.metadata.get("classes", ["normal", "pothole"])
            self.model = build_model(num_classes=len(classes), device=self.device)
            state_dict = torch.load(str(weights_path), map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            self.model.eval()

            # Initialize Grad-CAM
            self.grad_cam = GradCAM(self.model, self.model.get_last_conv_layer())
            _, self.eval_transform = get_transforms()

            logger.info(f"Loaded ML model '{self.model_version}' from {weights_path} onto {self.device}")
        except Exception as e:
            logger.error(f"Failed to load ML model artifact: {e}")

    def predict(self, image: Image.Image) -> Tuple[Dict[str, Any], Image.Image]:
        """
        Runs inference on a PIL Image.
        Returns:
            result_dict: {
                is_pothole: bool,
                confidence: float,
                model_version: str,
                estimated_severity: str,
                severity_breakdown: dict,
                heatmap_preview_base64: str
            }
            blended_heatmap_image: PIL.Image
        """
        if self.model is None or self.eval_transform is None:
            # Attempt lazy reload
            self._load_model()
            if self.model is None:
                raise RuntimeError("CV model artifact is not loaded or weights are missing.")

        # Transform image to PyTorch tensor
        tensor_img = self.eval_transform(image).unsqueeze(0).to(self.device)

        # 1. Forward Pass
        with torch.no_grad():
            logits = self.model(tensor_img)
            probs = F.softmax(logits, dim=1)
            pothole_prob = float(probs[0, 1].item())

        is_pothole = pothole_prob >= self.confidence_threshold

        # 2. Grad-CAM Spatial Heatmap
        heatmap = self.grad_cam.generate_heatmap(tensor_img, class_idx=1)
        blended_overlay = overlay_heatmap(image, heatmap, alpha=0.45)

        # 3. Rule-Based Visual Severity Estimation
        severity_info = estimate_visual_severity(pothole_prob, heatmap, is_pothole)

        # 4. Generate base64 thumbnail for quick UI preview
        buffered = io.BytesIO()
        preview_thumb = blended_overlay.copy()
        preview_thumb.thumbnail((400, 300), Image.Resampling.LANCZOS)
        preview_thumb.save(buffered, format="JPEG", quality=75)
        base64_preview = base64.b64encode(buffered.getvalue()).decode("utf-8")

        result = {
            "is_pothole": is_pothole,
            "confidence": round(pothole_prob, 4),
            "model_version": self.model_version,
            "estimated_severity": severity_info["estimated_severity"],
            "severity_breakdown": severity_info,
            "heatmap_preview_base64": f"data:image/jpeg;base64,{base64_preview}"
        }

        return result, blended_overlay


inference_service = MLInferenceService()
