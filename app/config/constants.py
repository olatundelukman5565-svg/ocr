"""Application-wide constants: metadata, supported formats, engines, languages."""

APP_NAME = "ImageOCR Pro"
APP_VERSION = "1.0.0"
ORG_NAME = "ImageOCR"

# --------------------------------------------------------------------------
# File format support
# --------------------------------------------------------------------------
SUPPORTED_IMAGE_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp",
)
SUPPORTED_PDF_EXTENSIONS = (".pdf",)
SUPPORTED_INPUT_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS + SUPPORTED_PDF_EXTENSIONS

EXPORT_FORMATS = (
    "TXT", "DOCX", "PDF", "SEARCHABLE_PDF", "CSV", "XLSX", "JSON", "HTML", "MARKDOWN", "RTF",
)

# --------------------------------------------------------------------------
# OCR engines
# --------------------------------------------------------------------------
OCR_ENGINES = ("tesseract", "easyocr", "paddleocr")

# --------------------------------------------------------------------------
# OCR modes -> preprocessing/engine behaviour presets
# --------------------------------------------------------------------------
OCR_MODES = (
    "fast",
    "balanced",
    "high_accuracy",
    "ai_enhanced",
    "batch",
    "region",
    "table",
    "handwriting",
)

# --------------------------------------------------------------------------
# Supported languages: display name -> ISO-639 style code understood by
# each engine's language mapping (see engines/*_engine.py for translation
# to the engine-specific code such as tesseract's 3-letter codes).
# --------------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "English": "en",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Chinese (Simplified)": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
    "Turkish": "tr",
    "Russian": "ru",
    "Thai": "th",
    "Vietnamese": "vi",
}

AUTO_DETECT_LANGUAGE = "auto"

DEFAULT_CONFIG_DIR_NAME = ".imageocr_pro"
DEFAULT_SETTINGS_FILENAME = "settings.enc"
DEFAULT_KEY_FILENAME = ".key"
DEFAULT_DATABASE_FILENAME = "history.db"
DEFAULT_LOG_FILENAME = "imageocr_pro.log"
