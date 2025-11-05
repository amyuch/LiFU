# utils/checker.py
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class Mismatch:
    cycle: int
    type: str  # "pc", "reg", "mem", "timing"
    expected: Any
    actual: Any
    dut_id: int

class DifferentialChecker:
    """Live checker: compares DUT vs ISS golden trace."""
    
    def __init__(self, tolerance_cycles: int = 5):
        self.tolerance = tolerance_cycles
        self.mismatches: List[Mismatch] = []

    def load_iss_trace(self, log_path: Path) -> List[Dict]:
        data = json.loads(log_path.read_text())
        return data.get("trace", [])

    def compare(self, iss_trace: List[Dict], dut_traces: List[List[Dict]], dut_ids: List[int]):
        self.mismatches.clear()
        min_len = min(len(iss_trace), min(len(d) for d in dut_traces))

        for cycle in range(min_len):
            iss_state = iss_trace[cycle]
            for dut_id, dut_trace in zip(dut_ids, dut_traces):
                dut_state = dut_trace[cycle]

                # PC check
                if iss_state.get("pc") != dut_state.get("pc"):
                    self.mismatches.append(Mismatch(
                        cycle=cycle, type="pc", expected=iss_state["pc"],
                        actual=dut_state["pc"], dut_id=dut_id
                    ))

                # Register divergence
                for reg in ["x0", "x1", "x2", "x3"]:
                    if iss_state.get(reg) != dut_state.get(reg):
                        self.mismatches.append(Mismatch(
                            cycle=cycle, type="reg", expected=iss_state[reg],
                            actual=dut_state[reg], dut_id=dut_id
                        ))

        return self.mismatches