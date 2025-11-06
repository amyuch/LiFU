.global _start
_start:
    addi x1, x0, 1
    addi x2, x0, 2
    fence.i
    add  x3, x1, x2
    lw   x4, 0(x3)
    ebreak

.data
    .word 0x12345678