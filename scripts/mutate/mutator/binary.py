# # scripts/mutate/mutator/binary.py
# import random
# import hashlib
# from pathlib import Path
# from utils.models import Testcase
# from utils.asm_util import assemble, disassemble  # Ensure this utility exists

# class BinaryMutator:
#     def __init__(self, mutations_per_seed: int = 3):
#         self.n = mutations_per_seed  # Use config value later

#     def mutate(self, tc: Testcase) -> list[Testcase]:  # Added 'self' parameter
#         mutants = []
        
#         try:
#             # Step 1: Save original assembly to temp file
#             temp_asm = Path(f"temp_{tc.id}.s")
#             temp_asm.write_text(tc.code)
            
#             # Step 2: Assemble to binary
#             temp_bin = Path(f"temp_{tc.id}.bin")
#             if not assemble(temp_asm, temp_bin):
#                 return mutants  # Skip if assembly fails
            
#             # Step 3: Read binary data
#             bin_data = temp_bin.read_bytes()
#             if len(bin_data) == 0:
#                 return mutants
            
#             # Step 4: Generate mutations
#             for i in range(self.n):  # Use class-level mutation count
#                 # Flip a random bit
#                 pos = random.randint(0, len(bin_data) - 1)
#                 flip_bit = 1 << random.randint(0, 7)
#                 mutated_bin = bin_data[:pos] + bytes([bin_data[pos] ^ flip_bit]) + bin_data[pos+1:]
                
#                 # Save mutated binary
#                 mutated_bin_path = Path(f"temp_mut_{tc.id}_{i}.bin")
#                 mutated_bin_path.write_bytes(mutated_bin)
                
#                 # Disassemble back to assembly
#                 mutated_asm_path = Path(f"temp_mut_{tc.id}_{i}.s")
#                 if disassemble(mutated_bin_path, mutated_asm_path):
#                     mutant_code = mutated_asm_path.read_text()
#                     # Validate with lightweight filter before adding
#                     from scripts.execute.filter import LightweightFilter
#                     if LightweightFilter().is_valid(Testcase(id="", code=mutant_code, source="", path=mutated_asm_path)):
#                         mutant_id = hashlib.sha256(mutant_code.encode()).hexdigest()[:12]
#                         mutants.append(Testcase(
#                             id=mutant_id,
#                             code=mutant_code,
#                             source="binary",
#                             path=mutated_asm_path
#                         ))
                
#                 # Cleanup temp files immediately
#                 mutated_bin_path.unlink(missing_ok=True)
#                 mutated_asm_path.unlink(missing_ok=True)
                
#         finally:
#             # Ensure all temp files are cleaned up
#             temp_asm.unlink(missing_ok=True)
#             temp_bin.unlink(missing_ok=True)
            
#         return mutants
# scripts/mutate/mutate.py
import asyncio
import random
import hashlib
from pathlib import Path
from utils.models import Testcase
from scripts.execute.filter import LightweightFilter

# RISC-V 32-bit instruction masks (simplified for RV64GC)
INSTR_MASK = 0xFFFFFFFF  # 32-bit instructions
OPCODE_MASK = 0x7F       # Bits 0-6
FUNCT3_MASK = 0x700      # Bits 12-14 (shift 12)
FUNCT7_MASK = 0xFE000000 # Bits 25-31 (shift 25)
RS1_MASK = 0xF80         # Bits 15-19 (shift 15)
RS2_MASK = 0x1F000       # Bits 20-24 (shift 20)
RD_MASK = 0xF800         # Bits 7-11 (shift 7)

# Termination instructions (preserve these to avoid infinite loops)
TERMINATION_INSTR = {0x00100073}  # ebreak (32-bit encoding)

class BinaryMutator:
    def __init__(self, mutations_per_seed: int = 3):
        self.n = mutations_per_seed
        self.filter = LightweightFilter()
        self.registers = [f"x{i}" for i in range(32)]  # x0-x31

    def _instr_to_bytes(self, instr: int) -> bytes:
        """Convert 32-bit instruction to little-endian bytes"""
        return instr.to_bytes(4, byteorder='little')

    def _bytes_to_instr(self, b: bytes) -> int:
        """Convert 4-byte little-endian to 32-bit instruction"""
        return int.from_bytes(b, byteorder='little') & INSTR_MASK

    def _mutate_opcode(self, instr: int) -> int:
        """Mutate opcode/funct3/funct7 to related instructions"""
        if instr in TERMINATION_INSTR:
            return instr  # Preserve termination
        
        opcode = instr & OPCODE_MASK
        funct3 = (instr & FUNCT3_MASK) >> 12
        funct7 = (instr & FUNCT7_MASK) >> 25

        # Flip 1-2 bits in opcode (keep within valid ranges)
        for _ in range(random.randint(1, 2)):
            bit = random.randint(0, 6)  # Opcode is 7 bits
            opcode ^= (1 << bit)
        
        # Flip 1 bit in funct3 if present (for ALU instructions)
        if funct3 != 0:
            bit = random.randint(0, 2)
            funct3 ^= (1 << bit)
        
        # Flip 1 bit in funct7 if present (for R-type)
        if funct7 != 0:
            bit = random.randint(0, 6)
            funct7 ^= (1 << bit)
        
        # Reassemble instruction
        new_instr = instr & ~(OPCODE_MASK | FUNCT3_MASK | FUNCT7_MASK)
        new_instr |= opcode
        new_instr |= (funct3 << 12)
        new_instr |= (funct7 << 25)
        return new_instr

    def _mutate_immediate(self, instr: int) -> int:
        """Mutate immediate fields (scale/shift instead of random flip)"""
        opcode = instr & OPCODE_MASK
        new_instr = instr

        # I-type (imm[11:0]): bits 20-31
        if opcode in (0x13, 0x03, 0x67):  # addi, lw, jalr
            imm = (instr >> 20) & 0xFFF
            imm = max(-2048, min(2047, imm * random.choice([-2, -1, 1, 2])))  # Scale
            new_instr = (new_instr & 0xFFFFF) | ((imm & 0xFFF) << 20)
        
        # S-type (imm[11:5] + imm[4:0]): bits 25-31 and 7-11
        elif opcode in (0x23,):  # sw
            imm_high = (instr >> 25) & 0x7F
            imm_low = (instr >> 7) & 0x1F
            imm = (imm_high << 5) | imm_low
            imm = max(-2048, min(2047, imm * random.choice([-2, -1, 1, 2])))
            new_instr = (new_instr & 0x1F80F) | (((imm >> 5) & 0x7F) << 25) | (((imm & 0x1F) << 7))
        
        # B-type (imm[12,10:5,4:1,11]): sign-extended branch offset
        elif opcode in (0x63,):  # beq, bne, etc.
            imm = ((instr >> 12) & 0x1) << 11  # bit 12
            imm |= ((instr >> 25) & 0x3F) << 5  # bits 10:5
            imm |= ((instr >> 8) & 0xF) << 1    # bits 4:1
            imm |= ((instr >> 7) & 0x1) << 12   # bit 11 (sign)
            imm = (imm >> 1)  # B-type is 13-bit signed (scaled by 2)
            imm = max(-4096, min(4094, imm * random.choice([-2, -1, 1, 2])))
            imm <<= 1  # Re-scale
            new_instr = (new_instr & 0x800F) | \
                        (((imm >> 11) & 0x1) << 12) | \
                        (((imm >> 5) & 0x3F) << 25) | \
                        (((imm >> 1) & 0xF) << 8) | \
                        (((imm >> 12) & 0x1) << 7)
        
        return new_instr

    def _mutate_register(self, instr: int) -> int:
        """Swap registers with valid alternatives (avoid x0 for writes)"""
        opcode = instr & OPCODE_MASK
        new_instr = instr

        # Mutate RS1 (source register 1)
        if (opcode & 0x3F) not in (0x23, 0x63):  # Most instructions use RS1
            rs1 = (instr & RS1_MASK) >> 15
            new_rs1 = random.choice(range(32))
            new_instr = (new_instr & ~RS1_MASK) | (new_rs1 << 15)
        
        # Mutate RS2 (source register 2)
        if opcode in (0x33, 0x23, 0x63):  # R-type, S-type, B-type
            rs2 = (instr & RS2_MASK) >> 20
            new_rs2 = random.choice(range(32))
            new_instr = (new_instr & ~RS2_MASK) | (new_rs2 << 20)
        
        # Mutate RD (destination register) - avoid x0 for writes
        if opcode in (0x33, 0x13, 0x3, 0x6F, 0x17):  # Write to RD
            rd = (instr & RD_MASK) >> 7
            new_rd = random.choice([x for x in range(32) if x != 0])  # Not x0
            new_instr = (new_instr & ~RD_MASK) | (new_rd << 7)
        
        return new_instr

    def _mutate_instruction(self, instr: int) -> int:
        """Choose a mutation operator based on instruction type"""
        if instr in TERMINATION_INSTR:
            return instr  # Never mutate termination instructions
        
        mutators = [
            self._mutate_opcode,
            self._mutate_immediate,
            self._mutate_register
        ]
        return random.choice(mutators)(instr)

    def mutate(self, tc: Testcase) -> list[Testcase]:
        """Mutate testcase by modifying RISC-V instructions"""
        mutants = []
        code_bytes = tc.code.encode('utf-8', errors='ignore')

        # Validate input is multiple of 4 bytes (RISC-V instructions)
        if len(code_bytes) % 4 != 0:
            return mutants

        # Split into 32-bit instructions
        instr_count = len(code_bytes) // 4
        instructions = [
            self._bytes_to_instr(code_bytes[i*4 : (i+1)*4])
            for i in range(instr_count)
        ]

        for _ in range(self.n):
            # Copy and mutate a random instruction
            mutated_instrs = instructions.copy()
            idx = random.randint(0, instr_count - 1)
            mutated_instrs[idx] = self._mutate_instruction(mutated_instrs[idx])

            # Convert back to bytes and decode
            mutated_bytes = b"".join([
                self._instr_to_bytes(ins) for ins in mutated_instrs
            ])
            try:
                mutated_code = mutated_bytes.decode()
                # Validate with lightweight filter
                mutant = Testcase(
                    id="",
                    code=mutated_code,
                    source="binary_isa",
                    path=tc.path
                )
                if self.filter.is_valid(mutant):
                    mutant.id = hashlib.sha256(mutated_code.encode()).hexdigest()[:12]
                    mutants.append(mutant)
            except UnicodeDecodeError:
                continue  # Skip invalid UTF-8
        
        return mutants
