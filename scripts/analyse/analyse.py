# scripts/4_analyse.py
import json, yaml
from pathlib import Path
from utils.wcache import WeightCache
from utils.llm import llm_generate_property
import asyncio

CONFIG = yaml.safe_load(Path("../config.yaml").read_text())
WCACHE = WeightCache(Path("../wcache.json"), CONFIG["wcache"])
LOGS_DIR = Path("../logs")

async def analyse():
    for iss_log in LOGS_DIR.glob("iss/*.json"):
        tc_id = iss_log.stem
        dut_logs = list((LOGS_DIR / "dut").glob(f"{tc_id}*.json"))
        if not dut_logs: continue

        # Mock coverage + bug
        delta_cov = 0.1
        bug_score = 1 if random.random() > 0.8 else 0
        cycles = 500

        # Update W$
        WCACHE.update(tc_id, delta_cov, bug_score, cycles)

        # LLM property
        if bug_score > 0:
            prop = await llm_generate_property("PC mismatch at cycle 42")
            print(f"[LLM] → {prop}")

if __name__ == "__main__":
    import random
    asyncio.run(analyse())