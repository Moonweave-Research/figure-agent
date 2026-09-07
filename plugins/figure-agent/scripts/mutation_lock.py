"""One kernel-owned mutation lock shared by MCP and candidate apply."""

import fcntl
import json
import os
import time
from contextlib import contextmanager


@contextmanager
def hold(path, operation):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        os.ftruncate(fd, 0)
        os.write(
            fd,
            json.dumps(
                {"operation": operation, "created_at": time.time(), "pid": os.getpid()},
                sort_keys=True,
            ).encode("utf-8"),
        )
        yield True
    finally:
        # Keep a stable inode: unlinking could split waiters across two locks.
        os.close(fd)
