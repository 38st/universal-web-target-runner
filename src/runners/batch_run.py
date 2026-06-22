"""
batch_run: sequential multi-run loop for a configured target.

Usage:
    python -m runners.batch_run --target aws_builder --count 10
"""

import sys
import time
import json
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey-patch undetected_chromedriver.patcher.Patcher.auto() to prevent
# re-download of ChromeDriver on every launch (must precede any uc import).
import patch_uc  # noqa: F401

from datetime import datetime


def batch_run(count: int = 5,
              stagger: int = 25,
              target_name: str = "aws_builder",
              target_config: str | None = None,
              proxy_ok: bool = False,
              proxy_url: str | None = None):
    """
    Run N target flows sequentially.

    Args:
        count:       Number of target run attempts.
        stagger:     Seconds to wait between each run start.
        target_name: Target adapter name.
        target_config: Optional target-specific YAML config.
        proxy_ok:      If True, skip proxy probe (already validated).
        proxy_url:     Pre-resolved proxy URL (pass through to main).
    """
    from runners.main import run

    print(f"\n{'=' * 60}")
    print(f"   BATCH RUNNER — {count} runs")
    print(f"   Target:  {target_name}")
    print(f"   Stagger: {stagger}s between runs")
    print(f"   Email:   configured email backend")
    print(f"   Proxy:   {'enabled' if proxy_url else 'configured per target/run'}")
    print(f"{'=' * 60}\n")

    results = []
    start_time = time.time()

    for i in range(1, count + 1):
        print(f"\n{'─' * 50}")
        print(f"   Run {i}/{count}")
        print(f"{'─' * 50}")

        account_start = time.time()

        try:
            run(target_name=target_name, target_config=target_config)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"\nAccount {i} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "run": i,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            # Write partial report so progress is visible
            _write_batch_report(results)
            _maybe_wait_stagger(i, count, stagger, account_start)
            continue

        elapsed = time.time() - account_start
        print(f"\nRun {i} done in {elapsed:.0f}s")

        results.append({
            "run": i,
            "status": "done",
            "elapsed_s": round(elapsed),
            "timestamp": datetime.now().isoformat(),
        })
        _write_batch_report(results)

        _maybe_wait_stagger(i, count, stagger, account_start)

    total_time = time.time() - start_time
    successes = sum(1 for r in results if r["status"] == "done")
    failures = sum(1 for r in results if r["status"] == "error")

    print(f"\n{'=' * 60}")
    print(f"   BATCH COMPLETE")
    print(f"   Total time: {total_time:.0f}s ({total_time / 60:.1f}m)")
    print(f"   Successes:  {successes}/{count}")
    print(f"   Failures:   {failures}/{count}")
    print(f"   Output:     accounts.jsonl")
    print(f"{'=' * 60}\n")

    _write_batch_report(results)
    return results


def _maybe_wait_stagger(current_run: int, total: int, stagger: int, run_start: float):
    """Wait remaining stagger time if not the last run."""
    if current_run >= total:
        return
    elapsed = time.time() - run_start
    wait = max(0, stagger - elapsed)
    if wait > 0:
        print(f"\n⏳ Waiting {wait:.0f}s before next run...")
        try:
            time.sleep(wait)
        except KeyboardInterrupt:
            raise


def _write_batch_report(results: list):
    """Write batch_report.jsonl with run-level results."""
    with open("batch_report.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Batch target runner")
    parser.add_argument("--target", default="aws_builder",
                        help="Target adapter to run (default: aws_builder)")
    parser.add_argument("--target-config",
                        help="Path to a target-specific YAML config")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of runs to execute (default: 5)")
    parser.add_argument("--stagger", type=int, default=25,
                        help="Seconds between runs (default: 25)")
    args = parser.parse_args()

    if args.count < 1:
        print("Count must be >= 1")
        sys.exit(1)

    try:
        batch_run(
            count=args.count,
            stagger=args.stagger,
            target_name=args.target,
            target_config=args.target_config,
        )
    except KeyboardInterrupt:
        print("\nBatch cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
