# ImageOCR Pro — Developer Guide

## Design principles

- **Clean layering.** `app/ui` never imports OpenCV, PyMuPDF, or sqlite3
  directly — it calls into `app/core`, `app/database`, and `app/exports`,
  which are fully independent of Qt and are exercised by the pytest suite
  without a display server.
- **Everything offline.** No module makes a network call. The only
  "external" I/O is the local filesystem, the local SQLite file, and
  (optionally) the local Tesseract binary / EasyOCR-PaddleOCR model
  weights cached on first use.
- **Fail soft, log loud.** A single bad file in a batch, an unplaceable
  OCR word in a searchable-PDF export, or a missing optional dependency
  should never crash the app — see the `except Exception` boundaries in
  `batch_manager.py`, `pdf_utils.create_searchable_pdf`, and the engine
  `is_available()` checks, all of which log via `app/utils/logger.py`.

## Module map

| Package | Responsibility |
|---|---|
| `app/config` | `constants.py` (formats/engines/languages), `settings.py` (encrypted JSON settings, `SettingsManager` singleton via `get_settings()`) |
| `app/core` | `models.py` (dataclasses shared everywhere: `OCRWord`, `OCRPage`, `OCRDocument`, `HistoryRecord`, `BatchItem`), `document_processor.py` (the single pipeline entry point), `batch_manager.py` (QThread-based queue), `text_postprocessor.py` (language detection, paragraph grouping, spellcheck) |
| `app/ocr` | `base_engine.py` (the `OCREngine` ABC every backend implements), `engine_manager.py` (registry + fallback resolution), `engines/{tesseract,easyocr,paddleocr}_engine.py` |
| `app/utils` | `image_preprocessing.py` (OpenCV pipeline), `pdf_utils.py` (PyMuPDF: rasterize, merge/split/rotate/reorder/delete pages, searchable-PDF text-layer generation), `file_utils.py`, `logger.py` |
| `app/database` | `db_manager.py` — SQLite history store with WAL mode, `REGEXP` search support, and aggregate statistics |
| `app/exports` | `exporter.py` (format dispatch), `formats/*.py` (one function per format: `export(document, path) -> Path`) |
| `app/ui` | `main_window.py` (nav/routing/theme/menu), `pages/*.py` (Home, Workspace, Batch, History, Settings), `widgets/*.py` (`ImageViewer`, `DropArea`, `ThumbnailList`) |

## The OCR pipeline, end to end

```
DocumentProcessor.process(path, engine_name, language, mode, ...)
  1. DocumentProcessor.load_pages(path)
       -> pdf_utils.pdf_to_images()   (PDF)
       -> cv2.imread()                (image)
  2. PreprocessingOptions.for_mode(mode) [+ any per-call overrides]
  3. For each page:
       ImagePreprocessor.preprocess_pipeline(image, options) -> PreprocessingResult
       engine.recognize(preprocessed_image, language, ...) -> OCRPage
  4. text_postprocessor.detect_language() if language == "auto"
  5. Returns an OCRDocument aggregating all OCRPages
```

The Workspace page and the Batch queue both call this exact function —
`OCRRunThread` in `workspace_page.py` and `BatchWorker` in
`batch_manager.py` are thin `QThread` wrappers so the same logic runs
identically single-file or in bulk, just off the UI thread.

## Adding a new OCR engine

1. Create `app/ocr/engines/my_engine.py` subclassing `OCREngine`
   (`app/ocr/base_engine.py`). Implement `is_available()`,
   `supported_languages()`, and `recognize()` returning an `OCRPage`.
   Guard the heavy import in a `try/except ImportError` at module level,
   exactly like `easyocr_engine.py`, so the app still runs without it.
2. Register it in `OCREngineManager.__init__` (`app/ocr/engine_manager.py`).
3. It automatically appears in the Workspace/Batch engine dropdowns —
   nothing else changes.

## Adding a new export format

1. Add the enum value to `ExportFormat` in `app/core/models.py`.
2. Create `app/exports/formats/my_format_exporter.py` exposing
   `export(document: OCRDocument, path) -> Path`.
3. Register the extension in `_EXTENSION_BY_FORMAT` and the handler in the
   `dispatch` dict inside `app/exports/exporter.py`.
4. It automatically appears in the Export Center dropdowns.

## Adding a new preprocessing stage

Add a `@staticmethod` to `ImagePreprocessor` (`app/utils/image_preprocessing.py`),
a corresponding boolean field to `PreprocessingOptions`, and wire it into
`preprocess_pipeline()` and, if it should be on by default for certain
modes, into `PreprocessingOptions.for_mode()`.

## Testing

```bash
pytest              # full suite, 54 tests
pytest -k pdf        # just PDF utilities
pytest -k exporters   # just export format tests
```

Tests that require the Tesseract binary are marked
`@pytest.mark.skipif(not TESSERACT_AVAILABLE, ...)` so the suite still
passes (skipping OCR-dependent assertions) in an environment without
Tesseract installed — everything else (preprocessing, PDF ops, DB, most
exporters) has no such dependency.

UI code (`app/ui/**`) is intentionally *not* unit tested with pytest —
verify it interactively with `python -m app.main`, or smoke-test
construction under Qt's offscreen platform plugin:

```bash
QT_QPA_PLATFORM=offscreen python -c "
from PySide6.QtWidgets import QApplication
app = QApplication([])
from app.ui.main_window import MainWindow
MainWindow()
print('OK')
"
```

## Building an executable

`build/build_windows.spec` is a PyInstaller spec (onedir build). EasyOCR
and PaddleOCR are excluded by default (`excludes=[...]` in the spec) to
keep the bundle small; remove them from `excludes` if you want a
GPU-engine-inclusive build, and be prepared for a multi-GB output.

```bash
pip install pyinstaller
python build/build.py
```

## Code style

PEP 8, type hints on public functions, one Google/NumPy-style docstring
per module/class explaining *why* rather than restating the signature.
Prefer dataclasses (`app/core/models.py`) over dicts for anything crossing
a module boundary.
