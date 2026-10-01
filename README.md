# CivicWatch: Pothole Detection & Intelligent Road-Defect Reporting Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-ResNet50-EE4C2C.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF.svg)](https://vitejs.dev/)

An enterprise-ready, full-stack civic infrastructure platform that allows citizens and municipal road authorities to report, automatically verify, localize, and track road surface defects (potholes) using Computer Vision.

Designed with **strict ML honesty**, production-grade architecture, and interview-ready engineering standards.

---

## 1. Project Overview

Municipal road authorities struggle with inefficient defect reporting pipelines: citizens report issues without verified imagery or precise GPS coordinates, resulting in high rates of false reports, wasted inspection drives, and delayed road repairs.

**CivicWatch** provides an automated, end-to-end civic reporting pipeline:
1. **Citizen Upload**: Citizen captures a suspected road pothole and grants browser geolocation permission.
2. **PyTorch CV Inference**: The image is analyzed in real time by an ImageNet-pretrained **ResNet-50** deep transfer learning classifier.
3. **Threshold Gatekeeping**: Low-confidence or non-pothole images are rejected from the official municipal registry with citizen guidance, eliminating spam and false alarms.
4. **Grad-CAM Localization**: Spatial activation heatmaps highlight the specific road surface features triggering the prediction.
5. **Estimated Visual Severity**: A transparent, rule-based heuristic computes visual severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) based on confidence and spatial defect footprint.
6. **Automated Incident Logging**: Confirmed defects are assigned a sequential reference (`PH-2026-XXXXXX`), stored in the database, visualized on an interactive Leaflet road map, and dispatched via administrative email notifications.

---

## 2. System Architecture

```
                  CITIZEN WEB CLIENT
             (React 19 + Lucide + Leaflet)
                          │
             POST /api/v1/reports (Multipart)
                          ▼
                  FASTAPI BACKEND
        ┌─────────────────┴─────────────────┐
        │  - Image Magic Byte & Size Check  │
        │  - Pydantic v2 Request Validation │
        │  - Async SQLAlchemy (aiosqlite)   │
        └─────────────────┬─────────────────┘
                          │
                          ▼
                ML INFERENCE ENGINE
        ┌─────────────────┴─────────────────┐
        │  - PyTorch ResNet-50 (v1 Artifact)│
        │  - Threshold Gate (Threshold=0.75)│
        │  - Grad-CAM Heatmap Extraction    │
        │  - Transparent Severity Heuristic │
        └──────────────┬─────────────┬──────┘
       Rejected (<0.75)│             │ Verified (>=0.75)
                       ▼             ▼
             Citizen Retry Flow    Database Record (PENDING)
                                   + Secure Image Storage (/uploads)
                                   + Admin Email Alert Dispatched
                                   + Interactive Map Pin Rendered
```

---

## 3. Computer Vision & ML Pipeline

### Strict ML Honesty & Dataset Analysis
- **Primary Dataset (`sachinpatel21/pothole-image-dataset`)**: 618 positive pothole images with **0 bounding boxes** and **0 negative normal road samples**.
- **Negative Class Ingestion**: To prevent statistical base-rate collapse, we paired the 618 pothole images with 352 verified normal road surface images from benchmark road datasets (`atulyakumar98/pothole-detection-dataset`).
- **Honesty Distinction**: Because no bounding-box annotations exist in the training data, **claiming object detection (YOLO) would be scientifically fraudulent**. Instead, we employ a genuine **ResNet-50 Transfer Learning Classifier** and extract spatial localization using **Grad-CAM (Gradient-weighted Class Activation Mapping)** on `layer4[-1]`.
- **Severity Classification**: True severity labels do not exist in the training set. Therefore, severity is explicitly documented as a **rule-based visual heuristic**, combining model confidence, defect coverage ratio, and peak activation intensity.

### Preprocessing & Leak-Free Splitting
Data was deduplicated via MD5 hashes (removing 11 duplicate files) and partitioned **strictly before data augmentation**:
- **Train (70%)**: 671 images (427 pothole, 244 normal) — with random horizontal flip, 15° rotation, and color jitter.
- **Validation (15%)**: 144 images (92 pothole, 52 normal) — deterministic resize (224x224) and ImageNet normalization.
- **Hold-out Test (15%)**: 144 images (91 pothole, 53 normal) — strictly isolated for final evaluation.

### Empirical Hold-Out Test Metrics
| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Test Accuracy** | **97.92%** | Overall correct classifications on unseen roads |
| **Test Precision** | **98.89%** | Only 1 false positive out of 53 normal road images |
| **Test Recall** | **97.80%** | Catches 89 out of 91 real road potholes |
| **Test F1-Score** | **98.34%** | Optimal harmonic balance of precision and recall |
| **Test ROC-AUC** | **99.90%** | Exceptional discriminative power between classes |

#### Confusion Matrix Breakdown:
- **True Positives (TP)**: 89
- **False Positives (FP)**: 1
- **True Negatives (TN)**: 52
- **False Negatives (FN)**: 2

---

## 4. Quick Start & Setup

### Prerequisites
- Python 3.12+ (or Python 3.14)
- Node.js 18+ and npm

### 1. Clone & Configure Environment
```bash
git clone https://github.com/your-username/pothole-detection-platform.git
cd pothole-detection-platform

# Copy environment template
cp .env.example .env
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Backend will start on `http://127.0.0.1:8000`. Database tables and default administrator account are automatically initialized on startup.

### 3. Frontend Setup
In a new terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 5. Environment Variables (`.env.example`)

| Variable | Description | Default | Scope |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Environment mode (`development` / `production`) | `development` | Server |
| `DATABASE_URL` | SQLAlchemy async connection string | `sqlite+aiosqlite:///./pothole_platform.db` | Server |
| `AUTH_SECRET` | Secret key used to sign and verify admin JWTs | Min 32 chars | Server |
| `POTHOLE_CONFIDENCE_THRESHOLD` | Threshold below which submissions are rejected | `0.75` | Server |
| `MODEL_WEIGHTS_PATH` | File path to production `.pt` state dict | `./ml/models/v1/model.pt` | Server |
| `MODEL_METADATA_PATH` | File path to production `metadata.json` | `./ml/models/v1/metadata.json` | Server |
| `EMAIL_PROVIDER` | Notification backend (`console` / `smtp` / `resend`) | `console` | Server |
| `ADMIN_INITIAL_EMAIL` | Default administrator account email | `admin@civicworks.org` | Server |
| `ADMIN_INITIAL_PASSWORD` | Default administrator account password | `admin_secure_change_me_123` | Server |

---

## 6. Training & Evaluation Pipeline

To retrain the model on new data or reproduce evaluation:

```bash
# 1. Prepare and split dataset
python ml/data/prepare_dataset.py

# 2. Train ResNet-50 classifier
python ml/src/train.py

# 3. Run hold-out evaluation & export production artifacts
python ml/src/run_eval.py
```

Artifacts are exported to `ml/models/v1/`:
- `model.pt`: Clean state dictionary weights for production deployment.
- `metadata.json`: Machine-readable evaluation metrics, threshold, and sample inferences.
- `confusion_matrix.png`: High-resolution seaborn heatmap plot.
- `roc_curve.png`: Receiver Operating Characteristic curve.
- `sample_predictions/`: Sample images overlaid with Grad-CAM activation heatmaps.

---

## 7. API Reference

### Public Endpoints
- `GET /api/v1/health`: Service health check and loaded model version.
- `POST /api/v1/predict`: Upload image for instant inference and Grad-CAM preview without saving.
- `POST /api/v1/reports`: Submit defect report (Multipart: `file`, `latitude`, `longitude`, `user_priority`).
- `GET /api/v1/reports`: Public list of verified road defects for map pins.
- `GET /api/v1/reports/{id}`: Detailed report view by UUID or public reference ID.

### Administrative Endpoints (Bearer JWT Required)
- `POST /api/v1/auth/login`: Admin authentication returning JWT access token.
- `GET /api/v1/admin/stats`: Aggregate metrics (counts by status, severity, avg confidence).
- `PATCH /api/v1/reports/{id}`: Transition report status (`PENDING` &rarr; `UNDER_REVIEW` &rarr; `VERIFIED` / `REJECTED` &rarr; `RESOLVED`) and append work order notes.
- `GET /api/v1/model/metrics`: Model hold-out test metrics and metadata.
- `GET /api/v1/model/confusion-matrix.png`: Stream confusion matrix plot.
- `GET /api/v1/model/roc-curve.png`: Stream ROC curve plot.

---

## 8. Security Architecture

1. **Untrusted Image Validation**: Images are validated by inspecting binary magic bytes (`FF D8 FF` for JPEG, `89 50 4E 47` for PNG, `RIFF...WEBP` for WebP), decoding pixels via Pillow, and rejecting payloads > 10MB.
2. **Safe Storage Keys**: Client-supplied filenames are discarded. Each image receives a non-guessable UUID v4 filename.
3. **Admin Privilege Isolation**: Protected endpoints enforce cryptographic signature verification of JWT Bearer tokens with expiration.
4. **Secret Containment**: Zero secrets or credentials are hardcoded or leaked to client bundles. `.env` is explicitly ignored by Git.

---

## 9. Real-World Limitations

1. **Dataset Bias**: Training data contains predominantly dry, daylight asphalt. Model performance on wet roads, snow, night lighting, or unpaved dirt roads may degrade.
2. **Severity Estimation**: Pothole depth and volume cannot be measured with a single 2D RGB camera. The severity score is a visual area and confidence proxy, not an engineering structural grade.
3. **GPS Accuracy**: Browser geolocation accuracy varies between mobile devices (GPS-enabled, ~3-5m) and desktop browsers (IP/Wi-Fi triangulation, ~20-50m).
