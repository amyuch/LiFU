import subprocess
from pathlib import Path
import logging
import re

log = logging.getLogger("asm_util")

# RISC-V specific constants
RISC_V_INSTRUCTION_SIZE = 4  # 4 bytes per instruction (32-bit)
RISC_V_OPCODES = {
    "add", "addi", "sub", "lw", "sw", "beq", "bne", "jal", "jr",  # Common opcodes
    "and", "andi", "or", "ori", "xor", "xori", "sll", "srl", "sra"
}

def get_instruction_size() -> int:
    """Return RISC-V instruction size in bytes (32-bit = 4 bytes)."""
    return RISC_V_INSTRUCTION_SIZE

def assemble(asm_path: Path, bin_path: Path) -> bool:
    """Assemble RISC-V assembly to binary using toolchain (unchanged but validated)."""
    try:
        obj_path = bin_path.with_suffix(".o")
        # Use rv64gc ISA (general-purpose with compressed instructions)
        result = subprocess.run(
            ["riscv64-unknown-elf-as", "-march=rv64gc", str(asm_path), "-o", str(obj_path)],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract raw binary (strip ELF headers)
        result = subprocess.run(
            ["riscv64-unknown-elf-objcopy", "-O", "binary", str(obj_path), str(bin_path)],
            capture_output=True,
            text=True,
            check=True
        )
        obj_path.unlink(missing_ok=True)
        return bin_path.exists() and bin_path.stat().st_size > 0
    except subprocess.CalledProcessError as e:
        log.error(f"Assembly failed: {e.stderr}")
        return False
    except Exception as e:
        log.error(f"Assembly error: {str(e)}")
        return False

def disassemble(bin_path: Path, asm_path: Path) -> bool:
    """Disassemble binary to RISC-V assembly, filtering invalid instructions."""
    try:
        result = subprocess.run(
            ["riscv64-unknown-elf-objdump", "-D", "-b", "binary", 
             "-m", "riscv:rv64", "--no-show-raw-insn", str(bin_path)],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract valid instructions (filter out addresses and invalid entries)
        instructions = []
        for line in result.stdout.splitlines():
            if ":\t" in line:
                parts = line.split("\t")[1:]  # Skip address (e.g., "00000000:")
                instr = parts[-1].strip()
                # Check if instruction contains a valid opcode
                if any(op in instr for op in RISC_V_OPCODES) and "invalid" not in instr:
                    instructions.append(instr)

        if instructions:
            asm_path.write_text("\n".join(instructions))
            return True
        log.warning(f"No valid instructions found in {bin_path}")
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"Disassembly failed: {e.stderr}")
        return False
    except Exception as e:
        log.error(f"Disassembly error: {str(e)}")
        return False

def parse_instruction(line: str) -> tuple[str, list[str]]:
    """Parse a RISC-V instruction line into (opcode, operands)."""
    line = line.strip()
    if not line or line.startswith("#"):
        return ("", [])  # Skip comments/empty lines
    match = re.match(r"^(\w+)\s+(.*)$", line)
    if not match:
        return ("", [])  # Invalid format
    opcode = match.group(1)
    operands = [op.strip() for op in match.group(2).split(",")] if match.group(2) else []
    return (opcode, operands)

def is_valid_instruction(line: str) -> bool:
    """Check if a line is a valid RISC-V instruction (syntax + opcode)."""
    opcode, operands = parse_instruction(line)
    if opcode not in RISC_V_OPCODES:
        return False
    # Basic operand count checks (simplified)
    if opcode in {"add", "sub", "and", "or", "xor"}:  # R-type (3 operands: rd, rs1, rs2)
        return len(operands) == 3
    elif opcode in {"addi", "andi", "ori", "xori", "lw"}:  # I-type (3 operands: rd, rs1, imm)
        return len(operands) == 3
    elif opcode in {"sw"}:  # S-type (3 operands: rs2, rs1, imm)
        return len(operands) == 3
    elif opcode in {"beq", "bne"}:  # B-type (3 operands: rs1, rs2, label)
        return len(operands) == 3
    elif opcode in {"jal"}:  # UJ-type (2 operands: rd, label)
        return len(operands) == 2
    elif opcode in {"jr"}:  # J-type (1 operand: rs1)
        return len(operands) == 1
    return True  # Allow unhandled opcodes but with valid structure