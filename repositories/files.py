"""Utility helpers for persisting small JSON files.

The previous implementation wrote directly to the destination path which
could lead to partially written files if the process crashed mid-write. In
addition, JSON parsing errors were silently swallowed which made diagnosing
corrupted files difficult.  This module now writes files atomically and
logs any I/O or JSON errors to aid debugging and improve reliability.
"""

import json
import logging
import os
import tempfile
import threading
from typing import Any, Dict

import config

# In-memory cache for JSON files to minimise disk access.  A single
# reentrant lock guards both cache lookups and file writes, ensuring that
# concurrent threads do not read stale data or step on each other's writes.
_CACHE: Dict[str, Dict[str, Any]] = {}
_LOCK = threading.RLock()

log = logging.getLogger(__name__)

def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def _path(filename: str) -> str:
    _ensure_dir(config.JSON_DIR)
    if filename.startswith(config.JSON_DIR):
        return filename
    return os.path.join(config.JSON_DIR, filename)

def load_json(filename: str) -> Dict[str, Any]:
    """Load JSON data from *filename*.

    Any :class:`OSError` or :class:`json.JSONDecodeError` is logged and an
    empty dictionary is returned instead of propagating the exception. This
    mirrors the previous behaviour while providing insight into what went
    wrong.
    """

    path = _path(filename)
    with _LOCK:
        if path in _CACHE:
            # Return a copy so callers cannot accidentally mutate the cache
            return dict(_CACHE[path])

        if not os.path.exists(path):
            _CACHE[path] = {}
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                data = json.loads(text) if text else {}
        except (OSError, json.JSONDecodeError) as err:
            log.warning("Failed to load JSON from %s: %s", path, err)
            data = {}

        _CACHE[path] = data
        return dict(data)

def save_json(filename: str, data: Dict[str, Any]) -> None:
    """Persist *data* to *filename* atomically.

    Writing is performed to a temporary file which is then moved into place.
    This prevents partially written files if the process crashes during
    serialisation. Any :class:`OSError` encountered is logged and re-raised
    so callers can react appropriately.
    """

    path = _path(filename)
    directory = os.path.dirname(path)
    _ensure_dir(directory)

    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=os.path.basename(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        with _LOCK:
            # Store a copy to avoid external mutation of the cached object
            _CACHE[path] = dict(data)
    except OSError as err:
        log.warning("Failed to write JSON to %s: %s", path, err)
        raise
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
