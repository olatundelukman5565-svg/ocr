# ImageOCR Pro — Windows Quick Start (no technical experience needed)

## Step 1 — Unzip the app

Right-click the downloaded `ImageOCR_Pro_source.zip` file → **Extract All…**
→ pick a folder you'll remember (e.g. your Desktop) → Extract.

## Step 2 — Run setup

Open the extracted folder and **double-click `setup_windows.bat`**.

- If Python and/or Tesseract OCR aren't already on your computer, the
  script installs them for you automatically. If either install needs
  administrator permission, a **Windows permission popup** appears right
  at that point — click **Yes**. The same black window keeps running
  throughout; nothing needs to be closed or reopened.
- Once both are present, it installs the app's own requirements — this
  can take a few minutes. When you see "Setup complete!", you're done.

(If your PC is older/managed and doesn't have `winget`, the script will
instead show you two manual download links — just install those and run
`setup_windows.bat` again.)

## Step 3 — Start the app

**Double-click `run_windows.bat`** any time you want to open ImageOCR Pro.

## Try it

Once the app window opens, drag one of the files from the `sample_images`
folder (e.g. `sample_invoice.png`) onto the app, then click **Run OCR** to
see it extract the text.

## If something goes wrong

- A black window that closes immediately or shows red text usually means
  setup didn't fully finish — just double-click `setup_windows.bat` again.
- Copy whatever the black window says and send it back — that message is
  enough to figure out what went wrong.
- **"Python was not found; run without arguments to install from the
  Microsoft Store…"** — this means Windows' built-in placeholder for
  Python (an "App execution alias") is blocking the real one. Fix:
  1. Open **Settings → Apps → Advanced app settings → App execution
     aliases**
  2. Turn **off** the switches next to `python.exe` and `python3.exe`
  3. Double-click `setup_windows.bat` again
- **"Access is denied."** during a Python/Tesseract install — a
  permission popup should have appeared right after; make sure to click
  **Yes** on it. If no popup appears at all and it just fails, your
  computer may be a work/managed one where your account isn't allowed to
  install software — your IT department would need to grant permission or
  install Python/Tesseract for you directly.
- **"No such file or directory: 'requirements.txt'"** — this was a bug in
  an earlier version of this script; make sure you're using the latest
  download (delete any old extracted copies first to avoid confusion).
