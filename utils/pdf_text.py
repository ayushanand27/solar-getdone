"""ReportLab-safe text and optional Unicode font registration."""

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

PDF_FONT = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"
_UNICODE_REGISTERED = False


def clean_pdf_text(text) -> str:
    """Replace unicode chars that break ReportLab Helvetica."""
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "₂": "2",
        "₁": "1",
        "₃": "3",
        "₄": "4",
        "₀": "0",
        "²": "2",
        "³": "3",
        "¹": "1",
        "₹": "Rs.",
        "→": "->",
        "←": "<-",
        "↑": "^",
        "↓": "v",
        "⟶": "->",
        "⇒": "=>",
        "—": "-",
        "–": "-",
        "✅": "[OK]",
        "❌": "[X]",
        "⚠️": "[!]",
        "⚠": "[!]",
        "✓": "OK",
        "✗": "X",
        "•": "-",
        "·": "-",
        "●": "*",
        "◉": "*",
        "○": "o",
        "☀️": "[Solar]",
        "☀": "[Solar]",
        "🔋": "[Battery]",
        "🛡️": "[Shield]",
        "🛡": "[Shield]",
        "⚡": "[Energy]",
        "🌿": "[CO2]",
        "💰": "[Cost]",
        "🌍": "[Earth]",
        "📊": "[Data]",
        "🔧": "[Maint]",
        "📋": "[Report]",
        "🌱": "[Carbon]",
        "💨": "[Wind]",
        "🌡️": "[Temp]",
        "🧪": "[H2]",
        "🪨": "[Coal]",
        "🔥": "[Gas]",
        "🟢": "[OK]",
        "🟡": "[!]",
        "🔴": "[X]",
        "°": " deg",
        "η": "n",
        "α": "a",
        "β": "b",
        "×": "x",
        "÷": "/",
        "≥": ">=",
        "≤": "<=",
        "≠": "!=",
        "∞": "inf",
        "½": "1/2",
        "¼": "1/4",
        "¾": "3/4",
        "Ω": "Ohm",
        "CO₂": "CO2",
        "H₂": "H2",
        "O₂": "O2",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Strip remaining chars outside latin-1 when using built-in fonts
    if PDF_FONT == "Helvetica":
        text = text.encode("latin-1", "replace").decode("latin-1").replace("?", "")
    return text


def register_unicode_font():
    """Register DejaVu/Arial if available; return body font name."""
    global PDF_FONT, PDF_FONT_BOLD, _UNICODE_REGISTERED
    if _UNICODE_REGISTERED:
        return PDF_FONT

    font_pairs = [
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
        (
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ]
    for regular, bold in font_pairs:
        if os.path.exists(regular):
            try:
                pdfmetrics.registerFont(TTFont("UniFont", regular))
                PDF_FONT = "UniFont"
                if os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont("UniFont-Bold", bold))
                    PDF_FONT_BOLD = "UniFont-Bold"
                else:
                    PDF_FONT_BOLD = "UniFont"
                _UNICODE_REGISTERED = True
                break
            except Exception:
                continue

    _UNICODE_REGISTERED = True
    return PDF_FONT


def pdf_paragraph(text, style):
    register_unicode_font()
    return Paragraph(clean_pdf_text(text), style)


def pdf_cell(value):
    register_unicode_font()
    return clean_pdf_text(value)
