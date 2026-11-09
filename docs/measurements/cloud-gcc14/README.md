# Example cloud experiment

Source revision: `26ee56bb551ec806c10d20fb8408cccaccb60aed`. Run on 2026-11-09 with GCC 14.2.0 in a shared Linux cloud environment. This is an example report with genuine raw samples, not a portable performance claim. No other tests, benchmarks or compilation tasks from this chat ran during measurement. Host activity and CPU frequency were uncontrolled; no affinity was requested.

```sh
opt-harness --compiler gcc --budget 8 --runs 7 --warmups 2 --jobs 2 \
  --target-seconds 0.05 --output docs/measurements/cloud-gcc14
```

See [report.md](report.md), [results.csv](results.csv), and [results.json](results.json). The latter retains complete source hashes, compiler commands, environment and settings. Temporary executable paths are provenance only. Search winners need confirmation on a separate run; no candidate is promoted automatically.
