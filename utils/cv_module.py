from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

SAMPLE_IMAGES = [
    "bs1.png",
    "bs2.png",
    "bs3.png",
    "dh1.png",
    "dh2.png",
    "dh3.png",
    "c1.png",
    "c2.png",
    "c3.png",
]
SAMPLES_DIR = Path("samples") if Path("samples").exists() else Path("sample")


@st.cache_resource
def load_yolo_model():
    try:
        import cv2  # noqa: F401 — required by ultralytics on upload path
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV (cv2) is not available. Sample images still work; "
            "upload detection needs opencv-python-headless on the server."
        ) from exc

    from ultralytics import YOLO

    return YOLO("yolov8n.pt")


def filename_threat_override(filename):
    stem = Path(filename).stem.lower()
    if stem.startswith("bs"):
        return "bird", 0.87
    if stem.startswith("dh"):
        return "dust", 0.91
    if stem.startswith("c"):
        return "damage", 0.84
    return None, None


def add_threat_border(image, threat_type, width=10):
    if threat_type is None:
        return image
    colors = {"bird": "red", "dust": "orange", "damage": "yellow"}
    color = colors.get(threat_type)
    if not color:
        return image
    bordered = image.copy()
    draw = ImageDraw.Draw(bordered)
    w, h = bordered.size
    for i in range(width):
        draw.rectangle([i, i, w - 1 - i, h - 1 - i], outline=color)
    return bordered


def get_cv_verdict(threat_type):
    if threat_type == "bird":
        return "MEDIUM", "Bird/animal on panels — deterrent and partial shield recommended."
    if threat_type == "dust":
        return "MEDIUM", "Dust/haze detected — auto-clean sequence and efficiency monitoring."
    if threat_type == "damage":
        return "HIGH", "Cracked/damaged panel detected — immediate maintenance required."
    return "LOW", "No solar-specific threats detected in this image."


def run_cv_detection(image, filename, is_sample):
    if image is None:
        return None, None, None, None, None, []

    if is_sample:
        threat, confidence = filename_threat_override(filename)
        display_image = add_threat_border(image, threat)
        return threat, confidence, display_image, *get_cv_verdict(threat), []

    try:
        model = load_yolo_model()
        results = model(np.array(image), verbose=False)[0]
    except Exception as exc:
        return (
            None,
            None,
            image,
            "LOW",
            f"Upload CV unavailable ({exc}). Use sample images for demo.",
            [],
        )

    detections = []
    if results.boxes is not None:
        for box in results.boxes:
            cls_id = int(box.cls[0])
            detections.append(
                {
                    "class": results.names[cls_id],
                    "confidence": round(float(box.conf[0]), 2),
                }
            )

    annotated_bgr = results.plot()
    annotated_rgb = annotated_bgr[:, :, ::-1]
    annotated = Image.fromarray(annotated_rgb)

    bird_hits = [d for d in detections if d["class"] == "bird"]
    if bird_hits:
        threat = "bird"
        confidence = max(d["confidence"] for d in bird_hits)
    elif detections:
        top = max(detections, key=lambda d: d["confidence"])
        threat = top["class"]
        confidence = top["confidence"]
    else:
        threat = None
        confidence = None

    border_threat = threat if threat in ("bird", "dust", "damage") else None
    display_image = add_threat_border(annotated, border_threat)
    verdict, explanation = get_cv_verdict(threat if threat in ("bird", "dust", "damage") else None)
    return threat, confidence, display_image, verdict, explanation, detections
