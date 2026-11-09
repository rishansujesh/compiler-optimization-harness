"""Bound resource use and terminate the complete process group on timeout."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Limits:
    timeout: float = 15.0
    memory_mb: int = 1024
    file_mb: int = 16

    def __post_init__(self) -> None:
        import math

        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if self.memory_mb < 64 or self.file_mb < 1:
            raise ValueError("memory must be >= 64 MiB and file limit >= 1 MiB")


@dataclass
class ProcessResult:
    argv: list[str]
    returncode: int
    elapsed_seconds: float
    stdout: str
    stderr: str
    timed_out: bool

    def to_dict(self) -> dict:
        return asdict(self)


def run(argv: list[str], limits: Limits, cwd: Path | None = None) -> ProcessResult:
    if sys.platform != "linux":
        raise RuntimeError("resource isolation currently requires Linux")
    if not argv:
        raise ValueError("empty command")
    launcher = Path(__file__).with_name("limits.py")
    command = [
        sys.executable,
        str(launcher),
        str(limits.memory_mb),
        str(limits.timeout),
        str(limits.file_mb),
        *map(str, argv),
    ]
    # Files avoid unbounded communicate() buffers. RLIMIT_FSIZE caps child output.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        start = time.perf_counter()
        process = subprocess.Popen(
            command,
            stdout=out,
            stderr=err,
            cwd=cwd,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
        )
        timed_out = False
        try:
            try:
                process.wait(timeout=limits.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            # Also remove descendants left behind by an exited group leader.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        elapsed = time.perf_counter() - start
        out.seek(0)
        err.seek(0)
        return ProcessResult(
            list(map(str, argv)),
            process.returncode,
            elapsed,
            out.read(65536).decode(errors="replace"),
            err.read(65536).decode(errors="replace"),
            timed_out,
        )
