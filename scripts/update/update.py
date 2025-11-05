# scripts/5_update.py
from utils.wcache import WeightCache
import yaml, shutil
from pathlib import Path

CONFIG = yaml.safe_load(Path("../config.yaml").read_text())
WCACHE = WeightCache(Path("../wcache.json"), CONFIG["wcache"])
RUNTIME_CORPUS = Path("../corpus/runtime")
RUNTIME_CORPUS.mkdir(exist_ok=True)

def update():
    top = WCACHE.top_k(5)
    for tc_id, w in top:
        src = Path("../queue_mutate") / f"{tc_id}.s"
        if src.exists() and w > CONFIG["wcache"]["promote_threshold"]:
            dst = RUNTIME_CORPUS / f"{tc_id}_{w:.3f}.s"
            shutil.copy(src, dst)
    print(f"[UPDATE] → {len(top)} seeds promoted")

if __name__ == "__main__":
    update()