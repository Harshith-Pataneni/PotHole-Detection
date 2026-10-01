"""
End-to-End Training & Evaluation Pipeline Runner
=================================================
Executes:
1. Model training with early stopping & checkpointing
2. Final evaluation on strictly hold-out test set
3. Exporting production model artifact (model.pt + metadata.json)
"""

import sys
from pathlib import Path

# Add src to python path
src_dir = Path(__file__).parent / "src"
sys.path.append(str(src_dir))

from train import run_training
from evaluate import run_evaluation

if __name__ == "__main__":
    print("==================================================")
    print("STEP 1: TRAINING RESNET-50 POTHOLE CLASSIFIER (v1)")
    print("==================================================")
    best_checkpoint, history = run_training(epochs=4, batch_size=16, lr=2e-4, patience=3)

    print("\n==================================================")
    print("STEP 2: RUNNING FINAL HOLD-OUT TEST EVALUATION")
    print("==================================================")
    metadata = run_evaluation(checkpoint_path=str(best_checkpoint))

    print("\n==================================================")
    print("SUCCESS: MODEL ARTIFACT v1 READY FOR PRODUCTION")
    print("==================================================")
