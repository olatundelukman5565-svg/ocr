# ImageOCR Pro — Windows Quick Start (no technical experience needed)

## Step 1 — Install two programs (one-time only)

1. **Python**: go to https://www.python.org/downloads/ , click the big yellow
   "Download Python" button, run the installer. **On the first install
   screen, make sure to tick the checkbox that says "Add python.exe to
   PATH"** before clicking Install.
2. **Tesseract OCR**: go to https://github.com/UB-Mannheim/tesseract/wiki ,
   download the Windows installer link near the top, run it, and just click
   Next/Install through the default options.

## Step 2 — Unzip the app

Right-click the downloaded `ImageOCR_Pro_source.zip` file → **Extract All…**
→ pick a folder you'll remember (e.g. your Desktop) → Extract.

## Step 3 — Run setup (one-time only)

Open the extracted folder and **double-click `setup_windows.bat`**.

A black window will open and install everything the app needs — this can
take a few minutes the first time. When it says "Setup complete!", you're
done with this step.

## Step 4 — Start the app

**Double-click `run_windows.bat`** any time you want to open ImageOCR Pro.

## Try it

Once the app window opens, drag one of the files from the `sample_images`
folder (e.g. `sample_invoice.png`) onto the app, then click **Run OCR** to
see it extract the text.

## If something goes wrong

- A black window that closes immediately or shows red text usually means
  Step 1 wasn't completed — double check Python and Tesseract are both
  installed (reopen the installers if unsure).
- If `setup_windows.bat` says Python or Tesseract wasn't found right after
  you installed them, close and reopen the folder (or restart your
  computer) so Windows picks up the changes, then try again.
