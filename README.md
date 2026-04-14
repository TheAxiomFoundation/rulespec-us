# rac-us-al

Alabama jurisdiction-specific RAC source and encoding corpus.

This repo is for Alabama-administered policy layers. Federal program cores stay
in `rac-us`; Alabama overlays, manuals, guidance, and state-specific encodings
live here.

## Current scope

- Alabama SNAP source slices for delegated SNAP state options
- jurisdiction-local source corpus for Alabama SNAP overlays

## Layout

```text
rac-us-al/
├── sources/
│   └── slices/
│       └── aldhr/
│           └── poe/
│               └── current-effective/
├── scripts/
│   ├── check_no_promoted_stubs.py
│   └── validate_repo.py
└── CLAUDE.md
```

## Local commands

```bash
cd /Users/maxghenis/TheAxiomFoundation/rac
uv run python -m rac.validate all /Users/maxghenis/TheAxiomFoundation/rac-us-al
uv run python -m rac.test_runner /Users/maxghenis/TheAxiomFoundation/rac-us-al -v

cd /Users/maxghenis/TheAxiomFoundation/rac-us-al
python3 scripts/validate_repo.py
```

## Encoding policy

- Repo boundaries follow jurisdictions.
- Keep Alabama-administered overlays in `rac-us-al`, even when they sit on top
  of a federal program like SNAP.
- Keep exact local excerpts in `sources/slices/`.
- When an Alabama source sets a value inside a federally delegated slot, add a
  `*.meta.yaml` sidecar next to the source slice with `relation: sets` pointing
  to the canonical upstream CFR or USC target.
- Do not hand-edit promoted policy outputs; use AutoRAC plus benchmarked repair
  loops.
