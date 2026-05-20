#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def require_qpdf() -> str:
    qpdf = shutil.which("qpdf")
    if not qpdf:
        fail("qpdf not found. Install it first with Homebrew: brew install qpdf")
    return qpdf


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        stdout = exc.stdout.strip() if exc.stdout else ""
        details = stderr or stdout or "command failed"
        fail(f"{details}\nCommand: {' '.join(cmd)}")
    return result.stdout.strip()


def get_total_pages(qpdf: str, input_pdf: Path) -> int:
    output = run([qpdf, "--show-npages", str(input_pdf)])
    try:
        return int(output)
    except ValueError as exc:
        raise SystemExit(f"Unable to parse qpdf page count: {output}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a PDF with qpdf.")
    parser.add_argument("input_pdf", help="Path to the source PDF")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--split-page",
        type=int,
        help="Split into two files: 1-N and N+1-end",
    )
    group.add_argument(
        "--ranges",
        help='Comma-separated qpdf ranges, e.g. "1-300,301-600,601-z"',
    )
    group.add_argument(
        "--parts",
        type=int,
        default=2,
        help="Split into N equal contiguous parts when no explicit range is given",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for output files. Defaults to the input file directory.",
    )
    parser.add_argument(
        "--prefix",
        help='Output filename prefix. Defaults to the input stem, e.g. "My PDF"',
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
    )
    return parser.parse_args()


def compute_equal_ranges(total_pages: int, parts: int) -> list[str]:
    if parts < 2:
        fail("--parts must be at least 2")
    if parts > total_pages:
        fail("--parts cannot exceed the total number of pages")

    base = total_pages // parts
    remainder = total_pages % parts
    ranges = []
    start = 1
    for index in range(parts):
        size = base + (1 if index < remainder else 0)
        end = start + size - 1
        ranges.append(f"{start}-{end}")
        start = end + 1
    return ranges


def normalize_ranges(total_pages: int, split_page: int | None, ranges: str | None, parts: int) -> list[str]:
    if split_page is not None:
        if split_page < 1 or split_page >= total_pages:
            fail("--split-page must be between 1 and the penultimate page")
        return [f"1-{split_page}", f"{split_page + 1}-{total_pages}"]
    if ranges:
        items = [item.strip() for item in ranges.split(",") if item.strip()]
        if len(items) < 2:
            fail("--ranges must contain at least two ranges")
        return items
    return compute_equal_ranges(total_pages, parts)


def output_paths(input_pdf: Path, output_dir: Path, prefix: str, count: int) -> list[Path]:
    return [output_dir / f"{prefix} - PART {index}.pdf" for index in range(1, count + 1)]


def main() -> None:
    args = parse_args()
    input_pdf = Path(args.input_pdf).expanduser().resolve()
    if not input_pdf.exists():
        fail(f"Input PDF not found: {input_pdf}")
    if not input_pdf.is_file():
        fail(f"Input path is not a file: {input_pdf}")

    qpdf = require_qpdf()
    total_pages = get_total_pages(qpdf, input_pdf)
    ranges = normalize_ranges(total_pages, args.split_page, args.ranges, args.parts)

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else input_pdf.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or input_pdf.stem
    outputs = output_paths(input_pdf, output_dir, prefix, len(ranges))

    for output in outputs:
        if output.exists() and not args.overwrite:
            fail(f"Output already exists: {output}. Re-run with --overwrite to replace it.")

    for page_range, output in zip(ranges, outputs):
        run([qpdf, "--empty", "--pages", str(input_pdf), page_range, "--", str(output)])

    print(f"Input: {input_pdf}")
    print(f"Total pages: {total_pages}")
    for page_range, output in zip(ranges, outputs):
        pages = run([qpdf, "--show-npages", str(output)])
        print(f"{output}: range={page_range}, pages={pages}")


if __name__ == "__main__":
    main()
