"""CLI runner for validation dataset recovery and benchmark protocol.

Executes:
1. Search local files and report discovered assets.
2. Check whether a full labelled dataset is already available.
3. Check available free disk space.
4. Evaluate authentic external sources against strict 500 MB limit.
5. Refuse any downloads exceeding 500 MB.
6. Generate dataset provenance, restored dataset manifest, and reports.
7. Freeze benchmark protocol and verify model architecture protocol.
8. Print final PASS / BLOCKED / INCOMPLETE_DATASET / FAIL status.
"""

from pathlib import Path
import json
import sys

# Ensure project root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from validation.dataset import (  # noqa: E402
    generate_dataset_manifest,
    generate_dataset_audit_markdown,
    generate_dataset_provenance,
    generate_restored_dataset_manifest,
    generate_restored_dataset_audit_markdown,
    scan_local_aptos_assets,
    get_available_disk_space,
    check_download_eligibility,
)
from validation.model_protocol import (  # noqa: E402
    run_model_protocol_verification,
    generate_model_protocol_markdown,
)
from validation.benchmark_protocol import (  # noqa: E402
    get_frozen_benchmark_protocol_config,
)


def main() -> int:
    """Run full validation dataset recovery audit and protocol export."""
    results_dir = WORKSPACE_ROOT / "results" / "validation"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("CLINICAL VALIDATION DATASET RECOVERY & BENCHMARK AUDIT")
    print("=" * 70)

    # 1. Search local files and report discovered assets
    print("\n[1/6] Searching local machine for APTOS assets...")
    discovered_assets = scan_local_aptos_assets()
    local_data_found = len(discovered_assets) > 0
    print(f" -> Discovered {len(discovered_assets)} relevant local files:")
    for a in discovered_assets:
        labels_str = "YES" if a.get("has_labels") else "NO"
        fname = a["filename"]
        ftype = a["file_type"]
        fsize = a["size_mb"]
        print(f"    - {fname} ({ftype}, {fsize} MB, labels: {labels_str})")

    # 2. Check available disk space
    print("\n[2/6] Checking available disk space...")
    disk_space = get_available_disk_space(WORKSPACE_ROOT)
    free_gb = disk_space["free_gb"]
    free_mb = disk_space["free_mb"]
    print(f" -> Available disk space: {free_gb} GB ({free_mb} MB)")

    # 3. Search and audit labelled evaluation dataset
    print("\n[3/6] Auditing local dataset splits and schemas...")
    base_manifest = generate_dataset_manifest()
    status = base_manifest.get("dataset_status", "UNKNOWN")
    full_aptos_available = bool(status == "PASS")
    print(f" -> Dataset status from local audit: {status}")
    print(f" -> Full labelled APTOS available locally: {full_aptos_available}")

    # 4. Authentic external source check against 500 MB limit
    print("\n[4/6] Checking external dataset sources & 500 MB limit...")
    candidate_sources = [
        {
            "name": "aptos2019-blindness-detection (Kaggle)",
            "url": "https://www.kaggle.com/c/aptos2019-blindness-detection",
            "size_bytes": 9_500_000_000,  # ~9.5 GB
        },
        {
            "name": "mariaherrerot/aptos2019 (Hugging Face)",
            "url": "https://huggingface.co/datasets/mariaherrerot/aptos2019",
            "size_bytes": 6_830_000_000,  # ~6.83 GB
        },
    ]

    download_used_bytes = 0
    for cand in candidate_sources:
        cand_size = int(cand["size_bytes"])
        cand_name = str(cand["name"])
        eligibility = check_download_eligibility(
            cand_size, cand_name
        )
        action = (
            "REFUSED (>500MB)" if not eligibility["eligible"] else "PERMITTED"
        )
        sz_mb = eligibility["size_mb"]
        lim_mb = eligibility["limit_mb"]
        print(f" -> Candidate: {cand_name}")
        print(f"    Size: {sz_mb} MB | Limit: {lim_mb} MB | Action: {action}")

    # Enforce rule: Stop and mark BLOCKED if authentic source > 500 MB
    if not full_aptos_available:
        status = "BLOCKED"
        status_reason = (
            "Full labelled APTOS benchmark dataset unavailable locally; "
            "canonical archives exceed the strict 500 MB limit."
        )
    else:
        status_reason = base_manifest.get("status_reason", "")

    # 5. Generate provenance and manifests
    print("\n[5/6] Generating provenance, manifest, and audit reports...")
    c_url = "https://www.kaggle.com/c/aptos2019-blindness-detection/data"
    provenance = generate_dataset_provenance(
        source="Kaggle / Local Workspace Audit",
        source_url=c_url,
        local_path=str(WORKSPACE_ROOT / "data"),
        original_file_size_bytes=9_500_000_000,
        downloaded_size_bytes=download_used_bytes,
        extraction_status="NOT_APPLICABLE",
        image_count=0,
        label_count=0,
        completeness_status=status,
        status_reason=status_reason,
    )

    provenance_path = results_dir / "dataset_provenance.json"
    with open(provenance_path, "w") as f:
        json.dump(provenance, f, indent=2)
    print(f" -> Saved provenance: {provenance_path}")

    restored_manifest = generate_restored_dataset_manifest(
        provenance=provenance
    )
    restored_manifest_path = results_dir / "restored_dataset_manifest.json"
    with open(restored_manifest_path, "w") as f:
        json.dump(restored_manifest, f, indent=2)
    print(f" -> Saved restored dataset manifest: {restored_manifest_path}")

    manifest_path = results_dir / "dataset_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(base_manifest, f, indent=2)
    print(f" -> Saved standard dataset manifest: {manifest_path}")

    restored_report_md = generate_restored_dataset_audit_markdown(
        restored_manifest
    )
    restored_report_path = results_dir / "restored_dataset_audit_report.md"
    with open(restored_report_path, "w") as f:
        f.write(restored_report_md)
    print(f" -> Saved restored dataset audit report: {restored_report_path}")

    audit_md = generate_dataset_audit_markdown(base_manifest)
    audit_md_path = results_dir / "dataset_audit_report.md"
    with open(audit_md_path, "w") as f:
        f.write(audit_md)
    print(f" -> Saved dataset audit report: {audit_md_path}")

    # Freeze protocol configs
    protocol_config = get_frozen_benchmark_protocol_config()
    config_path = results_dir / "benchmark_protocol.json"
    with open(config_path, "w") as f:
        json.dump(protocol_config, f, indent=2)
    print(f" -> Saved benchmark protocol config: {config_path}")

    model_verification = run_model_protocol_verification()
    model_md = generate_model_protocol_markdown(model_verification)
    model_md_path = results_dir / "model_protocol_report.md"
    with open(model_md_path, "w") as f:
        f.write(model_md)
    print(f" -> Saved model protocol report: {model_md_path}")

    # 6. Final Status Output
    download_used_mb = round(download_used_bytes / (1024 * 1024), 2)
    local_found_str = "YES" if local_data_found else "NO"
    full_aptos_str = "YES" if full_aptos_available else "NO"

    print("\n" + "=" * 70)
    print("FINAL SUMMARY REPORT")
    print("=" * 70)
    print(f"DOWNLOAD USED: {download_used_mb} MB")
    print(f"LOCAL DATA FOUND: {local_found_str}")
    print(f"FULL LABELLED APTOS AVAILABLE: {full_aptos_str}")
    print(f"DATASET STATUS: {status}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
