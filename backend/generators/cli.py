"""
CLI Entry Point for Industrial Master Data, Telemetry, and Failure Event Generation.
Provides subcommands:
  - master-data: Seed plants, production lines, operating shifts, machines, sensors, parts, technicians
  - telemetry: Stream 90 days of high-throughput synthetic telemetry via PostgreSQL COPY
  - failures: Generate deterministic failure events and linked corrective maintenance work orders
"""

import argparse
import sys
from typing import Dict, Any

from backend.database import SessionLocal
from backend.generators.master_data_constants import DEFAULT_RANDOM_SEED
from backend.generators.master_data_generator import MasterDataGenerator
from backend.generators.telemetry_constants import DEFAULT_TELEMETRY_SEED
from backend.generators.telemetry_generator import TelemetryGenerator
from backend.generators.failure_constants import DEFAULT_FAILURE_SEED
from backend.generators.failure_generator import FailureGenerator


def print_master_data_summary(stats: Dict[str, Dict[str, int]], dry_run: bool = False) -> None:
    """Print a structured summary of the generated master data records."""
    mode_text = "DRY-RUN (Changes Rolled Back)" if dry_run else "COMMITTED"
    print("\n" + "=" * 65)
    print(f" Master Data Generation Summary [{mode_text}]")
    print("=" * 65)
    print(f"{'Entity':<26} | {'Created':<10} | {'Existing':<10} | {'Total':<10}")
    print("-" * 65)
    for entity, counts in stats.items():
        formatted_entity = entity.replace("_", " ").title()
        print(
            f"{formatted_entity:<26} | {counts['created']:<10} | {counts['existing']:<10} | {counts['total']:<10}"
        )
    print("=" * 65 + "\n")


def print_telemetry_summary(stats: Dict[str, Any], dry_run: bool = False) -> None:
    """Print a structured summary of the generated telemetry records."""
    mode_text = "DRY-RUN (Changes Rolled Back)" if dry_run else "COMMITTED"
    print("\n" + "=" * 65)
    print(f" Telemetry Generation Summary [{mode_text}]")
    print("=" * 65)
    print(f"Window Start UTC       : {stats['window_start']}")
    print(f"Window End UTC         : {stats['window_end']}")
    print(f"Sensors Streamed       : {stats['target_sensors']}")
    print(f"Readings per Sensor    : {stats['readings_per_sensor']:,}")
    print(f"Total Rows Ingested    : {stats['total_records_inserted']:,}")
    print(f"Previous Rows Cleared  : {stats['deleted_previous_records']:,}")
    print(f"Execution Duration     : {stats['duration_seconds']}s")
    print("-" * 65)
    print("Quality Status Breakdown:")
    q_dist = stats["quality_distribution"]
    total = stats["total_records_inserted"] or 1
    for q_status, count in q_dist.items():
        pct = (count / total) * 100.0
        print(f"  - {q_status:<20}: {count:>10,} ({pct:>5.2f}%)")
    print("=" * 65 + "\n")


def print_failure_summary(stats: Dict[str, Any], dry_run: bool = False) -> None:
    """Print a structured summary of generated failure events and maintenance work orders."""
    mode_text = "DRY-RUN (Changes Rolled Back)" if dry_run else "COMMITTED"
    print("\n" + "=" * 70)
    print(f" Failure Events & Work Orders Generation Summary [{mode_text}]")
    print("=" * 70)
    print(f"Master Seed              : {stats['master_seed']}")
    print(f"Window Start UTC         : {stats['window_start']}")
    print(f"Window End UTC           : {stats['window_end']}")
    print(f"Total Failures Generated : {stats['total_failures_generated']}")
    print(f"  - Type A (Progressive) : {stats['type_a_failures']}")
    print(f"  - Type B (Stochastic)  : {stats['type_b_failures']}")
    print(f"Total Work Orders        : {stats['total_work_orders_generated']}")
    print(f"  - Corrective Orders    : {stats['work_order_types']['corrective']}")
    print(f"  - Preventive Orders    : {stats['work_order_types']['preventive']}")
    print(f"Execution Duration       : {stats['duration_seconds']}s")
    print("-" * 70)
    print("Work Order Status Breakdown:")
    for status, count in stats["status_distribution"].items():
        pct = (count / (stats["total_work_orders_generated"] or 1)) * 100.0
        print(f"  - {status:<18}: {count:>5} ({pct:>5.1f}%)")
    print("-" * 70)
    print("Type B Machine Event Frequency Breakdown (across 77 eligible machines):")
    for freq_key, count in stats.get("type_b_machine_event_frequencies", {}).items():
        num_ev = freq_key.split("_")[0]
        print(f"  - Machines with {num_ev} failures : {count:>2} machines ({count * int(num_ev)} total failures)")
    print("=" * 70 + "\n")


def run_master_data(args: argparse.Namespace) -> int:
    """Execute master data generation."""
    print(f"[INFO] Initializing Master Data Generator with seed: {args.seed} (dry_run={args.dry_run})")
    session = SessionLocal()
    try:
        generator = MasterDataGenerator(seed=args.seed, session=session)
        stats = generator.generate(dry_run=args.dry_run)

        if args.dry_run:
            print("[INFO] Dry-run completed successfully; all transactions rolled back.")
        else:
            print("[INFO] Master data successfully generated and committed to the database.")

        print_master_data_summary(stats, dry_run=args.dry_run)
        return 0
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Master data generation failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


def run_telemetry(args: argparse.Namespace) -> int:
    """Execute telemetry generation."""
    scale = getattr(args, "scale", "full")
    max_chunks = 1 if scale == "starter" else None
    print(
        f"[INFO] Initializing Telemetry Generator with seed: {args.seed} (scale={scale}) "
        f"(dry_run={args.dry_run}, overwrite={args.overwrite})"
    )
    session = SessionLocal()
    try:
        def on_progress(chunk_num: int, total_chunks: int, msg: str) -> None:
            print(f"[PROGRESS] {msg}")

        generator = TelemetryGenerator(seed=args.seed, session=session)
        stats = generator.generate(
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            max_chunks=max_chunks,
            progress_callback=on_progress,
        )

        if args.dry_run:
            print("[INFO] Dry-run completed successfully; simulated rows rolled back.")
        else:
            print("[INFO] Telemetry successfully generated and committed to the database.")

        print_telemetry_summary(stats, dry_run=args.dry_run)
        return 0
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Telemetry generation failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


def run_export(args: argparse.Namespace) -> int:
    """Execute database export to CSV, JSON, and SQL."""
    from pathlib import Path
    try:
        from backend.utils.exporter import DataExporter
    except ImportError:
        from utils.exporter import DataExporter

    base_dir = Path(__file__).resolve().parent.parent.parent
    session = SessionLocal()
    try:
        exporter = DataExporter(session=session, base_dir=base_dir)
        exporter.export_all()
        print("[SUCCESS] Export stage completed successfully.")
        return 0
    except Exception as exc:
        print(f"[ERROR] Export failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


def run_validate(args: argparse.Namespace) -> int:
    """Execute database validation checks."""
    try:
        from backend.validators.data_validator import DataValidator
    except ImportError:
        from validators.data_validator import DataValidator

    session = SessionLocal()
    try:
        validator = DataValidator(session=session)
        report = validator.validate_all()
        print("\n" + "=" * 65)
        print(" Data Validation Summary")
        print("=" * 65)
        print(f"Overall Valid: {report.get('overall_valid')}")
        checks = report.get("checks", {})
        for name, res in checks.items():
            status = "PASS" if res.get("passed", res.get("status") == "PASS") else "FAIL"
            print(f"  - {name:<30}: {status}")
        print("=" * 65 + "\n")
        return 0 if report.get("overall_valid", True) else 1
    except Exception as exc:
        print(f"[ERROR] Validation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


def run_reproduce(args: argparse.Namespace) -> int:
    """Execute deterministic reproducibility verification."""
    try:
        from backend.utils.reproducibility_checker import verify_reproducibility
    except ImportError:
        from utils.reproducibility_checker import verify_reproducibility

    try:
        verify_reproducibility()
        return 0
    except Exception as exc:
        print(f"[ERROR] Reproducibility verification failed: {exc}", file=sys.stderr)
        return 1


def run_failures(args: argparse.Namespace) -> int:
    """Execute failure event and maintenance work order generation."""
    print(
        f"[INFO] Initializing Failure & Work Order Generator with seed: {args.seed} "
        f"(dry_run={args.dry_run}, overwrite={args.overwrite})"
    )
    session = SessionLocal()
    try:
        def on_progress(step: int, total_steps: int, msg: str) -> None:
            print(f"[PROGRESS] [{step}/{total_steps}] {msg}")

        generator = FailureGenerator(seed=args.seed, session=session)
        stats = generator.generate(
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            progress_callback=on_progress,
        )

        if args.dry_run:
            print("[INFO] Dry-run completed successfully; 150 failure & work order records rolled back.")
        else:
            print("[INFO] Failure events and work orders successfully generated and committed.")

        print_failure_summary(stats, dry_run=args.dry_run)
        return 0
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Failure generation failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


def main() -> int:
    """Main CLI parser supporting master-data, telemetry, and failures subcommands."""
    parser = argparse.ArgumentParser(
        description="Industrial Predictive Maintenance - Data Generators CLI"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Generator subcommand to run")

    # master-data subcommand
    p_master = subparsers.add_parser(
        "master-data", help="Generate plants, lines, machines, sensors, parts, technicians"
    )
    p_master.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help=f"Deterministic random seed (default: {DEFAULT_RANDOM_SEED})",
    )
    p_master.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute generation inside a transaction and roll back without committing",
    )

    # telemetry subcommand
    p_telem = subparsers.add_parser(
        "telemetry", help="Stream synthetic telemetry dataset via PostgreSQL COPY"
    )
    p_telem.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_TELEMETRY_SEED,
        help=f"Deterministic random seed (default: {DEFAULT_TELEMETRY_SEED})",
    )
    p_telem.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="full",
        help="Dataset scale: starter (10-day sample) or full (90-day window)",
    )
    p_telem.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute streaming & COPY, validate results, then rollback without committing",
    )
    p_telem.add_argument(
        "--overwrite",
        action="store_true",
        help="Safely overwrite existing telemetry records strictly within the window",
    )

    # failures subcommand (and alias 'events')
    for alias in ["failures", "events"]:
        p_fail = subparsers.add_parser(
            alias, help="Generate deterministic failure events and linked corrective work orders"
        )
        p_fail.add_argument(
            "--seed",
            type=int,
            default=DEFAULT_FAILURE_SEED,
            help=f"Deterministic random seed (default: {DEFAULT_FAILURE_SEED})",
        )
        p_fail.add_argument(
            "--dry-run",
            action="store_true",
            help="Execute generation inside a transaction and roll back without committing",
        )
        p_fail.add_argument(
            "--overwrite",
            action="store_true",
            help="Safely overwrite existing failure events and work orders strictly within the 90-day window",
        )

    # export subcommand
    subparsers.add_parser("export", help="Export PostgreSQL database entities to CSV, JSON, and SQL")

    # validate subcommand
    subparsers.add_parser("validate", help="Run comprehensive relational and edge-case validation checks")

    # reproduce subcommand
    subparsers.add_parser("reproduce", help="Verify seed-based reproducibility and SHA-256 hash invariants")

    # Backward compatibility: top-level arguments default to master-data if no subcommand provided
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    if args.subcommand == "telemetry":
        return run_telemetry(args)
    elif args.subcommand in ("failures", "events"):
        return run_failures(args)
    elif args.subcommand == "export":
        return run_export(args)
    elif args.subcommand == "validate":
        return run_validate(args)
    elif args.subcommand == "reproduce":
        return run_reproduce(args)
    elif args.subcommand == "master-data" or args.subcommand is None:
        return run_master_data(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
