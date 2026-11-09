# Reproducible measurements

The default search uses 12 configurations, seed 42, two warmups and seven measured invocations per configuration. Each measured invocation repeats the kernel enough times to approach 50 ms at the baseline speed. Calibration uses one initial baseline invocation and is approximate. Raise the target for more stable timings.

For each workload, candidates run in a deterministic shuffled order for each round. This distributes monotonic temperature/frequency drift across configurations, but does not eliminate it. Compilation finishes before measurement begins. Pinning to a CPU reduces migrations; it does not disable frequency scaling, isolate the CPU, or prevent host contention.

Report median and median absolute deviation alongside all samples. A small reported speedup with similar dispersion is inconclusive. Searching many candidates preferentially selects lucky noise; validate winners in a fresh experiment. This implementation does not perform significance tests, confidence intervals, or automatic winner promotion.

Every warmup and timed run is compared with an `-O0` reference at relative tolerance 1e-8 and absolute tolerance 1e-6. Fast-math is intentionally absent. Reference agreement alone can preserve a shared source bug, so tests additionally check GEMM using sums of matrix columns and rows, FFT using Parseval's identity, and ray hits using projection onto the triangle plane.

The three workloads are microbenchmarks, not complete applications. The FFT includes initialization and checksum accumulation in its timed region. GEMM initialization is outside its timed region; matrix multiplication and checksum reduction are inside. Ray timing includes ray construction and hit accumulation. Comparisons are valid within a workload, not across workloads or machines.

Keep the JSON report with the source revision. It records source hashes, compiler version, platform, CPU model, affinity and search settings. It does not record CPU governor, thermal sensors, full system load or microcode version. Capture those separately when making publication-grade claims. CI smoke runs only check functioning, never enforce a performance threshold.
