---
name: pdf-splitter
description: Split large PDF files into smaller PDFs with qpdf while preserving file structure and avoiding the size blow-up common with PDFKit rewrites. Use when Codex needs to split a PDF into two halves, split by a specific page, split by custom page ranges, or first install qpdf with Homebrew if it is missing on the machine.
---

# PDF Splitter

## Overview

Split PDFs with `qpdf`, not `PDFKit`, unless there is a specific reason to do otherwise. `qpdf` usually preserves the original PDF structure better and avoids inflated output sizes after splitting.

## Workflow

1. Confirm the input PDF path exists.
2. Check whether `qpdf` is installed with `command -v qpdf`.
3. If `qpdf` is missing:
   - Check `command -v brew`.
   - If Homebrew exists, install `qpdf` with `brew install qpdf`.
   - If the environment requires approval for package installation, request approval before installing.
   - If Homebrew is unavailable, stop and report that `qpdf` must be installed before continuing.
4. Run `scripts/split_pdf.py`.
5. Verify outputs with `qpdf --show-npages` and, when useful, `qpdf --check`.

## Commands

Split into two equal parts:

```bash
python3 scripts/split_pdf.py "/abs/path/file.pdf"
```

Split at a specific page:

```bash
python3 scripts/split_pdf.py "/abs/path/file.pdf" --split-page 845
```

Split by explicit ranges:

```bash
python3 scripts/split_pdf.py "/abs/path/file.pdf" --ranges "1-300,301-600,601-z"
```

Write outputs to a different directory:

```bash
python3 scripts/split_pdf.py "/abs/path/file.pdf" --output-dir "/abs/path/out"
```

## Notes

- Prefer the script over ad hoc shell because it calculates ranges and names outputs consistently.
- Default output names follow the pattern `Original Name - PART N.pdf`.
- Use `--prefix` when the user wants a different output stem.
- Use `--overwrite` only when replacing existing split files intentionally.
- If the user asks for a custom number of equal parts, use `--parts N`.
