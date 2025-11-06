# # utils/property_generator.py
# import asyncio
# from typing import List
# from utils.llm import llm_generate_property

# class PropertyGenerator:
#     """LLM-grounded assertion synthesis with validation."""
    
#     def __init__(self):
#         self.templates = [
#             "Synthesize SVA for {desc} at cycle {cycle}",
#             "Assert: {reg} holds value {val} after {inst}"
#         ]

#     async def generate(self, mismatch_desc: str) -> str:
#         prompt = f"""
# Hardware mismatch detected:
# {mismatch_desc}

# Generate a **minimal, correct SystemVerilog assertion** to catch this.
# Use only observed signals. No speculation.
# """
#         try:
#             prop = await llm_generate_property(prompt)
#             return self._validate(prop)
#         except:
#             return "// LLM failed to generate valid property"

#     def _validate(self, prop: str) -> str:
#         # Basic syntax check
#         if "assert property" not in prop and "assume property" not in prop:
#             return "// Invalid: missing assert/assume"
#         return prop.strip()
# scripts/analyse/property_generator.py
from utils.llm import call
from typing import List

SYSTEM_PROMPT = """
You are a SystemVerilog assertion expert for processor RTL verification.
Generate minimal, synthesizable, commented assertions.
Use only observable signals. Include disable iff (reset).
"""

class PropertyGenerator:
    def __init__(self):
        pass

    async def from_mismatch(self, mismatch: str, cycle: int, dut: str = "DUT") -> str:
        user_prompt = f"""
Generate a SystemVerilog assertion to catch this mismatch:
- DUT: {dut}
- Cycle: {cycle}
- Details: {mismatch}

Requirements:
- Use @(posedge clk)
- Include disable iff (!reset_n)
- Be synthesizable
- Add inline comments
"""
        result, _, _ = call(user_prompt, system_prompt=SYSTEM_PROMPT)
        return result