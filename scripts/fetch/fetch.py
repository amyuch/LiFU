# scripts/fetch/fetch.py
"""
Fetch Stage: Select and promote seeds from corpus + W$
Output: queue_fetch/*.s
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import yaml
import json
from utils.models import Testcase
from utils.wcache import WeightCache

# === Paths ===
ROOT = Path(__file__).parent.parent.parent
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text())
WCACHE = WeightCache(ROOT / "wcache.json", CONFIG["wcache"])
QUEUE_DIR = ROOT / "queue_fetch"
QUEUE_DIR.mkdir(exist_ok=True)

def fetch():
    print("[FETCH] Starting seed selection...")

    # 1. Load all seeds from sources
    seeds = []
    for src_path in CONFIG["pipeline"]["seed_sources"]:
        src = ROOT / src_path
        print(f"[LOAD] {src}")
        if not src.exists():
            print(f"[WARN] Source not found: {src}")
            continue
        for f in (src.glob("*.S")):
            print(f"  [LOAD] {f.name}")
            try:
                tc = Testcase.from_file(f, source=src_path)
                seeds.append(tc)
                print(f"  [LOAD] {tc.id} ← {f.name}")
            except Exception as e:
                print(f"  [SKIP] {f}: {e}")

    if not seeds:
        print("[ERROR] No seeds found!")
        return

    # 2. Promote from W$
    top_k = WCACHE.top_k(CONFIG["pipeline"]["batch_size"])
    promoted_ids = [tid for tid, _ in top_k]
    promoted = [s for s in seeds if s.id in promoted_ids]

    # 3. Fallback: take random if not enough
    import random
    if len(promoted) < CONFIG["pipeline"]["batch_size"]:
        remaining = [s for s in seeds if s.id not in promoted_ids]
        random.shuffle(remaining)
        promoted += remaining[:CONFIG["pipeline"]["batch_size"] - len(promoted)]

    selected = promoted[:CONFIG["pipeline"]["batch_size"]]

    # 4. Save to queue
    for tc in selected:
        out_path = tc.save(QUEUE_DIR)
        print(f"  [QUEUE] {tc.id} → {out_path.name}")

    print(f"[FETCH] Selected {len(selected)} seeds → queue_fetch/")

if __name__ == "__main__":
    fetch()