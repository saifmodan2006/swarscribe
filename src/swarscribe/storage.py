"""Atomic UTF-8 JSON persistence for local state."""

import json
import os
import tempfile
from pathlib import Path


def write_json(path: str | Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False,
                                     dir=path.parent, prefix=f".{path.name}.") as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
