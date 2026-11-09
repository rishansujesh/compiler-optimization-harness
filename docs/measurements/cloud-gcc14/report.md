# Compiler optimization experiment

Compiler: `gcc (Debian 14.2.0-19) 14.2.0`

Timings are serial, warmed, randomized by round, and checksum-validated against -O0.
Speedups are exploratory observations, not statistical significance claims.

| Workload | ID | Median (ms) | MAD (ms) | Speedup vs -O2 | Flags |
|---|---:|---:|---:|---:|---|
| gemm | 0 | 57.559 | 1.852 | 1.000x | `-O2` |
| gemm | 1 | 123.709 | 5.464 | 0.465x | `-O1 -fno-tree-vectorize -finline-functions -fno-unswitch-loops -fno-ipa-cp` |
| gemm | 2 | 122.053 | 6.121 | 0.472x | `-Os -fno-peel-loops -fno-unswitch-loops -fno-ipa-cp -fvect-cost-model=cheap` |
| gemm | 3 | 123.507 | 2.162 | 0.466x | `-Os -ftree-vectorize -fno-inline-functions -fomit-frame-pointer -fno-unswitch-loops -fgcse -fipa-cp -fvect-cost-model=dynamic` |
| gemm | 4 | 58.782 | 2.181 | 0.979x | `-O2 -ftree-vectorize -fstrict-aliasing -funswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| gemm | 5 | 59.369 | 4.306 | 0.970x | `-O1 -fno-unroll-loops -ftree-vectorize -fno-inline-functions -fstrict-aliasing -fno-unswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| gemm | 6 | 60.399 | 3.161 | 0.953x | `-O2 -fno-unroll-loops -fno-omit-frame-pointer -fpeel-loops -fvect-cost-model=unlimited` |
| gemm | 7 | 131.515 | 5.087 | 0.438x | `-O3 -funroll-loops -fno-tree-vectorize -finline-functions -fstrict-aliasing -fpeel-loops -fno-gcse -fipa-cp` |
| fft | 0 | 25.185 | 1.487 | 1.000x | `-O2` |
| fft | 1 | 27.775 | 0.730 | 0.907x | `-O1 -fno-tree-vectorize -finline-functions -fno-unswitch-loops -fno-ipa-cp` |
| fft | 2 | 45.420 | 1.798 | 0.554x | `-Os -fno-peel-loops -fno-unswitch-loops -fno-ipa-cp -fvect-cost-model=cheap` |
| fft | 3 | 47.878 | 2.127 | 0.526x | `-Os -ftree-vectorize -fno-inline-functions -fomit-frame-pointer -fno-unswitch-loops -fgcse -fipa-cp -fvect-cost-model=dynamic` |
| fft | 4 | 29.280 | 3.619 | 0.860x | `-O2 -ftree-vectorize -fstrict-aliasing -funswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| fft | 5 | 26.643 | 1.528 | 0.945x | `-O1 -fno-unroll-loops -ftree-vectorize -fno-inline-functions -fstrict-aliasing -fno-unswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| fft | 6 | 27.694 | 4.759 | 0.909x | `-O2 -fno-unroll-loops -fno-omit-frame-pointer -fpeel-loops -fvect-cost-model=unlimited` |
| fft | 7 | 25.126 | 1.146 | 1.002x | `-O3 -funroll-loops -fno-tree-vectorize -finline-functions -fstrict-aliasing -fpeel-loops -fno-gcse -fipa-cp` |
| ray | 0 | 26.923 | 1.991 | 1.000x | `-O2` |
| ray | 1 | 27.513 | 1.071 | 0.979x | `-O1 -fno-tree-vectorize -finline-functions -fno-unswitch-loops -fno-ipa-cp` |
| ray | 2 | 59.281 | 2.778 | 0.454x | `-Os -fno-peel-loops -fno-unswitch-loops -fno-ipa-cp -fvect-cost-model=cheap` |
| ray | 3 | 56.390 | 0.683 | 0.477x | `-Os -ftree-vectorize -fno-inline-functions -fomit-frame-pointer -fno-unswitch-loops -fgcse -fipa-cp -fvect-cost-model=dynamic` |
| ray | 4 | 25.861 | 0.805 | 1.041x | `-O2 -ftree-vectorize -fstrict-aliasing -funswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| ray | 5 | 26.027 | 1.600 | 1.034x | `-O1 -fno-unroll-loops -ftree-vectorize -fno-inline-functions -fstrict-aliasing -fno-unswitch-loops -fgcse -fno-ipa-cp -fvect-cost-model=dynamic` |
| ray | 6 | 26.142 | 0.643 | 1.030x | `-O2 -fno-unroll-loops -fno-omit-frame-pointer -fpeel-loops -fvect-cost-model=unlimited` |
| ray | 7 | 27.296 | 1.581 | 0.986x | `-O3 -funroll-loops -fno-tree-vectorize -finline-functions -fstrict-aliasing -fpeel-loops -fno-gcse -fipa-cp` |
