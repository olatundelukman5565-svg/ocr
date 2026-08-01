from __future__ import annotations

from app.utils import pdf_utils


def test_pdf_to_images_returns_one_image_per_page(sample_multipage_pdf_path):
    images = pdf_utils.pdf_to_images(sample_multipage_pdf_path, dpi=100)
    assert len(images) == 2
    assert images[0].ndim == 3


def test_get_page_count(sample_multipage_pdf_path):
    assert pdf_utils.get_page_count(sample_multipage_pdf_path) == 2


def test_merge_pdfs(tmp_path, sample_multipage_pdf_path):
    output = tmp_path / "merged.pdf"
    pdf_utils.merge_pdfs([sample_multipage_pdf_path, sample_multipage_pdf_path], output)
    assert pdf_utils.get_page_count(output) == 4


def test_split_pdf(tmp_path, sample_multipage_pdf_path):
    output_dir = tmp_path / "split"
    parts = pdf_utils.split_pdf(sample_multipage_pdf_path, output_dir)
    assert len(parts) == 2
    for part in parts:
        assert pdf_utils.get_page_count(part) == 1


def test_delete_pages(tmp_path, sample_multipage_pdf_path):
    output = tmp_path / "trimmed.pdf"
    pdf_utils.delete_pages(sample_multipage_pdf_path, [0], output)
    assert pdf_utils.get_page_count(output) == 1


def test_reorder_pages(tmp_path, sample_multipage_pdf_path):
    output = tmp_path / "reordered.pdf"
    pdf_utils.reorder_pages(sample_multipage_pdf_path, [1, 0], output)
    images = pdf_utils.pdf_to_images(output, dpi=72)
    assert len(images) == 2


def test_rotate_page(tmp_path, sample_multipage_pdf_path):
    output = tmp_path / "rotated.pdf"
    pdf_utils.rotate_page(sample_multipage_pdf_path, 0, 90, output_path=output)
    assert output.exists()
