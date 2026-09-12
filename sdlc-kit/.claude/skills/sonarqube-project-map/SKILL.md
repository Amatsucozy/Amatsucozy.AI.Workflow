---
name: sonarqube-project-map
description: Generate or refresh the SonarQube-key ↔ GitHub-repo map that the `sonarqube-issues` skill reads from its resources/projects/<org>/map.md. Use for "map sonarqube projects", "refresh/sync the sonarqube project map", "onboard org X to sonarqube tooling", or when sonarqube-issues reports it fell back to live discovery. Cross-references GitHub repos with SonarQube projects by normalized name, renders from the fixed template, and lists anything ambiguous as unmapped rather than guessing.
---

# SonarQube Project Map Generator

## When to use

- Explicit ask to create/update/refresh/sync the SonarQube project map for a
  GitHub org.
- `sonarqube-issues` reported it fell back to live discovery because no map
  exists yet, or the existing one looks stale.
- Onboarding a new GitHub org / SonarQube account to this tooling.

Not for listing or summarizing issues — that's `sonarqube-issues`. This skill
only maintains the lookup table that skill depends on; it never queries
issues.

## Prerequisites

- Two MCP servers: SonarQube (`search_my_sonarqube_projects`) and GitHub
  (`search_repositories`). Both are deferred — load them with ToolSearch
  (`+sonarqube projects`, `+github search repositories`) before the first
  call and read the returned schemas; prefixes and parameter names come from
  the registration, never from memory.
- Either server missing or needing authorization → say so and stop; never
  fabricate a side of the mapping.

## Workflow

### 1. Determine the target org and output path

- Org: the one the user names, else derived from `git remote -v` (the path
  segment right before the repo name). Multiple remotes pointing at
  different orgs, or none → ask.
- Output path: `<sonarqube-issues skill dir>/resources/projects/<org-lowercase>/map.md`.
  The `sonarqube-issues` skill ships beside this one, so its directory is the
  sibling `../sonarqube-issues/` of the folder holding this SKILL.md; if it
  is installed elsewhere, resolve it from the available-skills listing.
  Never hardcode an absolute path.
- Template: this skill's own `resources/template.md` (sibling of this
  SKILL.md). Only the *output* lives inside `sonarqube-issues`.

### 2. Pull both sides fully paginated

- **GitHub**: `search_repositories` with `query: "org:<ORG>"` and
  `minimal_output: true`; page with `page`/`perPage` until all `total_count`
  repos are collected.
- **SonarQube**: `search_my_sonarqube_projects` with no `q` filter and
  `pageSize: 500`; page via `pageIndex` while `paging.hasNextPage` is true.

### 3. Cross-reference by normalized name

- Normalize both sides: lowercase; strip a leading/trailing org token
  (`<org> `, `<org>_`, `<org>-`); collapse `-`/`_`/space.
- Match when the normalized names are equal, or one is a substring of the
  other with no other equally plausible candidate.
- Anything without a single confident match — on either side — goes under
  "Unmapped — verify manually". A wrong mapping is worse than none:
  `sonarqube-issues` trusts this file as a fast path without re-verifying.

### 4. Write the resource file from the fixed template

Read `resources/template.md` first, every time. Write (or overwrite) the
output path by copying the template verbatim and filling only its `<...>`
placeholders and table rows/bullets:

- `<ORG>` / `<ORG_LOWER>` / `<ORG_URL>` / `<DATE>` in the header.
- One **Mapped projects** row per confident pair: SonarQube key | GitHub repo
  | Notes.
- One bullet per repo under **GitHub repos with no SonarQube project**.
- One bullet per entry under **Unmapped — verify manually**, or the
  template's exact "None as of last generation..." line when empty.

Never rename, reorder, add, or remove section headers — the fixed structure
is what keeps every org's map.md, and successive regenerations, mechanically
diffable. If the structure itself needs to change, edit
`resources/template.md` and say so, so every existing map.md gets
regenerated to match.

If the target map.md already existed, diff the new tables against the old
and report what moved (added/removed/renamed mappings, repos that gained or
lost coverage) rather than silently overwriting.

### 5. Report

Org, GitHub repo count, SonarQube project count, how many mapped cleanly,
how many unmapped/ambiguous (and why), and the file path written.

## Guardrails

- Never force a mapping you aren't confident in — list it as unmapped.
- Never drop an existing mapping because a repo didn't appear on the first
  GitHub page — page fully before comparing (Step 2).
- Writes only under `sonarqube-issues/resources/projects/<org>/`; never edits
  `sonarqube-issues/SKILL.md`.
- Always render from `resources/template.md`, not from memory of a previous
  map.md.

## Example

```
git remote -v → https://github.example.com/acme-corp/api-service.git → org "acme-corp"
search_repositories(query="org:acme-corp", minimal_output=true) → total_count 24, all pages collected
search_my_sonarqube_projects(pageSize=500) → 7 projects, hasNextPage=false

Normalize + match: all 7 SonarQube projects ↔ 7 GitHub repos (e.g.
  acme-corp_api-service ↔ acme-corp/api-service); 17 repos have no project.

Write ../sonarqube-issues/resources/projects/acme-corp/map.md from the template.
Report: "acme-corp — 24 GitHub repos, 7 SonarQube projects, 7 mapped, 0 unmapped.
Wrote resources/projects/acme-corp/map.md."
```
