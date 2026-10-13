# CivicWatch: Pothole Detection & Intelligent Road-Defect Reporting Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-ResNet50-EE4C2C.svg)](https://pytorch.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Detector%20(Roadmap)-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF.svg)](https://vitejs.dev/)
[![MLflow](https://img.shields.io/badge/MLflow-Tracking%20(Roadmap)-0194E2.svg)](https://mlflow.org/)
[![Docker](https://img.shields.io/badge/Docker-CI%2FCD%20(Roadmap)-2496ED.svg)](https://www.docker.com/)

An enterprise-grade, full-stack civic infrastructure platform enabling citizens and municipal road authorities to report, automatically verify, localize, and track road surface defects (potholes) using Computer Vision.

Designed with **rigorous ML validation**, production-grade asynchronous backend architecture, and interview-ready engineering standards.

---

## 1. Executive Summary & Resume Alignment Matrix

CivicWatch bridges citizen reporting and municipal road maintenance through an intelligent, automated verification pipeline. The platform addresses common municipal pain points: unverified complaints, spam submissions, lack of geospatial context, and inefficient inspection dispatching.

To ensure total transparency and alignment between our project roadmap and technical portfolio/resume specifications, the table below delineates **what is fully implemented and operational today (Phase 1)** versus **what is actively planned on the technical roadmap (Phase 2)**.

| Capability / Component | Resume Specification | Current Status | Implementation Details |
| :--- | :--- | :--- | :--- |
| **Pothole Classification** | Fine-tuned ResNet-50 classifier (97.9% acc, 99.9% ROC-AUC) | ✅ **Completed & Deployed** | Transfer learning on ResNet-50 (`layer4[-1]`), leak-free 70/15/15 split, achieving **97.92% accuracy**, **99.90% ROC-AUC**, and **98.89% precision**. |
| **Model Interpretability** | Grad-CAM for visual explanation | ✅ **Completed & Deployed** | Real-time gradient-weighted class activation mapping highlighting road surface defect regions; exported as overlay PNGs. |
| **Defect Severity Scoring** | Visual severity heuristic | ✅ **Completed & Deployed** | Transparent, multi-factor rule-based heuristic (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) using model confidence and spatial activation footprint. |
| **API & Backend Architecture** | JWT-secured asynchronous REST API | ✅ **Completed & Deployed** | FastAPI, Async SQLAlchemy (`aiosqlite`), Pydantic v2 validation, magic byte image verification, sequential ticketing (`PH-2026-XXXXXX`). |
| **Geospatial Reporting Portal** | Live geospatial reporting dashboard | ✅ **Completed & Deployed** | React 19 + Leaflet interactive map with browser GPS capture, cluster pins, citizen verification flow, and JWT-authenticated Admin Portal. |
| **Multi-Defect Localization** | YOLOv8 object detector pairing | 🔄 **Roadmap / In Progress** | Planned two-stage cascade: ResNet-50 acts as a fast high-precision gatekeeper; verified images route to fine-tuned YOLOv8 for multi-defect bounding boxes. |
| **Experiment Tracking** | MLflow experiment tracking & registry | 🔄 **Roadmap / In Progress** | Integration with MLflow to log training runs, loss/accuracy curves, hyperparameter sweeps, and model versioning/lifecycle management. |
| **Containerization & CI/CD** | Dockerized CI/CD pipeline | 🔄 **Roadmap / In Progress** | Multi-container Docker & Docker Compose setup (`backend`, `frontend`, `db`) paired with GitHub Actions for automated testing and model regression checks. |

---

## 2. End-to-End System Architecture

CivicWatch employs a tiered architecture designed to isolate client interactions, model inference, and persistence layers.

```
                          CITIZEN / MUNICIPAL CLIENT
                  (React 19 + Leaflet + Lucide + Vite 8)
                                     │
                    POST /api/v1/reports (Multipart Form)
                                     ▼
                           FASTAPI BACKEND
            ┌────────────────────────┴────────────────────────┐
            │  - Magic Byte MIME Verification (JPEG/PNG/WebP)  │
            │  - Pillow Pixel Integrity & Size Bounds (<10MB) │
            │  - Non-Guessable UUIDv4 File Storage (/uploads)  │
            │  - Async SQLAlchemy Session Handling            │
            └────────────────────────┬────────────────────────┘
                                     │
                                     ▼
                        TWO-STAGE CV PIPELINE
            ┌────────────────────────┴────────────────────────┐
            │ [STAGE 1: VERIFICATION GATEKEEPER] (DEPLOYED)   │
            │  - PyTorch ResNet-50 Transfer Learning Engine   │
            │  - Strict Confidence Gate (Threshold = 0.75)   │
            │  - Grad-CAM Interpretability Activation Map     │
            │  - Rule-Based Severity Heuristic                │
            ├─────────────────────────────────────────────────┤
            │ [STAGE 2: SPATIAL LOCALIZATION] (IN PROGRESS)   │
            │  - Fine-Tuned YOLOv8 Object Detector            │
            │  - Multi-Pothole Bounding Box Extraction        │
            │  - Defect Count & Surface Dimension Estimation  │
            └────────────────────────┬────────────────────────┘
                    Rejected (<0.75) │ Verified (>=0.75)
            ┌────────────────────────┴────────────────────────┐
            ▼                                                 ▼
      Citizen Guidance Flow                         Incident Record Created
      (Visual feedback & retry)                     - Assigned PH-2026-XXXXXX
                                                    - GPS Lat/Lng Stored
                                                    - Admin Notification Dispatched
                                                    - Real-Time Map Pin Rendered
```

---

## 3. Computer Vision & ML Pipeline

### 3.1 ResNet-50 Verification Classifier (Implemented)

To ensure the municipal platform is not inundated with non-pothole photos (e.g., clean asphalt, footpaths, random objects), the first stage utilizes an ImageNet-pretrained **ResNet-50** deep transfer learning classifier.

#### Dataset Curation & Leakage Prevention
- **Pothole Class**: Ingested 618 positive pothole images from the `sachinpatel21/pothole-image-dataset`.
- **Normal Road Class**: Paired with 352 verified normal road surface images from `atulyakumar98/pothole-detection-dataset` to prevent base-rate distortion and ensure robust negative-class rejection.
- **Deduplication**: Executed MD5 hashing across all images, removing 11 duplicate files prior to splitting.
- **Partitioning**: Partitioned into **70% Train (671 images)**, **15% Validation (144 images)**, and **15% Hold-out Test (144 images)** strictly *before* applying data augmentation (random horizontal flips, 15° rotation, and color jitter).

#### Hold-Out Test Evaluation Metrics
Evaluated on the completely unseen 144-image hold-out test set (91 potholes, 53 normal roads):

| Metric | Empirical Score | Engineering Significance |
| :--- | :--- | :--- |
| **Accuracy** | **97.92%** | High overall fidelity across unseen road conditions |
| **Precision** | **98.89%** | Only 1 false positive out of 53 clean road images, preventing inspection spam |
| **Recall** | **97.80%** | Accurately flags 89 out of 91 real potholes |
| **F1-Score** | **98.34%** | Harmonic balance between sensitivity and selectivity |
| **ROC-AUC** | **99.90%** | Exceptional discriminative capacity across classification thresholds |

**Confusion Matrix Breakdown:**
- **True Positives (TP)**: 89
- **False Positives (FP)**: 1 (Clean road flagged as pothole)
- **True Negatives (TN)**: 52
- **False Negatives (FN)**: 2 (Subtle surface anomalies missed)

---

### 3.2 Model Interpretability via Grad-CAM (Implemented)

Rather than treating the deep network as an inscrutable black box, CivicWatch integrates **Grad-CAM (Gradient-weighted Class Activation Mapping)**:
1. Gradients of the predicted class score are backpropagated into the final convolutional layer of ResNet-50 (`layer4[-1]`).
2. Global average pooling computes channel-wise importance weights $\alpha_k^c$.
3. A weighted combination followed by ReLU produces a 2D spatial heatmap highlighting the specific asphalt distress, edges, and cavity depressions driving the classification.
4. The heatmap is normalized, color-mapped via OpenCV (JET colormap), and composited over the original image for real-time visualization on both the citizen submission preview and administrative dashboard.

---

### 3.3 Rule-Based Severity Estimation (Implemented)

Because raw 2D classification datasets do not provide millimeter-level 3D depth measurements, CivicWatch employs a transparent, scientifically honest heuristic rather than an unvalidated regression head:
$$\text{Severity Index} = (\text{Model Confidence} \times 0.6) + (\text{High-Activation Footprint Ratio} \times 0.4)$$
- **LOW**: Minor surface wear or low visual footprint.
- **MEDIUM**: Clear localized defect requiring routine patching.
- **HIGH**: Substantial surface cavity with pronounced road hazard potential.
- **CRITICAL**: Large, high-activation defect requiring priority municipal dispatch.

---

### 3.4 YOLOv8 Multi-Defect Detection Pipeline (Planned / In Progress)

As outlined in the project vision, **Phase 2** pairs the existing ResNet-50 gatekeeper with an **Ultralytics YOLOv8 detector** in a high-efficiency cascade:

```
[Citizen Image] ──▶ [ResNet-50 Gatekeeper] ──▶ Verified? ──▶ [YOLOv8 Detector] ──▶ Bounding Boxes & Count
                                                │ (No)
                                                ▼
                                         [Drop / Retry]
```

#### Why Pair ResNet-50 with YOLOv8?
1. **Inference Efficiency**: Running full object detection models across millions of public citizen uploads consumes heavy GPU/CPU cycles. ResNet-50 acts as a fast, lightweight gatekeeper, filtering out 95%+ of irrelevant or clear-road imagery in milliseconds.
2. **Multi-Defect Localization**: For confirmed damaged roads, YOLOv8 identifies individual bounding boxes ($x, y, w, h$) per pothole, handles multi-defect scenes, and reports total pothole count per image.
3. **Dataset Ingestion**: Fine-tuning YOLOv8 on bounding-box road damage benchmarks (e.g., Road Damage Dataset **RDD2020/RDD2022** and Roboflow Pothole Bounding Box Datasets) to supplement the existing classification baseline.

---

### 3.5 MLflow Experiment Tracking & Model Registry (Planned / In Progress)

To elevate CivicWatch to enterprise ML standards:
- **Run Tracking**: Logging loss curves, accuracy, ROC-AUC, learning rates, batch sizes, and optimizer configurations directly to a centralized MLflow Tracking Server.
- **Artifact Versioning**: Automatically logging weights (`model.pt`, `weights.onnx`), confusion matrix plots, ROC curves, and Grad-CAM sample inferences.
- **Model Registry**: Staging models through `None` &rarr; `Staging` &rarr; `Production` lifecycle stages, ensuring seamless rollbacks and reproducible deployments.

---

## 4. Full-Stack Platform Features

### 4.1 Citizen Reporting Flow
- **Live Geolocation**: Automatically fetches browser GPS coordinates (`navigator.geolocation`) with fallback manual pin adjustment on Leaflet.
- **Instant Pre-Submission Inference**: Citizens can upload an image and preview the AI classification, confidence score, and Grad-CAM heatmap before submitting.
- **Automated Rejection Handling**: Submissions scoring below the 0.75 confidence threshold are intercepted with friendly feedback, avoiding database bloat.
- **Incident Reference**: Successful reports receive a tracking reference code (`PH-2026-XXXXXX`).

### 4.2 Administrative Management Portal
- **JWT Authentication**: Protected administrative dashboard secured via JSON Web Tokens with configurable expiration.
- **Interactive Defect Map**: Clustered geospatial pins color-coded by defect severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and lifecycle status (`PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `RESOLVED`).
- **Telemetry & Evaluation Visualizer**: Live dashboard streaming test set confusion matrix heatmaps, ROC curves, and model metadata directly from the backend.
- **Status Workflow**: Administrators can transition report states, record official municipal work order notes, and trigger notification alerts.

---

## 5. Security & Defensive Engineering

1. **Strict File Magic-Byte Validation**: Does not rely on client-provided MIME headers. Inspects raw binary headers (`FF D8 FF` for JPEG, `89 50 4E 47` for PNG, `RIFF...WEBP` for WebP).
2. **Pillow Pixel Verification**: Validates that uploaded files can be properly decoded as bitmap images, preventing polyglot file uploads and image exploit payloads.
3. **UUIDv4 Storage Keys**: User filenames are completely discarded. All uploads are assigned unguessable UUIDv4 identifiers.
4. **Input Sanitization**: Pydantic v2 validates coordinate bounds (latitude $[-90, 90]$, longitude $[-180, 180]$) and payload sizes (capped at 10 MB).
5. **Admin Isolation**: Role-based endpoints strictly enforce JWT Bearer signature checks (HS256).

---

## 6. Quick Start & Setup

### Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 18+ and npm

### 1. Clone & Configure Environment
```bash
git clone https://github.com/Harshith-Pataneni/PotHole-Detection.git
cd PotHole-Detection

# Copy environment template
cp .env.example .env
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The database schema and default administrator credentials (`admin@civicworks.org` / `admin_secure_change_me_123`) are initialized automatically upon startup.*

### 3. Frontend Setup
In a separate terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 7. Model Training & Evaluation Guide

To retrain the classification model or reproduce evaluation artifacts:

```bash
# 1. Clean, deduplicate, and split dataset
python ml/data/prepare_dataset.py

# 2. Train ResNet-50 classifier
python ml/src/train.py

# 3. Evaluate hold-out test set & export production artifacts
python ml/src/run_eval.py
```

Generated evaluation artifacts are stored in `ml/models/v1/`:
- `model.pt`: Clean state dictionary weights.
- `metadata.json`: Machine-readable evaluation metrics and threshold configuration.
- `confusion_matrix.png`: High-resolution test set confusion matrix.
- `roc_curve.png`: Receiver Operating Characteristic curve.
- `sample_predictions/`: Sample images overlaid with Grad-CAM heatmaps.

---

## 8. Docker & CI/CD Pipeline (Roadmap)

To fulfill the production-grade specification outlined in the project vision, containerization and CI/CD workflows are structured as follows:

### Planned Docker Compose Topology
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/pothole_platform.db
    volumes:
      - uploads_data:/app/uploads
      - db_data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  uploads_data:
  db_data:
```

### Planned CI/CD Pipeline (GitHub Actions)
- **Code Quality**: `ruff` / `flake8` linting and formatting verification.
- **Unit & Integration Tests**: `pytest` covering FastAPI endpoints and authentication workflows.
- **Model Regression Checks**: Validates that hold-out test accuracy remains $\ge 95\%$ prior to merging.
- **Container Build & Registry Push**: Builds multi-stage Docker images on release tags.

---

## 9. API Reference

### Public Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health check and loaded model version |
| `POST` | `/api/v1/predict` | Upload image for instant inference and Grad-CAM preview |
| `POST` | `/api/v1/reports` | Submit road defect report with GPS coordinates and image |
| `GET` | `/api/v1/reports` | Retrieve list of verified defects for public map rendering |
| `GET` | `/api/v1/reports/{id}` | Retrieve detailed report record by ID or reference code |

### Administrative Endpoints (Bearer JWT Required)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate administrator and receive JWT token |
| `GET` | `/api/v1/admin/stats` | Retrieve aggregate metrics (status counts, severity distribution) |
| `PATCH` | `/api/v1/reports/{id}` | Update report status (`PENDING` &rarr; `RESOLVED`) and append work notes |
| `GET` | `/api/v1/model/metrics` | Retrieve hold-out test metrics and model metadata |
| `GET` | `/api/v1/model/confusion-matrix.png` | Stream high-res confusion matrix plot |
| `GET` | `/api/v1/model/roc-curve.png` | Stream high-res ROC curve plot |

---

## 10. Real-World Limitations

1. **Domain Shift & Weather Conditions**: The current training distribution is predominantly daylight asphalt. Performance under snow, torrential rain, heavy reflections, or night-time street lighting requires domain adaptation fine-tuning.
2. **2D Surface vs. 3D Volumetric Depth**: Monocular 2D images cannot compute volumetric asphalt displacement; severity is estimated using area and model confidence rather than LiDAR/stereo depth estimation.
3. **GPS Precision**: Accuracy varies between mobile hardware (satellite GPS, $\sim 3\text{m}$) and desktop browsers (Wi-Fi/IP triangulation, $\sim 20\text{--}50\text{m}$). The UI allows manual pin refinement to address this.

---

## 11. Authors & License

- **Developer**: Srinivasa Harshith Pataneni ([GitHub](https://github.com/Harshith-Pataneni) • [LinkedIn](https://linkedin.com/in/srinivasa-harshith-pataneni))
- **Affiliation**: BITS Pilani, K. K. Birla Goa Campus
- **License**: MIT License
