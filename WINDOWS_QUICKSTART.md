# ImageOCR Pro — Windows Quick Start (no technical experience needed)

## Step 1 — Unzip the app

Right-click the downloaded `ImageOCR_Pro_source.zip` file → **Extract All…**
→ pick a folder you'll remember (e.g. your Desktop) → Extract.

## Step 2 — Install Python and Tesseract (one-time, if not already installed)

If you haven't already: install these two, using their default options:
- **Python**: https://www.python.org/downloads/ — tick **"Add python.exe to PATH"** during install
- **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki

If both are already installed on your computer, skip this step.

## Step 3 — Run setup

Open the extracted folder and **double-click `setup_windows.bat`**.

It checks for Python and Tesseract, then installs the app's own
requirements — this can take a few minutes. When you see "Setup
complete!", you're done.

## Step 4 — Start the app

**Double-click `run_windows.bat`** any time you want to open ImageOCR Pro.

## Try it

Once the app window opens, drag one of the files from the `sample_images`
folder (e.g. `sample_invoice.png`) onto the app, then click **Run OCR** to
see it extract the text.

## If something goes wrong

- **If the window flashes and disappears before you can read it**,
  double-click **`debug_setup.bat`** instead. It runs the same setup but
  saves everything to a file and opens it in Notepad automatically at the
  end — copy everything from that Notepad window (Ctrl+A, then Ctrl+C)
  and send it back.
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
- **"No such file or directory: 'requirements.txt'"** or **"'setup_windows.bat' is not recognized"** —
  make sure you properly extracted the whole zip (not just opened/ran a
  file from inside the zip viewer) into a real folder, and that you're
  using the latest download (delete any old extracted copies first).
