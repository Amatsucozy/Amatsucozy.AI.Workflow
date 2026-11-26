---
name: sonarqube-project-map
description: Generate or refresh the SonarQube-key ↔ GitHub-repo map that the `sonarqube-issues` skill reads from its resources/projects/<org>/map.md. Use for "map sonarqube projects", "refresh/sync the sonarqube project map", "onboard org X to sonarqube tooling", or when sonarqube-issues reports it fell back to live discovery. Cross-references GitHub repos with SonarQube projects by normalized name, renders from the fixed template, and lists anything ambiguous as unmapped rather than guessing.
---

# SonarQube Project Map Generator

Maintains the lookup table `sonarqube-issues` depends on; it never queries
issues. Needs two MCP servers — SonarQube (`search_my_sonarqube_projects`) and
GitHub (`search_repositories`); take prefixes and parameter names from the
loaded schemas. If either is missing or needs authorization, say so and stop.

## 1. Target and paths

- Org: the one the user names, else from `git remote -v`. Remotes for several
  orgs, or none → ask.
- Output: `<sonarqube-issues skill dir>/resources/projects/<org-lowercase>/map.md`
  — normally the sibling `../sonarqube-issues/`; if installed elsewhere,
  resolve it from the skill listing. No absolute paths.
- Template: this skill's `resources/template.md`.

## 2. Pull both sides, fully paginated

- GitHub: `search_repositories` with `query: "org:<ORG>"`,
  `minimal_output: true`, paging until all `total_count` repos are collected.
- SonarQube: `search_my_sonarqube_projects` with no `q`, `pageSize: 500`,
  paging while `paging.hasNextPage`.

Compare only after both sides are complete, so a repo missing from page one
isn't dropped from the map.

## 3. Match by normalized name

Normalize: lowercase, strip a leading/trailing org token (`<org> `, `<org>_`,
`<org>-`), collapse `-`/`_`/space. Match when normalized names are equal, or
one contains the other with no equally plausible alternative. Anything
without a single confident match goes under "Unmapped — verify manually" —
`sonarqube-issues` trusts this file without re-checking, so a wrong mapping is
worse than none.

## 4. Render from the template

Read `resources/template.md` every time and copy it verbatim, filling only
its placeholders and rows:

- `<ORG>` / `<ORG_LOWER>` / `<ORG_URL>` / `<DATE>` in the header.
- **Mapped projects**: one row per confident pair (SonarQube key | GitHub repo
  | Notes).
- **GitHub repos with no SonarQube project**: one bullet per repo.
- **Unmapped — verify manually**: one bullet per entry, or the template's
  exact "None as of last generation..." line.

Keep the section headers exactly as the template has them so every map stays
mechanically diffable; to change the structure, edit the template and say
that existing maps need regenerating. If a map already existed, report what
moved (added/removed/renamed mappings, coverage gained or lost).

Write only under `sonarqube-issues/resources/projects/<org>/`; never edit
`sonarqube-issues/SKILL.md`.

## 5. Report

Org, GitHub repo count, SonarQube project count, mapped count, unmapped count
with reasons, and the path written.
