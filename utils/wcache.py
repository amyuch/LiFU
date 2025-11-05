# utils/wcache.py
import json
from pathlib import Path
from typing import Dict
from .models import Testcase

class WeightCache:
    def __init__(self, path: Path, config: dict):
        self.path = path
        self.config = config
        self.entries: Dict[str, float] = {}
        self.history: Dict[str, dict] = {}
        self.load()

    def load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.entries = data.get("entries", {})
            self.history = data.get("history", {})

    def save(self):
        data = {"entries": self.entries, "history": self.history}
        self.path.write_text(json.dumps(data, indent=2))

    def update(self, testcase: Testcase, delta_cov: float, bug_score: float, cycles: int):
        novelty = 1.0  # TODO: edit distance
        efficiency = (delta_cov + bug_score) / max(cycles, 1)
        w = (
            self.config["alpha"] * delta_cov +
            self.config["beta"] * bug_score +
            self.config["gamma"] * novelty +
            self.config["delta"] * efficiency
        )
        self.entries[testcase.id] = w
        self.history[testcase.id] = {
            "cov_gain": delta_cov,
            "bug_score": bug_score,
            "w": w,
            "cycles": cycles
        }
        print(f"[W$] {testcase.id} → w={w:.4f}")
        self.save()

    def top_k(self, k: int):
        return sorted(self.entries.items(), key=lambda x: x[1], reverse=True)[:k]