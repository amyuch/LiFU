# utils/models.py
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import hashlib

@dataclass
class Testcase:
    id: str
    code: str
    source: str
    path: Path
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        self.metadata = self.metadata or {}

    @classmethod
    def from_file(cls, path: Path, source: str = "file"):
        code = path.read_text()
        id_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
        return cls(id=id_hash, code=code, source=source, path=path)

    def save(self, dir: Path):
        out = dir / f"{self.id}.s"
        out.write_text(self.code)
        return out