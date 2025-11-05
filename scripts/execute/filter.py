# utils/filter.py
import re
from typing import List
from utils.models import Testcase

class LightweightFilter:
    """Pre-execution filter to discard pathological testcases."""
    
    def __init__(self):
        self.max_lines = 200
        self.max_loops = 3
        self.banned_patterns = [
            r"\.inf:",           # infinite loop labels
            r"j\s*\.",           # unconditional jump to self
            r"loop:\s*loop",     # nested infinite
        ]

    def is_valid(self, tc: Testcase) -> bool:
        code = tc.code.lower()
        lines = code.splitlines()

        # 1. Size check
        if len(lines) > self.max_lines:
            return False

        # 2. Loop count
        loop_count = code.count("loop:")
        if loop_count > self.max_loops:
            return False

        # 3. Banned patterns
        if any(re.search(p, code) for p in self.banned_patterns):
            return False

        # 4. Minimal instruction count
        instr = [l for l in lines if l.strip() and not l.startswith("#")]
        if len(instr) < 3:
            return False

        return True

    def filter_batch(self, testcases: List[Testcase]) -> List[Testcase]:
        valid = [tc for tc in testcases if self.is_valid(tc)]
        print(f"[FILTER] {len(testcases)} → {len(valid)} passed")
        return valid