# Toolchain custody

## Rules repository

- Worktree: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/rulespec-us-nsf-in149-20260830-47290`
- Required base object: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Local `origin/main` at creation: `d58cc0ce67ad891fde4c9061c86a2091bfdd524f`
- Mode: detached HEAD
- Fresh-fetch attempt: failed before ref update because the sandbox could not resolve `github.com`
- Existing branches and axiom-corpus PR #631: untouched

## Encoder

- Root: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-encode`
- Commit: `3869d66d009f52258be35901edbef370e65a399c`
- Worktree state at audit: clean detached HEAD
- Package version: `0.2.1200`
- `.venv/bin/axiom-encode` SHA-256: `6d134a9820f10826d3cb56e1a0df755636cad8543051811acc2f0be102af0173`
- `uv.lock` SHA-256: `ff0ea7983fe344be90ab54b388b0c4c441a1ac69ecf73937440d12802d92d5fc`
- `pyproject.toml` SHA-256: `4b9b24e4e9c78035ac4e66b09b9b9515b28a599660a17c48e031e968592256cd`
- Backend/model: Codex / `gpt-5.5`
- Codex CLI version: `0.144.0`

## Rust rules engine

- Root: `/Users/maxghenis/TheAxiomFoundation/_axiom-worktrees/nsf-pappg-toolchain/axiom-rules-engine`
- Commit: `ffd8213271947b0189a9dd61a055c1e0e78908a0`
- Worktree state at audit: clean detached HEAD
- `Cargo.lock` SHA-256: `56f01fb4b5118a479328fbffd55b93635ed11038de60bcdd206b88aad84d16cb`
- `target/debug/axiom-rules-engine` SHA-256: `ea9ba72582a92ac5f7b38fee0c6e30924669e5f2b8d1158f9162187776bd8efb`

The required base `.axiom/toolchain.toml` does not pin these encoder and engine
commits. The user-specified detached checkout paths and the hashes above are
therefore the custody pins for this task.

## Signing custody

- Required interface: `agent-secret`
- Expected service: `agent/axiom-encode-apply-signing-key`
- `AXIOM_ENCODE_APPLY_SIGNING_KEY` was absent from the shell.
- `agent-secret search axiom` failed before listing services because the
  dedicated keychain's login-keychain unlock-password item is missing.
- The prescribed `agent-secret init` recovery check failed closed because the
  dedicated keychain already exists.
- No signing-key value was read, printed, copied, or bypassed.

Signed apply cannot proceed until the dedicated keychain unlock item is safely
restored. Recreating the existing keychain could destroy other agent secrets and
requires explicit user action.

## Resumed signing custody

The preceding subsection records the earlier run's environment and is retained
as historical custody. On resumption, the user stated that
`AXIOM_ENCODE_APPLY_SIGNING_KEY` was inherited and expressly prohibited any
printing, logging, hashing, rotation, or retrieval. The fresh A3 commands passed
no key argument and performed no keychain lookup. They requested `--apply`, but
both stopped at `apply_blocked_generation` before validation, installation, or
manifest signing, so signer usability was not exercised. No key value was
accessed or disclosed, and the obsolete keychain-recovery step was not followed.
