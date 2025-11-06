.global _start
_start:
    lui x1, 0x100
    sw x1, 0(x0)
    fence.i
    lw x2, 0(x0)
    addi x3, x2, 1
    sw x3, 8(x0)
    fence.i
    lw x4, 8(x0)
    ebreak