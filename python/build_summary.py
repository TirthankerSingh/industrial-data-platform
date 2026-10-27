"""Build technical_summary.pdf (2-3 pages) from docs/report/technical_summary.md via headless Edge/Chrome.

    python python/build_summary.py
"""
from __future__ import annotations

from pathlib import Path

import markdown

from build_report import to_pdf_file

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "report" / "technical_summary.md"
OUT = ROOT / "technical_summary.pdf"

CSS = """
@page { size: A4; margin: 13mm 14mm 13mm 14mm; }
html { font-family: "Segoe UI", system-ui, sans-serif; font-size: 8.6pt; color: #0b0b0b; line-height: 1.35; }
h1 { font-size: 15pt; margin: 0 0 3px; color: #1c5cab; }
h2 { font-size: 10.5pt; margin: 9px 0 3px; color: #1c5cab; border-bottom: 1px solid #c3c2b7; padding-bottom: 1px;
     break-after: avoid; }
p { margin: 3px 0; }
ul { margin: 2px 0; padding-left: 16px; }
li { margin: 1px 0; }
.meta { color: #52514e; font-size: 8pt; margin-bottom: 6px; }
table { border-collapse: collapse; width: 100%; margin: 4px 0; font-size: 7.9pt; break-inside: avoid; }
th { background: #eef3fb; text-align: left; }
th, td { border: 1px solid #c3c2b7; padding: 2px 5px; vertical-align: top; }
code { font-size: 7.9pt; }
"""


def build() -> Path:
    body = markdown.markdown(SRC.read_text(encoding="utf-8"), extensions=["tables", "md_in_html", "sane_lists"])
    out = ROOT / "docs" / "report" / "build" / "technical_summary.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>Technical Summary</title>'
                   f'<style>{CSS}</style></head><body>{body}</body></html>', encoding="utf-8")
    return out


if __name__ == "__main__":
    to_pdf_file(build(), OUT)
