# ImageOCR Pro

A modular, fully offline OCR desktop application built with **PySide6**,
**OpenCV**, and pluggable **Tesseract / EasyOCR / PaddleOCR** engines. It
extracts text from images (JPG, PNG, BMP, TIFF, WEBP) and scanned PDFs
(single or multi-page), with an OpenCV preprocessing pipeline (deskew,
denoise, CLAHE contrast, adaptive threshold, perspective correction,
shadow removal), a batch queue with pause/resume/cancel, an OCR history
database, and export to TXT/DOCX/PDF/Searchable PDF/CSV/XLSX/JSON/
HTML/Markdown/RTF — all processing happens locally, nothing is uploaded.

## Status

This is a complete, working implementation of the core architecture and
feature set below — every module has passing unit tests and has been
exercised end-to-end against the sample documents in `sample_images/`.
Two things to be upfront about before you treat it as "ABBYY FineReader in
a box":

- **Table/form/handwriting-specific recognition and QR/barcode detection**
  are exposed as selectable OCR modes/hooks but rely on the underlying
  engine's general-purpose accuracy rather than dedicated table/form
  models — there's no bespoke table-structure-recognition network here.
- **EasyOCR and PaddleOCR** are wired up as first-class, switchable engines
  but are large ML dependencies (`pip install easyocr` /
  `pip install paddleocr paddlepaddle`) that aren't installed by default;
  Tesseract is the zero-friction default. The engine manager detects
  what's installed and falls back gracefully.

## Features

- **Multi-format input**: JPG, JPEG, PNG, BMP, TIFF, WEBP, single & multi-page PDF
- **3 switchable OCR engines**: Tesseract (default, CPU), EasyOCR (CPU/GPU), PaddleOCR (CPU/GPU)
- **16 languages** with auto-detection (English, French, German, Spanish, Italian,
  Portuguese, Dutch, Chinese, Japanese, Korean, Arabic, Hindi, Turkish, Russian, Thai, Vietnamese)
- **OpenCV preprocessing pipeline**: grayscale, denoise, deskew, perspective
  correction, CLAHE contrast, sharpen, adaptive threshold, shadow removal, upscaling
- **4 OCR mode presets** (Fast / Balanced / High Accuracy / AI Enhanced) plus
  Batch, Region, Table and Handwriting mode selectors
- **Modern PySide6 UI**: dark/light theme, sidebar navigation, drag & drop,
  zoom/rotate/region-select image viewer, editable results with find &
  replace and spell check
- **Batch processing**: queue hundreds of files, pause/resume/cancel, live ETA
- **Export Center**: TXT, DOCX, PDF, Searchable PDF (invisible OCR text
  layer over the original scan), CSV, XLSX, JSON, HTML, Markdown, RTF
- **OCR History**: SQLite-backed, with regex/case-sensitive/whole-word search
- **PDF tooling**: merge, split, rotate, delete/reorder pages, extract
  embedded images, drop blank pages
- **Settings**: encrypted local settings file, GPU/CPU toggle, default
  export folder, autosave, hotkeys
- **Fully offline**: no network calls, no cloud upload, anywhere in the pipeline

## Architecture

```
ImageOCR/
├── app/
│   ├── core/            # DocumentProcessor, BatchManager, data models, text postprocessing
│   ├── ocr/              # OCREngine ABC + engine_manager + engines/{tesseract,easyocr,paddleocr}
│   ├── ui/                # main_window, pages/{home,workspace,batch,history,settings}, widgets/
│   ├── utils/             # image_preprocessing (OpenCV), pdf_utils (PyMuPDF), file_utils, logger
│   ├── database/          # SQLite history store (db_manager.py)
│   ├── exports/           # exporter.py dispatcher + formats/{txt,docx,pdf,csv,xlsx,json,html,md,rtf}
│   ├── config/            # constants.py, settings.py (encrypted JSON settings)
│   ├── resources/         # icons / stylesheets (icons currently come from Qt's built-in set)
│   └── logs/               # rotating log files written at runtime
├── tests/                  # pytest suite (54 tests) covering every non-UI module
├── sample_images/           # synthetic sample docs + generate_samples.py
├── build/                    # PyInstaller spec + build helper script
├── docs/                      # user manual & developer guide
└── requirements.txt
```

Each layer only depends on the ones below it — the UI never touches OpenCV
or SQLite directly, it goes through `DocumentProcessor` / `DBManager` /
`export_document()`. That's what lets you swap the OCR engine, add a new
export format, or replace the UI toolkit without cascading changes.

## Installation

### 1. System dependencies

```bash
# Tesseract OCR engine (required for the default engine)
sudo apt install tesseract-ocr          # Debian/Ubuntu
brew install tesseract                  # macOS
# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# Optional: extra Tesseract language packs, e.g.
sudo apt install tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-chi-sim
```

### 2. Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional GPU-capable engines (large downloads):
pip install easyocr
pip install paddleocr paddlepaddle
```

### 3. Run

```bash
python -m app.main
```

## Testing

```bash
pytest
```

54 tests cover image preprocessing, PDF utilities, the OCR engine
registry/fallback logic, the document processing pipeline (run against the
generated sample documents), every export format including searchable-PDF
text-layer extraction, the SQLite history store, settings persistence, and
text postprocessing.

## Building a standalone executable

```bash
pip install pyinstaller
python build/build.py
```

Produces a onedir build under `dist/ImageOCR_Pro/`. See `build/build_windows.spec`
to bundle the optional EasyOCR/PaddleOCR engines (excluded by default to
keep the build small).

## Documentation

- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) — using the application
- [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) — architecture, extending engines/exporters, contributing

## Sample data

`sample_images/` contains a synthetic invoice, letter, business card,
skewed receipt, and a 2-page PDF — all generated by
`sample_images/generate_samples.py` (no copyrighted scans are included).

## License

Provided as-is for evaluation and further development.
