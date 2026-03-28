#!/usr/bin/env python3
"""Parse a PDF using Docling and output markdown with extracted figures.

Usage:
    python3 scripts/parse-pdf.py <pdf_path> [--output-dir <dir>] [--force]

Output:
    <pdf_stem>.md        — Markdown with referenced images
    <pdf_stem>_figures/  — Extracted figures and images

If the PDF is a symlink (e.g., to the shared PDF cache), output goes next to
the REAL file so parsing happens once per PDF. The caller (pipeline stages,
pdf-cache.sh link) is responsible for symlinking the outputs into the project.

Exit codes:
    0 — success (prints markdown path to stdout)
    1 — error
    2 — skipped (markdown already exists and is newer than PDF)
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Parse PDF to markdown with Docling")
    parser.add_argument("pdf_path", type=Path, help="Path to the PDF file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: same directory as the resolved PDF)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-parse even if markdown already exists",
    )
    args = parser.parse_args()

    pdf_path = Path.cwd() / args.pdf_path if not args.pdf_path.is_absolute() else args.pdf_path
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    if not pdf_path.suffix.lower() == ".pdf":
        print(f"Error: Not a PDF file: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Resolve symlinks — output goes next to the real PDF so parsing happens
    # once per PDF across all projects sharing the cache.
    real_pdf_path = pdf_path.resolve()
    output_dir = (args.output_dir or real_pdf_path.parent).resolve()
    stem = real_pdf_path.stem
    md_path = output_dir / f"{stem}.md"
    figures_dir = output_dir / f"{stem}_figures"

    # Skip if already parsed and up to date
    if not args.force and md_path.exists():
        if md_path.stat().st_mtime >= real_pdf_path.stat().st_mtime:
            print(md_path)
            sys.exit(2)

    # Import docling here so --help works without it installed
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        print(
            "Error: docling not installed. Run: pip install docling",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from docling_core.types.doc.base import ImageRefMode
    except ImportError:
        print(
            "Error: docling-core not installed. Run: pip install docling",
            file=sys.stderr,
        )
        sys.exit(1)

    # Convert
    try:
        converter = DocumentConverter()
        result = converter.convert(str(real_pdf_path))
        doc = result.document
    except Exception as e:
        print(f"Error converting {pdf_path.name}: {e}", file=sys.stderr)
        sys.exit(1)

    # Save markdown with referenced images
    try:
        figures_dir.mkdir(parents=True, exist_ok=True)
        doc.save_as_markdown(
            str(md_path),
            image_mode=ImageRefMode.REFERENCED,
            artifacts_dir=figures_dir,
        )
    except Exception as e:
        print(f"Error saving output: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean up empty figures dir if no images were extracted
    if figures_dir.exists() and not any(figures_dir.iterdir()):
        figures_dir.rmdir()

    print(md_path)


if __name__ == "__main__":
    main()
