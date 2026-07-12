# Architecture

This repo turns Windows builds published on [uupdump.net](https://uupdump.net) into
symbol-server manifests, fully automated on GitHub Actions.

## Pipeline

```mermaid
flowchart TD
    A[main.yml: list_releases<br>daily.py picks new builds] -->|uuid matrix| B
    subgraph download_build.yml [download_build.yml - one run per uuid]
        B[create_iso - windows runner<br>download UUP set, convert, parse iso root]
        B -->|failure| F[mark_build_failed<br>state.py mark-failed]
        B -->|boot.wim + install.wim artifacts| C[split_wims<br>wim_dedup.py: hash-dedup across images,<br>keep PE-like files, emit listfiles]
        C -->|listfiles + image matrix| D1[parse_boot_wim<br>extract_and_parse.sh per image]
        C --> D2[parse_install_wim<br>extract_and_parse.sh per image]
        D1 --> E[merge_artifacts<br>sort -u of all partial manifests]
        D2 --> E
        E --> G[deploy_manifest<br>commit manifests/uuid.manifest,<br>state.py mark-done]
    end
    A --> H[publish_docs<br>mkdocs gh-deploy]
    G -.builds_state.json commit.-> H
```

`main.yml` runs daily (03:00 UTC cron) and via `workflow_dispatch`. The repo
variable `ALLOWED_DOWNLOAD_SIZE` caps how many new builds one run attempts
(defaults to 3 when unset).

## State: builds_state.json

The single record of what happened to every build, owned by `code/state.py`:

```json
{
  "priority": ["<uuid>"],
  "builds": {
    "<uuid>": {"status": "done", "title": "...", "build": "26100.1", "arch": "amd64"},
    "<uuid>": {"status": "failed", "failures": 2, "last_run": "<actions run url>"}
  }
}
```

- `done` builds are never re-attempted; their metadata renders the website.
- `failed` builds are retried until `failures` reaches `MAX_FAILURES` (3), so
  transient runner/uupdump errors do not permanently blacklist a build.
- `priority` uuids are picked before anything else on the next run.

Both jobs that commit (`mark_build_failed`, `deploy_manifest`) serialize via a
mutex action, and all state mutations go through `state.py`, which is
idempotent - a rerun cannot duplicate entries.

## Key scripts (code/)

| Script | Role |
|---|---|
| `uupdump.py` | the only uupdump API client: models, shared session, retries |
| `daily.py` | picks the next builds (filters insider/preview/cumulative, arm64, non-en-us) |
| `state.py` | owns builds_state.json; `mark-done` / `mark-failed` CLI |
| `wim_dedup.py` | lists each wim image from WIM metadata, hash-dedups across images, emits `wimextract` listfiles of PE-like files only |
| `extract_and_parse.sh` | extracts one image's listfile and runs the parser |
| `pdb_finding.py` | walks a directory, reads PE debug directories (parallel, debug-dir-only parsing), emits `pdb,guid,1` lines |
| `get_editions.py` | resolves a build's edition list for the uupdump download request |
| `gen_docs_index.py` | mkdocs-gen-files script: renders `index.md` + machine-readable `index.json` from builds_state.json |
| `move_iso_dir.bat` | renames the converter's output dir to `unpacked_dir` |

`config.template` is the [uup-converter](https://github.com/abbodi1406/BatUtil)
`ConvertConfig.ini` used during iso creation (SkipISO=1: we only need the wims).

## Website

The site is generated - do not edit `docs/index.md` (it does not exist in the
repo). `code/gen_docs_index.py` renders the version tables and `index.json`
from `builds_state.json` at build time. Publishing happens at the end of every
`main.yml` run and on any push to main that touches the state file.

## Runbooks

- **Process one specific build:** add its uuid to `priority` in
  builds_state.json (or dispatch `main.yml`; priority uuids are picked first).
- **Retry a permanently-failed build:** delete its entry from `builds` in
  builds_state.json - it becomes eligible on the next run.
- **Re-run a whole uuid manually:** dispatch `main.yml`, or re-run the failed
  `download_build.yml` run from the Actions UI.
- **Local development:** `pip install -r requirements.txt`, `apt install
  wimtools`, then run the test scripts under `tests/` from the repo root
  (they are also run by `.github/workflows/test.yml` on every push).
