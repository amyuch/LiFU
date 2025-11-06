.global _start
_start:
    addi x1, x0, 1
    addi x2, x0, 2
    add  x3, x1, x2
    ebreak
# LLM: added hazard
fence.i
addi x10, x10, 1