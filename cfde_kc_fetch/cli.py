"""
Command-line interface for CFDE Knowledge Center dataset fetcher.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import __version__
from .client import CFDEAPIError, CFDEClient
from .single_cell import (
    download_dataset_registry,
    download_single_cell_assets,
    fetch_single_cell_lognorm,
)


def write_run_params(output_dir: Path, params: Dict[str, Any]) -> None:
    """Write run parameters to JSON file for reproducibility."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_params_path = output_dir / "run_params.json"

    with open(run_params_path, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)

    print(f"[SAVED] Run parameters: {run_params_path}")


def cmd_list_datasets(args: argparse.Namespace) -> int:
    """
    List available single-cell datasets.

    Downloads the dataset registry and displays a table of available datasets.
    """
    try:
        client = CFDEClient(timeout=args.timeout, retries=args.retries)

        print("Downloading dataset registry...")
        registry = download_dataset_registry(
            output_path=args.out,
            overwrite=args.overwrite,
            client=client,
        )

        output_dir = Path(args.out).parent
        write_run_params(
            output_dir,
            {
                "timestamp": datetime.now().isoformat(),
                "command": "list-datasets",
                "output": str(args.out),
                "timeout": args.timeout,
                "retries": args.retries,
            },
        )

        print("\n" + "=" * 80)
        print("Available Single-Cell Datasets")
        print("=" * 80)

        if isinstance(registry, list):
            datasets = registry
        elif isinstance(registry, dict):
            datasets = registry.get("datasets", [registry])
        else:
            datasets = []

        if not datasets:
            print("No datasets found in registry.")
            return 0

        print(f"{'Dataset ID':<30} {'Name/Title':<50}")
        print("-" * 80)

        count = 0
        for dataset in datasets:
            if isinstance(dataset, dict):
                dataset_id = dataset.get("id", dataset.get("dataset_id", "unknown"))
                name = dataset.get(
                    "name", dataset.get("title", dataset.get("description", ""))
                )

                if len(name) > 47:
                    name = name[:44] + "..."

                print(f"{dataset_id:<30} {name:<50}")
                count += 1

        print("-" * 80)
        print(f"Total datasets: {count}")
        print(f"\nRegistry saved to: {args.out}")

        return 0

    except CFDEAPIError as e:
        print(f"[ERROR] API error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_fetch_assets(args: argparse.Namespace) -> int:
    """
    Fetch single-cell dataset assets (coordinates, fields).

    Downloads the coordinates.tsv.gz and fields.json.gz files for the specified dataset.
    """
    try:
        client = CFDEClient(timeout=args.timeout, retries=args.retries)

        print(f"Downloading assets for dataset '{args.dataset_id}'...")
        assets = download_single_cell_assets(
            dataset_id=args.dataset_id,
            output_dir=args.out,
            overwrite=args.overwrite,
            decompress=args.decompress,
            client=client,
        )

        write_run_params(
            Path(args.out),
            {
                "timestamp": datetime.now().isoformat(),
                "command": "fetch-assets",
                "dataset_id": args.dataset_id,
                "output_dir": str(args.out),
                "overwrite": args.overwrite,
                "decompress": args.decompress,
                "timeout": args.timeout,
                "retries": args.retries,
                "endpoints": [
                    f"/api/raw/file/single_cell/{args.dataset_id}/coordinates.tsv.gz",
                    f"/api/raw/file/single_cell/{args.dataset_id}/fields.json.gz",
                ],
            },
        )

        print("\n" + "=" * 80)
        print(f"Successfully downloaded {len(assets)} asset(s):")
        for asset_name, path in assets.items():
            print(f"  - {asset_name}: {path}")
        print("=" * 80)

        return 0

    except CFDEAPIError as e:
        print(f"[ERROR] API error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_fetch_gene(args: argparse.Namespace) -> int:
    """
    Fetch log-normalized gene expression data for a specific gene.

    Queries the single-cell-lognorm endpoint and saves the result.
    """
    try:
        client = CFDEClient(timeout=args.timeout, retries=args.retries)

        print(f"Querying gene '{args.gene}' in dataset '{args.dataset_id}'...")
        data = fetch_single_cell_lognorm(
            dataset_id=args.dataset_id,
            gene=args.gene,
            output_path=args.out,
            client=client,
        )

        output_dir = Path(args.out).parent
        write_run_params(
            output_dir,
            {
                "timestamp": datetime.now().isoformat(),
                "command": "fetch-gene",
                "dataset_id": args.dataset_id,
                "gene": args.gene,
                "output": str(args.out),
                "timeout": args.timeout,
                "retries": args.retries,
                "endpoints": [
                    f"/api/bio/query/single-cell-lognorm?q={args.dataset_id},{args.gene}",
                ],
            },
        )

        print("\n" + "=" * 80)
        print("Successfully queried gene expression data")
        print(f"  Dataset: {args.dataset_id}")
        print(f"  Gene: {args.gene}")
        print(f"  Saved to: {args.out}")

        if isinstance(data, dict):
            print(f"\nResponse contains {len(data)} top-level key(s)")
            for key in list(data.keys())[:5]:
                print(f"  - {key}")
            if len(data) > 5:
                print(f"  ... and {len(data) - 5} more")

        print("=" * 80)

        return 0

    except CFDEAPIError as e:
        print(f"[ERROR] API error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="cfde-kc-fetch",
        description="Fetch single-cell datasets from the CFDE Knowledge Center API",
        epilog="For API documentation, see: https://cfde.hugeampkpnbi.org/docs",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=CFDEClient.DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {CFDEClient.DEFAULT_TIMEOUT})",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=CFDEClient.DEFAULT_RETRIES,
        help=f"Number of retry attempts (default: {CFDEClient.DEFAULT_RETRIES})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    list_parser = subparsers.add_parser(
        "list-datasets",
        help="List available single-cell datasets",
    )
    list_parser.add_argument(
        "--out",
        type=str,
        default="dataset_metadata.json.gz",
        help="Output path for registry file (default: dataset_metadata.json.gz)",
    )
    list_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )
    fetch_parser = subparsers.add_parser(
        "fetch-assets",
        help="Download single-cell dataset assets (coordinates, fields)",
    )
    fetch_parser.add_argument(
        "dataset_id",
        type=str,
        help="Dataset identifier (e.g., heart, lung)",
    )
    fetch_parser.add_argument(
        "--out",
        type=str,
        default=".",
        help="Output directory for downloaded files (default: current directory)",
    )
    fetch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )
    fetch_parser.add_argument(
        "--decompress",
        action="store_true",
        help="Decompress .gz files (keeps .gz files by default)",
    )
    gene_parser = subparsers.add_parser(
        "fetch-gene",
        help="Fetch log-normalized gene expression data",
    )
    gene_parser.add_argument(
        "dataset_id",
        type=str,
        help="Dataset identifier (e.g., heart, lung)",
    )
    gene_parser.add_argument(
        "gene",
        type=str,
        help="Gene symbol (e.g., CP, TP53)",
    )
    gene_parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for JSON response",
    )

    return parser


def main(argv: List[str] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1
    if args.command == "list-datasets":
        return cmd_list_datasets(args)
    if args.command == "fetch-assets":
        return cmd_fetch_assets(args)
    if args.command == "fetch-gene":
        return cmd_fetch_gene(args)
    print(f"[ERROR] Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
