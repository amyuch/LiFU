# scripts/2_mutate.py
import asyncio, random
from pathlib import Path
from utils.models import Testcase
import hashlib

IN_DIR = Path("../queue_fetch")
OUT_DIR = Path("../queue_mutate")
OUT_DIR.mkdir(exist_ok=True)

async def binary_mutate(tc: Testcase) -> list[Testcase]:
    mutants = []
    code = tc.code.encode()
    for _ in range(3):
        i = random.randint(0, len(code)-1)
        flipped = code[:i] + bytes([code[i] ^ (1 << random.randint(0,7))]) + code[i+1:]
        try:
            m = Testcase(id="", code=flipped.decode(), source="binary")
            m.id = hashlib.sha256(m.code.encode()).hexdigest()[:12]
            mutants.append(m)
        except:
            pass
    return mutants

async def mutate():
    tasks = []
    for f in IN_DIR.glob("*.s"):
        tc = Testcase.from_file(f)
        tasks.append(binary_mutate(tc))
    results = await asyncio.gather(*tasks)
    for batch in results:
        for m in batch:
            m.save(OUT_DIR)
    print(f"[MUTATE] → {sum(len(b) for b in results)} mutants")

if __name__ == "__main__":
    asyncio.run(mutate())