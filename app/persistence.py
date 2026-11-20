"""Replace a settings file only after a complete, flushed temporary write."""
import json
import os
import pathlib
import tempfile


def atomic_bytes(path, content):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, content):
    atomic_bytes(path, json.dumps(content, ensure_ascii=False, allow_nan=False, indent=2).encode('utf-8'))
