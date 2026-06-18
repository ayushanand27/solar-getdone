"""Backward-compatible re-exports for scripts and local dev."""

from utils.cv_config import (  # noqa: F401
    SAMPLE_IMAGES,
    SAMPLES_DIR,
    add_threat_border,
    filename_threat_override,
    get_cv_verdict,
    run_cv_detection,
)
