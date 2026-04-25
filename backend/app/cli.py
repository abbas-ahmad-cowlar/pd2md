"""
PD2MD CLI — Command-line interface for PDF to Markdown conversion.

Usage:
    pd2md convert input.pdf                     # Single file
    pd2md convert input.pdf -o output/          # Specify output dir
    pd2md batch folder/                         # Batch convert all PDFs
    pd2md batch folder/ -o results/             # Batch with output dir
    pd2md convert input.pdf --no-frontmatter    # Skip YAML frontmatter
    pd2md convert input.pdf --image-format jpeg # Use JPEG for images
    pd2md convert input.pdf --report            # Show quality report
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
import time
from pathlib import Path

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from backend.app.pipeline.orchestrator import PipelineOrchestrator, ConversionError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pd2md",
        description="PD2MD -- Intelligent PDF to Markdown Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pd2md convert report.pdf
  pd2md convert report.pdf -o ./output/ --image-format jpeg
  pd2md batch ./pdfs/ -o ./results/
  pd2md convert report.pdf --report --no-frontmatter
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Convert Command ---
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a single PDF file to Markdown",
    )
    convert_parser.add_argument(
        "input",
        type=Path,
        help="Path to the PDF file",
    )
    convert_parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory (default: ./output/<filename>/)",
    )
    convert_parser.add_argument(
        "--image-format",
        choices=["png", "jpeg"],
        default="png",
        help="Image format for extracted images (default: png)",
    )
    convert_parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="JPEG quality 1-100 (default: 85)",
    )
    convert_parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Skip YAML frontmatter in output",
    )
    convert_parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip content accuracy validation",
    )
    convert_parser.add_argument(
        "--report",
        action="store_true",
        help="Show detailed quality report after conversion",
    )
    convert_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    # --- Batch Command ---
    batch_parser = subparsers.add_parser(
        "batch",
        help="Batch convert all PDFs in a directory",
    )
    batch_parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing PDF files",
    )
    batch_parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory (default: ./output/)",
    )
    batch_parser.add_argument(
        "--image-format",
        choices=["png", "jpeg"],
        default="png",
        help="Image format for extracted images",
    )
    batch_parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Skip YAML frontmatter in output",
    )
    batch_parser.add_argument(
        "--report",
        action="store_true",
        help="Show quality report for each file",
    )
    batch_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    level = logging.DEBUG if getattr(args, "verbose", False) else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "convert":
        sys.exit(_cmd_convert(args))
    elif args.command == "batch":
        sys.exit(_cmd_batch(args))
    else:
        parser.print_help()
        sys.exit(1)


# --- Convert Single File ---

def _cmd_convert(args) -> int:
    """Convert a single PDF file."""
    input_path = args.input.resolve()

    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        return 1

    output_dir = (args.output or Path("output") / input_path.stem).resolve()

    print(f"[>] Converting: {input_path.name}")
    print(f"[>] Output:     {output_dir}")
    print()

    try:
        pipe = PipelineOrchestrator(
            pdf_path=input_path,
            output_dir=output_dir,
            image_format=args.image_format,
            jpeg_quality=args.jpeg_quality,
            include_frontmatter=not args.no_frontmatter,
            validate=not args.no_validate,
        )

        # Progress bar
        pipe.set_progress_callback(_progress_bar)

        result = pipe.convert()
        print()  # Clear progress line
        print()

        # Result summary
        _print_result(result, pipe, args.report)
        return 0

    except ConversionError as e:
        print(f"\n[ERROR] Conversion error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 2


# --- Batch Processing ---

def _cmd_batch(args) -> int:
    """Batch convert all PDFs in a directory."""
    input_dir = args.input_dir.resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] Directory not found: {input_dir}", file=sys.stderr)
        return 1

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ERROR] No PDF files found in: {input_dir}", file=sys.stderr)
        return 1

    output_base = (args.output or Path("output")).resolve()
    print(f"[>] Input:  {input_dir}")
    print(f"[>] Output: {output_base}")
    print(f"[>] Found {len(pdf_files)} PDF files")
    print()

    results = []
    errors = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")

        output_dir = output_base / pdf_path.stem

        try:
            pipe = PipelineOrchestrator(
                pdf_path=pdf_path,
                output_dir=output_dir,
                image_format=args.image_format,
                include_frontmatter=not args.no_frontmatter,
            )
            result = pipe.convert()

            total_time = pipe.timings.get("total", 0)
            score = (
                pipe.validation_report.overall_score
                if pipe.validation_report else 0
            )

            results.append({
                "file": pdf_path.name,
                "pages": len(result.pages),
                "blocks": result.total_blocks,
                "time": round(total_time, 2),
                "score": round(score, 2),
                "status": "OK",
            })

            print(
                f"  [OK] {len(result.pages)} pages, "
                f"{result.total_blocks} blocks, "
                f"{total_time:.1f}s, "
                f"score: {score:.0%}"
            )

        except Exception as e:
            errors.append(pdf_path.name)
            results.append({
                "file": pdf_path.name,
                "status": "FAIL",
                "error": str(e),
            })
            print(f"  [FAIL] {e}")

    # Summary
    print()
    print(f"{'=' * 50}")
    print(f"Batch complete: {len(results) - len(errors)}/{len(results)} succeeded")
    if errors:
        print(f"Failed: {', '.join(errors)}")

    # Write batch report
    report_path = output_base / "batch_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Report: {report_path}")

    return 0 if not errors else 1


# --- UI Helpers ---

def _progress_bar(progress: float, step: str):
    """Print an inline progress bar."""
    bar_width = 30
    filled = int(bar_width * progress / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"\r  [{bar}] {progress:5.1f}% {step:<30}", end="", flush=True)


def _print_result(result, pipe: PipelineOrchestrator, show_report: bool):
    """Print conversion result summary."""
    print(f"[OK] Conversion complete!")
    print(f"  Pages:  {len(result.pages)}")
    print(f"  Blocks: {result.total_blocks}")
    print(f"  Images: {result.total_images}")
    print(f"  Tables: {result.total_tables}")

    # Timings
    timings = pipe.timings
    print(f"  Time:   {timings.get('total', 0):.2f}s")

    # Validation
    if pipe.validation_report:
        report = pipe.validation_report
        status = "PASS" if report.is_valid else "WARN"
        print(f"  Score:  [{status}] {report.overall_score:.0%}")

        if show_report:
            print()
            _print_quality_report(report, timings)


def _print_quality_report(report, timings: dict):
    """Print detailed quality report (Phase 9.3)."""
    print("+=========================================+")
    print("|           Quality Report                |")
    print("+=========================================+")
    print(f"|  Overall Score: {report.overall_score:.0%}                        |")
    print(f"|  Total Blocks:  {report.total_blocks:<24}|")
    print(f"|  Classified:    {report.classified_blocks:<24}|")
    print(f"|  Empty Blocks:  {report.empty_blocks:<24}|")
    print(f"|  Errors:        {report.error_count:<24}|")
    print(f"|  Warnings:      {report.warning_count:<24}|")
    print("+-----------------------------------------+")
    print("|  Timing Breakdown:                      |")
    for stage, t in timings.items():
        if stage != "total":
            print(f"|    {stage:<14} {t:.3f}s                  |")
    print(f"|    {'total':<14} {timings.get('total', 0):.3f}s                  |")
    print("+=========================================+")

    if report.issues:
        print()
        print(f"Issues ({len(report.issues)}):")
        for issue in report.issues[:20]:  # Cap at 20
            icon = "[ERR]" if issue.severity == "error" else "[WARN]"
            print(f"  {icon} [p{issue.page}] {issue.message}")
        if len(report.issues) > 20:
            print(f"  ... and {len(report.issues) - 20} more")


if __name__ == "__main__":
    main()
