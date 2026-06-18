"""Optional YOLO upload path — only imported when user uploads an image."""

import numpy as np
import streamlit as st
from PIL import Image

from utils.cv_config import add_threat_border, get_cv_verdict


@st.cache_resource
def load_yolo_model():
    from ultralytics import YOLO

    return YOLO("yolov8n.pt")


def run_yolo_cv_detection(image, filename):
    model = load_yolo_model()
    results = model(np.array(image), verbose=False)[0]

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
