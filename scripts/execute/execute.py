# scripts/execute/execute.py
"""
Execute Stage: Asymmetric simulation with ISS pre-run
1. Filter
2. ISS pre-run (fast oracle)
3. DUT execution (slow)
4. Differential check
Output: logs/iss/*.json, logs/dut/*.json
"""

import sys
import json
import asyncio
from pathlib import Path

# === Add project root ===
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.models import Testcase
from scripts.execute.filter import LightweightFilter
from scripts.execute.checker import DifferentialChecker

# === Paths ===
IN_DIR = PROJECT_ROOT / "queue_mutate"
ISS_LOG_DIR = PROJECT_ROOT / "logs" / "iss"
DUT_LOG_DIR = PROJECT_ROOT / "logs" / "dut"
ISS_LOG_DIR.mkdir(parents=True, exist_ok=True)
DUT_LOG_DIR.mkdir(parents=True, exist_ok=True)

# === Mock ISS & DUT (replace with real spike/verilator) ===
async def run_iss(tc: Testcase) -> dict:
    await asyncio.sleep(0.01)  # fast
    trace = [{"pc": 0x1000 + i*4, "x1": i, "x2": i+1, "x3": i+2} for i in range(100)]
    return {"trace": trace, "cycles": 100}

async def run_dut(tc: Testcase, dut_id: int) -> dict:
    await asyncio.sleep(0.5)  # slow RTL
    # Simulate divergence
    offset = 1 if dut_id == 1 else 0
    trace = [{"pc": 0x1000 + i*4 + offset, "x1": i, "x2": i+1, "x3": i+2} for i in range(100)]
    return {"trace": trace, "cycles": 500}

# === Main ===
async def execute():
    print(f"[EXECUTE] Reading from: {IN_DIR}")
    if not list(IN_DIR.glob("*.s")):
        print("[ERROR] No mutants in queue_mutate!")
        return

    filter = LightweightFilter()
    checker = DifferentialChecker()

    for seed_file in IN_DIR.glob("*.s"):
        tc = Testcase.from_file(seed_file)
        print(f"  [TESTCASE] {tc.id[:8]}... ({tc.source})")

        # 1. Filter
        if not filter.is_valid(tc):
            print(f"    [FILTER] Rejected")
            continue

        # 2. ISS pre-run
        iss_result = await run_iss(tc)
        iss_log = ISS_LOG_DIR / f"{tc.id}.json"
        iss_log.write_text(json.dumps({"trace": iss_result["trace"], "cycles": iss_result["cycles"]}))
        print(f"    [ISS] → {iss_log.name} ({iss_result['cycles']} cycles)")

        # 3. DUT runs
        dut_tasks = [run_dut(tc, i) for i in range(3)]
        dut_results = await asyncio.gather(*dut_tasks)
        for i, res in enumerate(dut_results):
            dut_log = DUT_LOG_DIR / f"{tc.id}_dut{i}.json"
            dut_log.write_text(json.dumps({"trace": res["trace"], "cycles": res["cycles"]}))
            print(f"    [DUT{i}] → {dut_log.name}")

        # 4. Differential check
        dut_traces = [r["trace"] for r in dut_results]
        mismatches = checker.compare(iss_result["trace"], dut_traces, [0,1,2])
        if mismatches:
            print(f"    [MISMATCH] {len(mismatches)} found:")
            for m in mismatches[:2]:
                print(f"      cycle {m.cycle}: {m.type} {m.expected} ≠ {m.actual} (DUT{m.dut_id})")
        else:
            print(f"    [PASS] No mismatch")

    print(f"[EXECUTE] Done → logs/iss/, logs/dut/")

if __name__ == "__main__":
    asyncio.run(execute())