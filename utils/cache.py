import hashlib
import json
import logging
from pathlib import Path
from typing import Any


class DiskCache:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        folder = self.base_dir / namespace
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{digest}.json"

    def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        path = self._path(namespace, key)
        if not path.exists():
            self.logger.debug("Cache miss: %s/%s", namespace, path.name)
            return None
        self.logger.debug("Cache hit: %s/%s", namespace, path.name)
        return json.loads(path.read_text(encoding="utf-8"))

    def set_json(self, namespace: str, key: str, payload: dict[str, Any]) -> None:
        path = self._path(namespace, key)
        self.logger.debug("Cache set: %s/%s", namespace, path.name)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
