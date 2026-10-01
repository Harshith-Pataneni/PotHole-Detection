"""
Model Architecture Definition
=============================
Defines the Pothole Classifier using a pretrained ResNet-50 backbone
with custom classification head and dropout regularization.
"""

import torch
import torch.nn as nn
from torchvision import models


class PotholeClassifier(nn.Module):
    """
    ResNet-50 transfer learning model for binary road defect classification.
    Classes: [normal, pothole]
    """
    def __init__(self, num_classes: int = 2, pretrained: bool = True, freeze_backbone: bool = False, dropout_rate: float = 0.4):
        super().__init__()
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet50(weights=weights)

        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Replace classification head
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def get_last_conv_layer(self):
        """Returns the final convolutional block for Grad-CAM activation mapping."""
        return self.backbone.layer4[-1]


def build_model(num_classes: int = 2, pretrained: bool = True, freeze_backbone: bool = False, device: str = "cpu") -> PotholeClassifier:
    model = PotholeClassifier(num_classes=num_classes, pretrained=pretrained, freeze_backbone=freeze_backbone)
    return model.to(device)


if __name__ == "__main__":
    m = build_model()
    dummy = torch.randn(2, 3, 224, 224)
    out = m(dummy)
    print("Model test output shape:", out.shape)
