"""Self-contained HTML export, with per-page sections and basic styling."""
from __future__ import annotations

from html import escape
from pathlib import Path

from app.core.models import OCRDocument

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  h2 {{ font-size: 1.1rem; color: #555; margin-top: 2rem; border-bottom: 1px solid #ddd; padding-bottom: .25rem; }}
  p {{ line-height: 1.6; white-space: pre-wrap; }}
  .meta {{ color: #888; font-size: .85rem; margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">Engine: {engine} &middot; Language: {language} &middot; Confidence: {confidence:.1f}%</div>
{body}
</body>
</html>
"""


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    title = escape(Path(document.source_path).name)
    body_parts = []
    for page in document.pages:
        if document.page_count > 1:
            body_parts.append(f"<h2>Page {page.page_number}</h2>")
        for paragraph in page.text.split("\n\n"):
            if paragraph.strip():
                body_parts.append(f"<p>{escape(paragraph.strip())}</p>")
    html = _TEMPLATE.format(
        title=title,
        engine=escape(document.engine),
        language=escape(document.language),
        confidence=document.mean_confidence,
        body="\n".join(body_parts),
    )
    path.write_text(html, encoding="utf-8")
    return path
