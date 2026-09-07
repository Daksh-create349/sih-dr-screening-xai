#!/usr/bin/env python3
"""IDRiD Dataset Audit and Manifest Generation Script.

Implements Task 3 & Task 8:
- Audits external IDRiD dataset directory for images and ground truth annotations.
- Computes SHA-256 cryptographic hashes for integrity and duplicate detection.
- Generates reproducible manifest: evidence/data/idrid_manifest.json.
- Verifies image dimensions, split consistency, and missing annotation flags.
- Fails clearly with 'IDRiD DATASET NOT FOUND' if dataset is missing.
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure workspace root is on sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from evidence.idrid import (
    IDRiDDataset,
    IDRiDNotFoundError,
    resolve_idrid_root,
    MANIFEST_OUTPUT_PATH,
    DEFAULT_LOCAL_IDRID_DIR,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit IDRiD dataset and generate reproducible manifest."
    )
    parser.add_argument(
        "--root",
        "--idrid-root",
        dest="root",
        type=str,
        default=None,
        help="Path to IDRiD dataset root directory (overrides IDRID_ROOT env var).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=str(MANIFEST_OUTPUT_PATH),
        help=f"Output manifest JSON path (default: {MANIFEST_OUTPUT_PATH}).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if IDRiD dataset is not found.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    resolved_root = resolve_idrid_root(cli_arg=args.root)
    output_path = Path(args.output).resolve()

    print("========================================")
    print("IDRiD DATASET INTEGRITY AUDIT")
    print("========================================")
    print(f"Target Root:     {resolved_root}")
    print(f"Output Manifest: {output_path}")

    # Instantiate dataset in inspection mode (require_exists=False)
    ds = IDRiDDataset(root=resolved_root, require_exists=False)
    available = ds.is_available()

    if not available:
        print("\nSTATUS: IDRiD DATASET NOT FOUND")
        print(f"No genuine IDRiD fundus images located in '{resolved_root}'.")
        print("Note: In accordance with clinical data safety guidelines,")
        print("no synthetic data or mock masks will be generated.\n")

        manifest = ds.generate_manifest(output_path=output_path)
        print(f"Wrote audit stub manifest to: {output_path}")

        if args.strict:
            sys.exit(1)
        return 0

    print("\nSTATUS: IDRiD DATASET FOUND")
    manifest = ds.generate_manifest(output_path=output_path)
    total_imgs = manifest.get("total_images", 0)
    print(f"Total Discovered Images: {total_imgs}")

    # Run integrity audit
    audit = ds.audit_integrity()
    print(f"Total Files Audited:     {audit.get('total_files', 0)}")
    print(f"Unique SHA-256 Hashes:   {audit.get('unique_hashes', 0)}")
    print(f"Duplicates Detected:     {audit.get('duplicates_detected', 0)}")
    print(f"Cross-Split Leakage:     {audit.get('split_leakage_detected', False)}")

    if audit.get("duplicates_detected", 0) > 0:
        print("\n[WARNING] Duplicate files identified (retained, not deleted):")
        for sha, files in audit.get("duplicate_groups", {}).items():
            print(f"  SHA-256: {sha[:12]}... -> {files}")

    print(f"\nManifest successfully written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
