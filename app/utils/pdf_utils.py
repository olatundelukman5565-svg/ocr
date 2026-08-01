"""PDF processing built on PyMuPDF (fitz): rasterization, page ops, and
generation of searchable (text-under-image) PDFs from OCR results.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def pdf_to_images(path: str | Path, dpi: int = 300) -> list[np.ndarray]:
    """Rasterize every page of a PDF to a BGR numpy image (OpenCV-ready)."""
    images: list[np.ndarray] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(str(path)) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 3:
                img = img[:, :, ::-1]  # RGB -> BGR
            images.append(np.ascontiguousarray(img))
    return images


def get_page_count(path: str | Path) -> int:
    with fitz.open(str(path)) as doc:
        return doc.page_count


def create_searchable_pdf(
    page_images: Sequence[np.ndarray],
    page_ocr_words: Sequence[Sequence[object]],
    output_path: str | Path,
    dpi: int = 300,
) -> Path:
    """Build a PDF where each page is the (optionally enhanced) source image
    with an invisible OCR text layer positioned over each recognized word,
    so the resulting document is fully text-searchable while looking
    identical to the scan.

    ``page_ocr_words`` items must expose ``.text`` and ``.bbox`` (x, y,
    width, height in pixel space of the corresponding page image) --
    typically :class:`app.core.models.OCRWord` instances.
    """
    output_path = Path(output_path)
    doc = fitz.open()
    zoom = 72.0 / dpi
    for image, words in zip(page_images, page_ocr_words):
        height, width = image.shape[:2]
        pdf_width, pdf_height = width * zoom, height * zoom
        page = doc.new_page(width=pdf_width, height=pdf_height)

        rgb_image = image[:, :, ::-1] if image.ndim == 3 else image
        pil_image = Image.fromarray(rgb_image)
        img_bytes = _pil_to_png_bytes(pil_image)
        page.insert_image(fitz.Rect(0, 0, pdf_width, pdf_height), stream=img_bytes)

        for word in words:
            text = getattr(word, "text", "")
            if not text.strip():
                continue
            x, y, w, h = word.bbox
            rect = fitz.Rect(x * zoom, y * zoom, (x + w) * zoom, (y + h) * zoom)
            font_size = max(rect.height * 0.9, 1)
            # insert_text (unlike insert_textbox) places from a baseline point
            # rather than fitting inside a box, so it never silently drops
            # text that doesn't fit a tight single-line rect.
            baseline = fitz.Point(rect.x0, rect.y1)
            try:
                text_width = fitz.get_text_length(text, fontname="helv", fontsize=font_size)
                if text_width > 0 and rect.width > 0:
                    font_size *= min(rect.width / text_width, 1.5)
                page.insert_text(baseline, text, fontsize=font_size, render_mode=3)
            except Exception:  # noqa: BLE001 - a single bad word must not abort the export
                logger.debug("Skipping unplaceable OCR word during searchable PDF export", exc_info=True)

    doc.save(str(output_path))
    doc.close()
    return output_path


def _pil_to_png_bytes(image: Image.Image) -> bytes:
    from io import BytesIO

    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def merge_pdfs(paths: Sequence[str | Path], output_path: str | Path) -> Path:
    merged = fitz.open()
    for path in paths:
        with fitz.open(str(path)) as doc:
            merged.insert_pdf(doc)
    merged.save(str(output_path))
    merged.close()
    return Path(output_path)


def split_pdf(path: str | Path, output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    with fitz.open(str(path)) as doc:
        base_name = Path(path).stem
        for i in range(doc.page_count):
            single = fitz.open()
            single.insert_pdf(doc, from_page=i, to_page=i)
            out_path = output_dir / f"{base_name}_page{i + 1:03d}.pdf"
            single.save(str(out_path))
            single.close()
            outputs.append(out_path)
    return outputs


def rotate_page(path: str | Path, page_number: int, angle: int, output_path: str | Path | None = None) -> Path:
    """Rotate a single page (0-indexed) by a multiple of 90 degrees, writing to a new file."""
    out = Path(output_path) if output_path else Path(path).with_suffix(".rotated.pdf")
    with fitz.open(str(path)) as doc:
        page = doc[page_number]
        page.set_rotation((page.rotation + angle) % 360)
        doc.save(str(out))
    return out


def delete_pages(path: str | Path, page_numbers: Sequence[int], output_path: str | Path) -> Path:
    with fitz.open(str(path)) as doc:
        doc.delete_pages(list(page_numbers))
        doc.save(str(output_path))
    return Path(output_path)


def reorder_pages(path: str | Path, new_order: Sequence[int], output_path: str | Path) -> Path:
    """``new_order`` is a 0-indexed permutation of the original page indices."""
    with fitz.open(str(path)) as doc:
        doc.select(list(new_order))
        doc.save(str(output_path))
    return Path(output_path)


def extract_images_from_pdf(path: str | Path, output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with fitz.open(str(path)) as doc:
        for page_index in range(doc.page_count):
            for image_index, img in enumerate(doc.get_page_images(page_index), start=1):
                xref = img[0]
                base = doc.extract_image(xref)
                ext = base["ext"]
                out_path = output_dir / f"page{page_index + 1:03d}_img{image_index}.{ext}"
                out_path.write_bytes(base["image"])
                extracted.append(out_path)
    return extracted


def remove_blank_pages(path: str | Path, output_path: str | Path, ink_threshold: float = 0.002) -> Path:
    """Drop pages whose rendered pixel coverage is below ``ink_threshold`` (near-blank)."""
    keep: list[int] = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            gray = arr.mean(axis=2) if pix.n >= 3 else arr[:, :, 0]
            ink_ratio = float((gray < 250).mean())
            if ink_ratio >= ink_threshold:
                keep.append(i)
        if not keep:
            keep = list(range(doc.page_count))
        doc.select(keep)
        doc.save(str(output_path))
    return Path(output_path)
