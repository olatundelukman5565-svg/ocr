# ImageOCR Pro — User Manual

## 1. Installation

See the root [`README.md`](../README.md) for system requirements
(Tesseract binary) and `pip install -r requirements.txt`. Launch with:

```bash
python -m app.main
```

## 2. The Home dashboard

The landing page shows:
- **Quick actions** — jump straight to a new OCR job, Batch Processing, History, or Settings
- **Drop zone** — drag images/PDFs here (or click to browse) to open them directly in the Workspace
- **Statistics** — total files processed, average confidence, total pages OCR'd, average time per file
- **Recent files** — double-click to reopen in the Workspace

## 3. OCR Workspace

1. **Load a file**: drag & drop onto the panel on the left, or use *File → Open File…* (`Ctrl+O`) / *Open Folder…* (`Ctrl+Shift+O`).
2. Multi-page PDFs populate the **thumbnail list** on the left — click a thumbnail to preview that page.
3. Use the toolbar above the image preview to **zoom in/out, fit-to-view, rotate 90° left/right**, and toggle **Region Select** to draw a rubber-band box (for Region OCR / cropping context).
4. Configure **OCR Settings** on the right:
   - **Engine**: Tesseract / EasyOCR / PaddleOCR (unavailable engines are labeled and are skipped automatically if selected)
   - **Language**: Auto-detect or one of the 16 supported languages
   - **Mode**: Fast, Balanced, High Accuracy, AI Enhanced, Batch, Region, Table, Handwriting — each maps to a different OpenCV preprocessing preset (see Developer Guide)
   - **Confidence threshold**: recognized words below this score are filtered out
   - **Use GPU**: only applies to EasyOCR/PaddleOCR
5. Click **Run OCR** (`Ctrl+R`). Progress is shown per page.
6. The extracted text appears in the **editable** results panel on the right:
   - **Find / Replace All** — simple text find and replace-all
   - **Check Spelling** — flags likely misspelled words (best-effort, dictionary-dependent)
   - Edits you make here are included in the exported output
7. **Export** — pick a format (TXT, DOCX, PDF, Searchable PDF, CSV, XLSX, JSON, HTML, Markdown, RTF) and click **Export**, or **Copy to Clipboard**. Every OCR run and export is logged to History (toggle in Settings → Autosave).

### Searchable PDF

"Searchable PDF" reproduces the original page images exactly, with an
invisible OCR text layer positioned over every recognized word — so the
output looks identical to the scan but is fully selectable/searchable in
any PDF reader.

## 4. Batch Processing

1. Drag & drop many files, or **Add Folder** to recursively import every
   supported file in a directory tree.
2. Choose engine / language / mode / export format for the whole batch.
3. **Start** — the queue table shows per-file status, progress, confidence
   and timing live. **Pause/Resume** and **Cancel** work mid-run.
4. The overall progress bar shows completed/total and a live **ETA**
   based on the rolling average time-per-file.
5. Each completed file is auto-exported to your default export folder
   (Settings) and logged to History.

## 5. History

Every OCR run (from the Workspace or Batch) is recorded with date, file,
engine, language, confidence, processing time and output path.

- **Search** the extracted text or file name; toggle **Regex**, **Case
  sensitive**, **Whole word**.
- Filter by **engine**.
- **Double-click** a row to open its exported output in your OS's default
  viewer.
- **Delete Selected** removes chosen entries from history (does not touch
  the exported files on disk).

## 6. Settings

- **Theme**: Dark / Light (also toggleable from the sidebar button)
- **Default OCR engine / language**
- **GPU**: use GPU when available (EasyOCR/PaddleOCR)
- **CPU threads**
- **Default export folder**
- **Autosave**: automatically log every OCR run to History
- **Keyboard shortcuts** reference (read-only)

## 7. Keyboard shortcuts

| Action | Shortcut |
|---|---|
| Open file | `Ctrl+O` |
| Open folder | `Ctrl+Shift+O` |
| Run OCR | `Ctrl+R` |
| Export | `Ctrl+E` |
| Find | `Ctrl+F` |
| Save (settings) | `Ctrl+S` |

## 8. Troubleshooting

- **"No OCR engine is available"** — install the Tesseract binary
  (`apt install tesseract-ocr` / `brew install tesseract` / the Windows
  installer) or `pip install easyocr` / `pip install paddleocr paddlepaddle`.
- **Low accuracy on a photographed (not scanned) document** — try **High
  Accuracy** or **AI Enhanced** mode, which enable deskew, perspective
  correction, shadow removal and adaptive thresholding.
- **Non-Latin script not detected correctly** — pick the language
  explicitly instead of Auto-detect; auto-detection runs on the OCR
  *output* text, so it can only help once recognition has already found
  some correct characters.
- Logs are written to `app/logs/imageocr_pro.log` (rotated at 5 MB, 5
  backups kept) — check there first for any error.
