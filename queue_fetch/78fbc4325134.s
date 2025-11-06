.global _start
_start:
    lui x1, 0x100
    sw x1, 0(x0)
    lw x2, 0(x0)
    ebreak