#!/usr/bin/env python3
"""
Automated Opaque-Box E2E Test Runner for Smart Inbox Assistant
Executes Tiers 1-4 per Dual-Track Specification.

Usage:
    python tests/e2e/test_runner.py [--tier 1|2|3|4|all] [--live] [--mock] [--verbose] [--report PATH]
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

TIER_FILES = {
    "1": "test_tier1_features.py",
    "2": "test_tier2_boundaries.py",
    "3": "test_tier3_combinations.py",
    "4": "test_tier4_real_world.py"
}

TIER_NAMES = {
    "1": "Tier 1: Feature Coverage (>=5 per feature)",
    "2": "Tier 2: Boundary & Corner Cases (>=5 per feature)",
    "3": "Tier 3: Cross-Feature Combinations",
    "4": "Tier 4: Real-World Scenarios (Manifest Verification)"
}


class TierResultCollector:
    def __init__(self):
        self.tier_data = {
            "1": {"name": TIER_NAMES["1"], "passed": 0, "failed": 0, "skipped": 0, "total": 0, "duration": 0.0, "tests": []},
            "2": {"name": TIER_NAMES["2"], "passed": 0, "failed": 0, "skipped": 0, "total": 0, "duration": 0.0, "tests": []},
            "3": {"name": TIER_NAMES["3"], "passed": 0, "failed": 0, "skipped": 0, "total": 0, "duration": 0.0, "tests": []},
            "4": {"name": TIER_NAMES["4"], "passed": 0, "failed": 0, "skipped": 0, "total": 0, "duration": 0.0, "tests": []}
        }

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            tier_key = "1"
            nodeid = report.nodeid
            for k, f in TIER_FILES.items():
                if f in nodeid:
                    tier_key = k
                    break

            entry = self.tier_data[tier_key]
            entry["total"] += 1
            entry["duration"] += report.duration

            if report.passed:
                entry["passed"] += 1
                status = "PASSED"
            elif report.skipped:
                entry["skipped"] += 1
                status = "SKIPPED"
            else:
                entry["failed"] += 1
                status = "FAILED"

            entry["tests"].append({
                "nodeid": nodeid,
                "status": status,
                "duration": round(report.duration, 4)
            })


def print_banner():
    print("=" * 80)
    print("        SMART INBOX ASSISTANT — OPAQUE-BOX E2E TEST SUITE RUNNER")
    print("=" * 80)


def generate_markdown_report(tier_data: dict, report_path: Path, mode: str, total_duration: float):
    total_passed = sum(t["passed"] for t in tier_data.values())
    total_failed = sum(t["failed"] for t in tier_data.values())
    total_skipped = sum(t["skipped"] for t in tier_data.values())
    total_count = sum(t["total"] for t in tier_data.values())
    overall_status = "PASS" if total_failed == 0 and total_count > 0 else "FAIL"

    lines = [
        "# E2E Automated Test Suite Execution Report",
        f"\n**Execution Mode:** {mode}",
        f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}",
        f"**Overall Result:** {overall_status} ({total_passed}/{total_count} Passed)",
        f"**Total Duration:** {round(total_duration, 2)}s\n",
        "## Tier Summary\n",
        "| Tier | Name | Total | Passed | Failed | Skipped | Duration (s) | Status |",
        "|------|------|-------|--------|--------|---------|--------------|--------|"
    ]

    for k in sorted(tier_data.keys()):
        r = tier_data[k]
        if r["total"] == 0:
            continue
        status_badge = "✅ PASS" if r["failed"] == 0 else "❌ FAIL"
        lines.append(
            f"| {k} | {r['name']} | {r['total']} | {r['passed']} | {r['failed']} | {r['skipped']} | {round(r['duration'], 2)}s | {status_badge} |"
        )

    lines.append("\n## Detailed Test Inventory\n")
    for k in sorted(tier_data.keys()):
        r = tier_data[k]
        if r["total"] == 0:
            continue
        lines.append(f"### {r['name']} ({r['passed']}/{r['total']} Passed)\n")
        lines.append("| Test Case | Status | Duration (s) |")
        lines.append("|-----------|--------|--------------|")
        for t in r["tests"]:
            test_name = t["nodeid"].split("::")[-1]
            status_icon = "✅ PASSED" if t["status"] == "PASSED" else "❌ FAILED"
            lines.append(f"| `{test_name}` | {status_icon} | {t['duration']}s |")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[INFO] Test report successfully generated: {report_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Opaque-Box E2E Test Suite Runner")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "all"], default="all", help="Test Tier to execute (default: all)")
    parser.add_argument("--live", action="store_true", help="Target live services (disables mock fallback)")
    parser.add_argument("--mock", action="store_true", help="Force embedded mock server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose pytest output")
    parser.add_argument("--report", type=str, default=None, help="Output markdown report path")

    args = parser.parse_args()

    if args.live:
        os.environ["E2E_USE_MOCK_FALLBACK"] = "false"
        os.environ["E2E_FORCE_MOCK"] = "false"
        mode = "LIVE (http://localhost:8080 & http://localhost:8000)"
    elif args.mock:
        os.environ["E2E_FORCE_MOCK"] = "true"
        mode = "MOCK (Embedded Stateful Server)"
    else:
        mode = "AUTO (Live with Mock Fallback)"

    print_banner()
    print(f"Target Environment: {mode}")
    print(f"Target Scope:       Tier '{args.tier}'")
    print("-" * 80)

    # Determine pytest arguments
    if args.tier == "all":
        test_path = PROJECT_ROOT / "tests" / "e2e"
    else:
        test_path = PROJECT_ROOT / "tests" / "e2e" / TIER_FILES[args.tier]

    collector = TierResultCollector()
    pytest_args = ["-q", str(test_path)]
    if args.verbose:
        pytest_args.append("-v")

    print(f">> Running pytest on: {test_path.name}...\n")
    start_time = time.time()
    exit_code = pytest.main(pytest_args, plugins=[collector])
    total_duration = time.time() - start_time

    # Display final summary table
    print("\n" + "=" * 80)
    print("                             FINAL SUMMARY")
    print("=" * 80)
    print(f"{'Tier':<6} | {'Description':<46} | {'Passed':<7} | {'Failed':<7} | {'Status':<6}")
    print("-" * 80)

    total_passed = 0
    total_failed = 0
    total_count = 0

    active_tiers = [args.tier] if args.tier != "all" else ["1", "2", "3", "4"]
    for k in active_tiers:
        r = collector.tier_data[k]
        total_passed += r["passed"]
        total_failed += r["failed"]
        total_count += r["total"]
        status = "PASS" if r["failed"] == 0 and r["total"] > 0 else "FAIL"
        print(f"{k:<6} | {r['name']:<46} | {r['passed']:<7} | {r['failed']:<7} | {status:<6}")

    print("-" * 80)
    overall = "ALL TESTS PASSED" if total_failed == 0 and total_count > 0 else f"{total_failed} TESTS FAILED"
    print(f"TOTAL: {total_passed}/{total_count} Passed ({overall}) in {round(total_duration, 2)}s")
    print("=" * 80)

    if args.report:
        generate_markdown_report(collector.tier_data, Path(args.report), mode, total_duration)

    sys.exit(0 if total_failed == 0 and total_count > 0 else 1)


if __name__ == "__main__":
    main()
