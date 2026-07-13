# Graph Report - .  (2026-07-13)

## Corpus Check
- Corpus is ~20,693 words - fits in a single context window. You may not need a graph.

## Summary
- 126 nodes · 196 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.82)
- Token cost: 77,020 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CICD Pipeline & Config|CI/CD Pipeline & Config]]
- [[_COMMUNITY_UUP Dump API Client|UUP Dump API Client]]
- [[_COMMUNITY_Build State Management|Build State Management]]
- [[_COMMUNITY_PEWIM Test Fixtures|PE/WIM Test Fixtures]]
- [[_COMMUNITY_Daily Build Picker|Daily Build Picker]]
- [[_COMMUNITY_Workflow Definitions|Workflow Definitions]]
- [[_COMMUNITY_Architecture & Method Docs|Architecture & Method Docs]]
- [[_COMMUNITY_PDB Symbol Finder|PDB Symbol Finder]]
- [[_COMMUNITY_WIM Deduplication|WIM Deduplication]]
- [[_COMMUNITY_Docs Index Generator|Docs Index Generator]]
- [[_COMMUNITY_Extract and Parse Script|Extract and Parse Script]]
- [[_COMMUNITY_Symbol Manifest Concepts|Symbol Manifest Concepts]]

## God Nodes (most connected - your core abstractions)
1. `create_iso job` - 9 edges
2. `Key Scripts Catalog (code/)` - 9 edges
3. `listid()` - 8 edges
4. `Pinned Python Requirements (requirements.txt)` - 7 edges
5. `main()` - 6 edges
6. `split_wims job` - 6 edges
7. `build job (mkdocs.yml workflow)` - 6 edges
8. `test job` - 6 edges
9. `process_file()` - 5 edges
10. `BuildInfo` - 5 edges

## Surprising Connections (you probably didn't know these)
- `UUP-to-ISO-to-WIM Method` --semantically_similar_to--> `Automated Symbol Manifest Pipeline`  [INFERRED] [semantically similar]
  README.md → ARCHITECTURE.md
- `test_module()` --calls--> `priority_uuids()`  [INFERRED]
  tests/test_state.py → code/state.py
- `build()` --calls--> `BuildInfo`  [INFERRED]
  tests/test_daily.py → code/uupdump.py
- `Dependabot Configuration` --references--> `Pinned Python Requirements (requirements.txt)`  [INFERRED]
  .github/dependabot.yml → requirements.txt
- `tests/test_state.py` --references--> `code/state.py (builds_state.json owner, mark-done/mark-failed CLI)`  [INFERRED]
  .github/workflows/test.yml → ARCHITECTURE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Key Scripts Catalog** — code_uupdump_uupdump, code_daily_daily, code_state_state, code_wim_dedup_wim_dedup, code_extract_and_parse_extract_and_parse, code_pdb_finding_pdb_finding, code_get_editions_get_editions, code_gen_docs_index_gen_docs_index, code_move_iso_dir_move_iso_dir [EXTRACTED 1.00]
- **Manifest Generation Pipeline (download_build.yml jobs)** — _github_workflows_download_build_create_iso, _github_workflows_download_build_split_wims, _github_workflows_download_build_parse_boot_wim, _github_workflows_download_build_parse_install_wim, _github_workflows_download_build_merge_artifacts, _github_workflows_download_build_deploy_manifest, _github_workflows_download_build_mark_build_failed [EXTRACTED 1.00]
- **Mutex-Serialized State Mutation Flow** — _github_workflows_download_build_mark_build_failed, _github_workflows_download_build_deploy_manifest, code_state_state, builds_state_json [EXTRACTED 1.00]

## Communities (12 total, 2 thin omitted)

### Community 0 - "CI/CD Pipeline & Config"
Cohesion: 0.14
Nodes (27): create_iso job, deploy_manifest job, mark_build_failed job, merge_artifacts job, parse_boot_wim job, parse_install_wim job, split_wims job, publish_docs job (main.yml) (+19 more)

### Community 1 - "UUP Dump API Client"
Cohesion: 0.25
Nodes (14): BaseModel, BuildInfo, _EditionsResponse, _Envelope, _get(), get_build_name(), get_editions(), get_langs() (+6 more)

### Community 2 - "Build State Management"
Cohesion: 0.21
Nodes (12): excluded_uuids(), load_state(), main(), mark_done(), mark_failed(), priority_uuids(), Uuids that must not be attempted again., save_state() (+4 more)

### Community 3 - "PE/WIM Test Fixtures"
Cohesion: 0.23
Nodes (12): expected_signature_string(), make_pe(), Build a minimal PE32+ file with an optional CodeView (RSDS) debug entry.  Used b, The Signature_String pefile derives from an RSDS entry (symbol-server id)., build_tree(), main(), End-to-end test for code/pdb_finding.py.  Builds a directory tree of synthetic P, main() (+4 more)

### Community 4 - "Daily Build Picker"
Cohesion: 0.21
Nodes (8): is_wanted(), pick_builds(), Minimal helper for talking to the GitHub Actions runner., Set a step output; echoes to stderr (and stdout when run locally)., write_output(), build(), main(), Unit test for the build-picking logic in code/daily.py.  Run from the repo root:

### Community 5 - "Workflow Definitions"
Cohesion: 0.22
Nodes (9): Dependabot Configuration, Download UUID Build Workflow (reusable), download_releases job, list_releases job, Detect more uup entries workflow (main.yml), Publish docs via GitHub Pages workflow, Tests workflow, code/daily.py (pick next builds) (+1 more)

### Community 6 - "Architecture & Method Docs"
Cohesion: 0.25
Nodes (9): builds_state.json State Semantics, Mutex-Serialized State Commits, Automated Symbol Manifest Pipeline, Operational Runbooks, Alternative Windows Media Sources (considered, not adopted), UUP-to-ISO-to-WIM Method, pdblister (external tool), WindowsSymbolsByVersion Project Overview (+1 more)

### Community 7 - "PDB Symbol Finder"
Cohesion: 0.39
Nodes (7): get_guid(), list_files(), process_file(), Return the (pdb, guid) entries of a single file., Traverse the directory and process each file., traverse_directory(), PE

### Community 8 - "WIM Deduplication"
Cohesion: 0.53
Nodes (5): image_count(), is_interesting(), list_image_files(), main(), Yield (path, hash) for every regular file in the image.

### Community 9 - "Docs Index Generator"
Cohesion: 0.60
Nodes (4): build_sort_key(), group_of(), main(), mkdocs-gen-files script: render the version index from builds_state.json.  Gener

## Knowledge Gaps
- **11 isolated node(s):** `extract_and_parse.sh script`, `Detect more uup entries workflow (main.yml)`, `Publish docs via GitHub Pages workflow`, `Tests workflow`, `Operational Runbooks` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `create_iso job` connect `CI/CD Pipeline & Config` to `Architecture & Method Docs`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `Pinned Python Requirements (requirements.txt)` connect `CI/CD Pipeline & Config` to `Workflow Definitions`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Automated Symbol Manifest Pipeline` connect `Architecture & Method Docs` to `CI/CD Pipeline & Config`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **What connects `extract_and_parse.sh script`, `mkdocs-gen-files script: render the version index from builds_state.json.  Gener`, `Minimal helper for talking to the GitHub Actions runner.` to the rest of the system?**
  _30 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CI/CD Pipeline & Config` be split into smaller, more focused modules?**
  _Cohesion score 0.1396011396011396 - nodes in this community are weakly interconnected._