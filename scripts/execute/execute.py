# scripts/3_execute.py
import asyncio, subprocess, json
from pathlib import Path
from utils.models import Testcase

IN_DIR = Path("../queue_mutate")
ISS_LOG_DIR = Path("../logs/iss")
DUT_LOG_DIR = Path("../logs/dut")
ISS_LOG_DIR.mkdir(exist_ok=True), DUT_LOG_DIR.mkdir(exist_ok=True)

async def run_iss(tc: Testcase) -> dict:
    cmd = ["spike", "--isa=RV64GC", str(tc.path)]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
    log_path = ISS_LOG_DIR / f"{tc.id}.json"
    log_path.write_text(json.dumps({"trace": out.decode().splitlines()}))
    return {"cycles": len(out.decode().splitlines()), "log": str(log_path)}

async def run_dut(tc: Testcase, idx: int) -> dict:
    await asyncio.sleep(1)  # simulate RTL
    log_path = DUT_LOG_DIR / f"{tc.id}_dut{idx}.json"
    log_path.write_text(json.dumps({"coverage": [f"b{idx}"]}))
    return {"log": str(log_path)}

async def execute():
    tasks = []
    for f in IN_DIR.glob("*.s"):
        tc = Testcase.from_file(f)
        tasks.append(run_iss(tc))
        for i in range(3):
            tasks.append(run_dut(tc, i))
    await asyncio.gather(*tasks)
    print(f"[EXECUTE] → {len(IN_DIR.glob('*.s'))} testcases")

if __name__ == "__main__":
    asyncio.run(execute())