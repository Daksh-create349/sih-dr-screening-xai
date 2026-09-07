#!/usr/bin/env python3
"""Runner script for image quality dataset audit."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from image_quality.audit import run_data_audit

def main():
    data_dir = root_dir / "data" / "real_retinal_images"
    output_dir = root_dir / "image_quality" / "results"
    summary = run_data_audit(data_dir, output_dir)
    print("=" * 60)
    print("DATA AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total images found:    {summary['total_images_discovered']}")
    print(f"Successfully audited:  {summary['successfully_audited']}")
    print(f"Failed loads:          {summary['failed_audits']}")
    print(f"Audit pass rate:       {summary['audit_pass_rate_pct']}%")
    print("=" * 60)
    print(f"Reports saved to: {output_dir}")

if __name__ == "__main__":
    main()
