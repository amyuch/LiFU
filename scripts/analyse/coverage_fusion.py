# utils/coverage_fusion.py
from typing import Set, Dict
from pathlib import Path
import pickle

class CoverageFusion:
    """Bitmap-based global coverage aggregator."""
    
    def __init__(self, bitmap_path: Path):
        self.bitmap_path = bitmap_path
        self.global_bitmap: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if self.bitmap_path.exists():
            return pickle.loads(self.bitmap_path.read_bytes())
        return set()

    def _save(self):
        self.bitmap_path.write_bytes(pickle.dumps(self.global_bitmap))

    def update(self, local_coverage: Set[str]) -> float:
        prev_size = len(self.global_bitmap)
        self.global_bitmap.update(local_coverage)
        new_size = len(self.global_bitmap)
        delta = (new_size - prev_size) / 1000.0  # normalize
        self._save()
        return delta

    def get_uncoverpoints(self, total_points: Set[str]) -> Set[str]:
        return total_points - self.global_bitmap