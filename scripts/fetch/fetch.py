# scripts/1_fetch.py
import yaml, json, asyncio
from pathlib import Path
from utils.models import Testcase
from utils.wcache import WeightCache

CONFIG = yaml.safe_load(Path("../config.yaml").read_text())
WCACHE = WeightCache(Path("../wcache.json"), CONFIG["wcache"])
CORPUS_DIR = Path("../corpus")
QUEUE_DIR = Path("../queue_fetch")
QUEUE_DIR.mkdir(exist_ok=True)

async def fetch():
    # Load all seeds
    seeds = []
    for src in ["initial_seeds", "runtime", "prior_work"]:
        for f in (CORPUS_DIR / src).glob("*.s"):
            seeds.append(Testcase.from_file(f, source=src))

    # Promote from W$
    top = WCACHE.top_k(CONFIG["pipeline"]["batch_size"])
    promoted = [s for s in seeds if s.id in [x[0] for x in top]]
    selected = promoted[:CONFIG["pipeline"]["batch_size"]]

    # Save to queue
    for s in selected:
        s.save(QUEUE_DIR)
    print(f"[FETCH] → {len(selected)} seeds")

if __name__ == "__main__":
    asyncio.run(fetch())