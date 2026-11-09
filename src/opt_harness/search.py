"""Seeded sampling over mutually exclusive flag categories; never accept raw flags."""

from __future__ import annotations

import random

# Twenty-five explicit GCC flags. Clang uses only the shared subset below.
GCC_GROUPS = (
    ("-O1", "-O2", "-O3", "-Os"),
    ("-funroll-loops", "-fno-unroll-loops"),
    ("-ftree-vectorize", "-fno-tree-vectorize"),
    ("-finline-functions", "-fno-inline-functions"),
    ("-fomit-frame-pointer", "-fno-omit-frame-pointer"),
    ("-fstrict-aliasing", "-fno-strict-aliasing"),
    ("-fpeel-loops", "-fno-peel-loops"),
    ("-funswitch-loops", "-fno-unswitch-loops"),
    ("-fgcse", "-fno-gcse"),
    ("-fipa-cp", "-fno-ipa-cp"),
    ("-fvect-cost-model=cheap", "-fvect-cost-model=dynamic", "-fvect-cost-model=unlimited"),
)
CLANG_GROUPS = (
    GCC_GROUPS[:2]
    + GCC_GROUPS[3:6]
    + (("-fvectorize", "-fno-vectorize"), ("-fslp-vectorize", "-fno-slp-vectorize"))
)
BASELINE = ("-O2",)


def configurations(family: str, budget: int, seed: int) -> list[tuple[str, ...]]:
    if family not in {"gcc", "clang"}:
        raise ValueError("compiler family must be gcc or clang")
    if not 1 <= budget <= 1000:
        raise ValueError("budget must be between 1 and 1000 (including baseline)")
    groups = GCC_GROUPS if family == "gcc" else CLANG_GROUPS
    rng = random.Random(seed)
    result = [BASELINE]
    seen = {BASELINE}
    while len(result) < budget:
        flags = (rng.choice(groups[0]),) + tuple(
            flag for group in groups[1:] if (flag := rng.choice((None, *group))) is not None
        )
        if flags not in seen:
            seen.add(flags)
            result.append(flags)
    return result
