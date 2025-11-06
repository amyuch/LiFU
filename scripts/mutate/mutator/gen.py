# scripts/mutate/mutator/gen.py
from utils.llm import call
from utils.models import Testcase
from pathlib import Path
import hashlib
import re
from typing import Optional

class LLMMutator:
    def __init__(self):
        self.system_prompt = """You are a RISC-V assembly fuzzer. Generate valid, novel, short tests.
Your response should contain the assembly code between ```assembly or ```asm tags."""

    def _extract_code(self, response: str) -> Optional[str]:
        """Extract assembly code from LLM response."""
        # Try both assembly and asm tags
        patterns = [
            r'```assembly\n(.*?)\n```',
            r'```asm\n(.*?)\n```',
            r'```Assembly\n(.*?)\n```',
            r'```ASM\n(.*?)\n```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no code blocks found, return None
        return None

    def mutate(self, seed: Testcase) -> list[Testcase]:
        user_prompt = f"""Mutate this RISC-V test to increase coverage:

{seed.code}

Requirements:
- RV64GC
- .global _start
- No infinite loops
- Add fence.i if needed
- Target pipeline hazards or cache
"""
        
        result, _, _ = call(user_prompt, system_prompt=self.system_prompt)
        
        # Extract assembly code from response
        code = self._extract_code(result)
        
        if not code:
            print(f"Warning: No assembly code found in LLM response")
            return []
            
        # Generate unique ID
        mutant_id = hashlib.sha256(code.encode()).hexdigest()[:12]
        
        # Create and return new test case
        return [Testcase(id=mutant_id, code=code, source="llm", path=Path(""))]

    def batch_mutate(self, seeds: list[Testcase]) -> list[Testcase]:
        """Mutate multiple test cases."""
        mutants = []
        for seed in seeds:
            mutants.extend(self.mutate(seed))
        return mutants

# from utils.models import Testcase
# import random
# import hashlib
# from pathlib import Path

# class LLMMutator:
#     """Stub for LLM-based mutation (will use utils.llm.call later)."""
    
#     def mutate(self, seed: Testcase) -> list[Testcase]:
#         # Simulate LLM generating a new test
#         templates = [
#             f"{seed.code}\n# LLM: added hazard\nfence.i\naddi x10, x10, 1",
#             f"{seed.code}\n# LLM: cache stress\nsfence.vma\nlw x5, 0(x6)",
#         ]
#         code = random.choice(templates)
#         mutant_id = hashlib.sha256(code.encode()).hexdigest()[:12]
#         return [Testcase(id=mutant_id, code=code, source="llm", path=Path(""))]