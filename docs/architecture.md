# Experiment pipeline

1. Validate settings and identify the compiler through its version output.
2. Generate a unique, seeded list of configurations. Mutually exclusive categories prevent contradictory flags. `-O2` is always candidate zero. Compiler-version-specific unsupported flags become recorded compilation failures.
3. Compile an `-O0` reference and every candidate for each workload in a temporary directory. A thread pool bounds simultaneous compiler processes. Each runs in its own process group through a single-threaded Python resource-limit launcher, avoiding unsafe `preexec_fn` use in a threaded parent.
4. Wait for all compilation to finish. Optionally pin the current thread and its subsequent children to one allowed CPU, restoring the original affinity in a `finally` block.
5. Calibrate repetition count from a baseline run, calculate the reference checksum, validate and warm each candidate, then time candidates in shuffled rounds.
6. Persist all samples, commands, compiler diagnostics and metadata in JSON; derive CSV and Markdown summaries. Temporary executables are removed automatically.

The process runner caps each captured output read at 64 KiB and uses bounded temporary output files. It kills the process group in cleanup even if the group leader exits normally, then reaps the direct child. RLIMIT_AS, RLIMIT_CPU and RLIMIT_FSIZE supplement the wall-clock timeout. This is resource control for trusted workloads, not a security isolation boundary.

Timing comes from the workload's monotonic clock, excluding Python process-launch overhead. A process failure, invalid JSON, non-finite checksum, nonpositive timing or checksum mismatch disqualifies that candidate. A failed baseline suppresses speedup reporting for the workload. A successful candidate must have every requested sample.

The public API is `experiment(...)`, `write_report(...)`, and the `opt-harness` CLI. Result schema version 1 includes environment, settings, and a workload list with per-configuration samples and status. Consumers should tolerate additional fields and treat temporary command paths as provenance, not retained executables.
