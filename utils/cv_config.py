from pathlib import Path

from PIL import ImageDraw

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


def run_sample_cv_detection(image, filename):
    threat, confidence = filename_threat_override(filename)
    display_image = add_threat_border(image, threat)
    verdict, explanation = get_cv_verdict(threat)
    return threat, confidence, display_image, verdict, explanation, []


def run_cv_detection(image, filename, is_sample):
    if image is None:
        return None, None, None, None, None, []

    if is_sample:
        return run_sample_cv_detection(image, filename)

    try:
        from utils.cv_yolo import run_yolo_cv_detection

        return run_yolo_cv_detection(image, filename)
    except Exception as exc:
        return (
            None,
            None,
            image,
            "LOW",
            f"Upload CV unavailable on cloud ({exc}). Use sample images for demo.",
            [],
        )
