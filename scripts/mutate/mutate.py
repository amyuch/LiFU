# scripts/mutate/mutate.py
"""
Mutate Stage: Apply hybrid mutators to seeds from queue_fetch/
Output: queue_mutate/*.s
"""

import sys
from pathlib import Path

# === Add project root ===
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.models import Testcase
from scripts.mutate.mutator.binary import BinaryMutator
from scripts.mutate.mutator.gen import LLMMutator

# === Paths ===
IN_DIR = PROJECT_ROOT / "queue_fetch"
OUT_DIR = PROJECT_ROOT / "queue_mutate"
OUT_DIR.mkdir(exist_ok=True)

def mutate():
    print(f"[MUTATE] Reading from: {IN_DIR}")
    if not list(IN_DIR.glob("*.s")):
        print("[ERROR] No seeds in queue_fetch!")
        return

    mutators = [
        BinaryMutator(mutations_per_seed=3),
        LLMMutator(),
    ]

    all_mutants = []
    for seed_file in IN_DIR.glob("*.s"):
        seed = Testcase.from_file(seed_file)
        print(f"  [SEED] {seed.id[:8]}... ({seed.source})")

        for mutator in mutators:
            try:
                mutants = mutator.mutate(seed)
                for m in mutants:
                    out_path = m.save(OUT_DIR)
                    print(f"    [MUTANT] {m.id[:8]}... → {out_path.name} ({m.source})")
                all_mutants.extend(mutants)
            except Exception as e:
                print(f"    [ERROR] {mutator.__class__.__name__}: {e}")

    print(f"[MUTATE] Generated {len(all_mutants)} mutants → queue_mutate/")

if __name__ == "__main__":
    mutate()