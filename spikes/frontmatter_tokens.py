"""Frontmatter schema spike (issue #1).

Measures the token cost that the `mysk:` block adds to a SKILL.md across three
key-naming variants: verbose, abbreviated, and hybrid. The lifecycle state is a
single mutually-exclusive `state` key (always written explicitly); provenance
adds a source URL and a modified flag for imported skills.

Run with:
    uv run --with tiktoken python spikes/frontmatter_tokens.py

The numbers inform ADR-0003 (agreed mysk-block key names).
"""

from __future__ import annotations

import tiktoken

# A representative worst case: an imported skill currently under evaluation.
# This block carries the maximum number of mysk keys (lifecycle + provenance).
SOURCE_URL = "https://github.com/owner/repo/tree/main/skills/some-skill"

VARIANTS: dict[str, str] = {
    "verbose": (
        f"mysk:\n  state: experimental\n  source: {SOURCE_URL}\n  modified: true\n"
    ),
    "abbreviated": (f"mysk:\n  st: experimental\n  src: {SOURCE_URL}\n  mod: true\n"),
    "hybrid": (
        f"mysk:\n  state: experimental\n  src: {SOURCE_URL}\n  modified: true\n"
    ),
}

# Encodings to report. o200k_base backs current GPT-4o/o-series models and is
# the closest public proxy for the agents that read these skills; cl100k_base
# is included as a second data point.
ENCODINGS = ["o200k_base", "cl100k_base"]

# Roughly the number of managed skills a heavy user accumulates; used to show
# the aggregate cost an agent pays when scanning every SKILL.md.
SKILL_COUNT = 100


def main() -> None:
    encoders = {name: tiktoken.get_encoding(name) for name in ENCODINGS}

    header = f"{'variant':<14}" + "".join(f"{enc:>14}" for enc in ENCODINGS)
    print(header)
    print("-" * len(header))

    baseline: dict[str, int] = {}
    rows: dict[str, dict[str, int]] = {}
    for variant, block in VARIANTS.items():
        counts = {enc: len(encoders[enc].encode(block)) for enc in ENCODINGS}
        rows[variant] = counts
        if variant == "verbose":
            baseline = counts
        line = f"{variant:<14}" + "".join(f"{counts[enc]:>14}" for enc in ENCODINGS)
        print(line)

    print()
    print(f"Savings vs verbose (per skill, then x{SKILL_COUNT} skills):")
    for variant, counts in rows.items():
        if variant == "verbose":
            continue
        for enc in ENCODINGS:
            saved = baseline[enc] - counts[enc]
            print(
                f"  {variant:<12} {enc:<12} "
                f"-{saved} tok/skill  (-{saved * SKILL_COUNT} across {SKILL_COUNT})"
            )

    # Isolate the keys so the URL noise doesn't mask differences. If a key name
    # and its abbreviation cost the same number of tokens, abbreviating buys
    # nothing but lost readability.
    print()
    print("Per-key token cost (key name alone):")
    enc = encoders["o200k_base"]
    for full, short in [("state", "st"), ("source", "src"), ("modified", "mod")]:
        print(
            f"  {full:<10} {len(enc.encode(full))} tok   "
            f"vs  {short:<5} {len(enc.encode(short))} tok"
        )

    # The common case: a self-authored skill with no provenance. Only the
    # lifecycle state is present, and it is always written explicitly.
    print()
    print("Self-authored cases (o200k_base):")
    cases = {
        "active": "mysk:\n  state: active\n",
        "experimental": "mysk:\n  state: experimental\n",
        "deprecated": "mysk:\n  state: deprecated\n",
    }
    for label, block in cases.items():
        print(f"  {label:<24} {len(enc.encode(block))} tok")


if __name__ == "__main__":
    main()
