"""Single-threaded child launcher: avoids preexec_fn in a threaded parent."""
import math
import os
import resource
import sys


def main() -> None:
    memory_mb, cpu_seconds, file_mb = map(float, sys.argv[1:4])
    resource.setrlimit(resource.RLIMIT_AS, (int(memory_mb * 2**20),) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (max(1, math.ceil(cpu_seconds)),) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (int(file_mb * 2**20),) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.execvp(sys.argv[4], sys.argv[4:])


if __name__ == "__main__":
    main()
