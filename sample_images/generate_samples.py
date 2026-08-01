"""Generates the synthetic sample images/PDF committed alongside this
script, so the repository ships runnable examples without depending on
any copyrighted scans. Re-run with ``python sample_images/generate_samples.py``
after changing the content below.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_invoice() -> Path:
    img = Image.new("RGB", (900, 1200), "white")
    draw = ImageDraw.Draw(img)
    title_font = _font(42)
    body_font = _font(24)
    draw.text((60, 50), "INVOICE", fill="black", font=title_font)
    lines = [
        "ImageOCR Pro Demo Company",
        "123 Sample Street, Springfield",
        "",
        "Invoice #: INV-2026-0731",
        "Date: 2026-08-01",
        "",
        "Description                Qty     Price       Total",
        "OCR Software License        1     $499.00     $499.00",
        "Support Plan (1 year)       1     $120.00     $120.00",
        "",
        "Subtotal:                                     $619.00",
        "Tax (8%):                                       $49.52",
        "Total Due:                                     $668.52",
        "",
        "Thank you for your business!",
    ]
    y = 140
    for line in lines:
        draw.text((60, y), line, fill="black", font=body_font)
        y += 40
    path = OUTPUT_DIR / "sample_invoice.png"
    img.save(path)
    return path


def make_letter() -> Path:
    img = Image.new("RGB", (850, 1100), "white")
    draw = ImageDraw.Draw(img)
    body_font = _font(22)
    paragraph = (
        "Dear Reader,\n\n"
        "This is a synthetic sample document generated for ImageOCR Pro.\n"
        "It demonstrates multi-paragraph text extraction, including\n"
        "punctuation, numbers (1234567890) and mixed-case words.\n\n"
        "Optical Character Recognition converts printed or handwritten\n"
        "text within an image into machine-encoded text, enabling search,\n"
        "editing and analysis of scanned documents.\n\n"
        "Sincerely,\nThe ImageOCR Pro Team"
    )
    draw.multiline_text((60, 60), paragraph, fill="black", font=body_font, spacing=14)
    path = OUTPUT_DIR / "sample_letter.jpg"
    img.save(path, quality=92)
    return path


def make_business_card() -> Path:
    img = Image.new("RGB", (600, 350), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 599, 349], outline="black", width=2)
    draw.text((40, 40), "Jane Doe", fill="black", font=_font(30))
    draw.text((40, 90), "Senior Software Engineer", fill="black", font=_font(20))
    draw.text((40, 160), "jane.doe@example.com", fill="black", font=_font(18))
    draw.text((40, 190), "+1 (555) 123-4567", fill="black", font=_font(18))
    draw.text((40, 220), "www.example.com", fill="black", font=_font(18))
    path = OUTPUT_DIR / "sample_business_card.png"
    img.save(path)
    return path


def make_skewed_receipt() -> Path:
    img = Image.new("RGB", (700, 900), "white")
    draw = ImageDraw.Draw(img)
    body_font = _font(22)
    lines = ["RECEIPT", "Store #42", "", "Item A       $4.50", "Item B       $9.25", "Item C      $12.00", "", "Total       $25.75"]
    y = 60
    for line in lines:
        draw.text((60, y), line, fill="black", font=body_font)
        y += 36
    rotated = img.rotate(-4, expand=True, fillcolor="white")
    path = OUTPUT_DIR / "sample_receipt_skewed.png"
    rotated.save(path)
    return path


def make_multipage_pdf() -> Path:
    page1 = Image.new("RGB", (850, 1100), "white")
    ImageDraw.Draw(page1).text((60, 60), "Page 1 of the sample multi-page document.", fill="black", font=_font(24))
    page2 = Image.new("RGB", (850, 1100), "white")
    ImageDraw.Draw(page2).text((60, 60), "Page 2 -- ImageOCR Pro supports multi-page PDFs.", fill="black", font=_font(24))
    path = OUTPUT_DIR / "sample_multipage.pdf"
    page1.save(path, save_all=True, append_images=[page2])
    return path


if __name__ == "__main__":
    for builder in (make_invoice, make_letter, make_business_card, make_skewed_receipt, make_multipage_pdf):
        output = builder()
        print(f"Generated {output}")
