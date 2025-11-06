# utils/arbiter.py
from typing import List, Tuple
from utils.wcache import WeightCache
from utils.models import Testcase
from pathlib import Path

class Arbiter:
    """Final seed ranking and feedback injector."""
    
    def __init__(self, wcache: WeightCache, threshold: float = 0.5):
        self.wcache = wcache
        self.threshold = threshold

    def rank_and_inject(self, candidates: List[Testcase], runtime_dir: Path) -> List[Path]:
        promoted = []
        for tc in candidates:
            w = self.wcache.entries.get(tc.id, 0.0)
            if w >= self.threshold:
                dst = runtime_dir / f"{tc.id}_w{w:.3f}.s"
                dst.write_text(tc.code)
                promoted.append(dst)
        print(f"[ARBITER] Promoted {len(promoted)} seeds")
        return promoted