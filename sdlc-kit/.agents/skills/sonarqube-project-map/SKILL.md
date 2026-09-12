---
name: sonarqube-project-map
description: Generate or refresh the SonarQube project-key to GitHub repository map for an organization. Use for project mapping or onboarding requests; write the companion sonarqube-issues cache from the bundled template and flag ambiguous matches.
---

# Skill: SonarQube project map generator

## When to use

- Explicit ask to create/update/refresh/sync the SonarQube project map for
  a GitHub org.
- `sonarqube-issues` reported it had to fall back to live discovery
  because no resource map exists yet, or the existing one looks stale.
- Onboarding a new GitHub org / SonarQube account to this tooling.

Not for: listing or summarizing SonarQube issues on a branch/PR — that's
`sonarqube-issues`. This skill only maintains the lookup table that skill
depends on; it never queries issues itself.

## Prerequisites

Discover the configured SonarQube MCP tools through the available Codex tool
listing or tool search. For project mapping, also discover GitHub repository
search. Inspect actual schemas before calling tools; operation names below are
examples and prefixes/parameters may vary. If required access is missing,
report the missing capability without inventing results.

## Workflow

### 1. Determine the target org and output path

- Use the org the user names, or derive it from the current repo's
  `git remote -v` (the path segment right before the repo name).
- Locate the `sonarqube-issues` skill's directory from its file path
  in the available-skills listing, or resolve the sibling
  `../sonarqube-issues/SKILL.md` when working from this kit — don't hardcode an absolute path, since the skill could live
  under a different install location (project-scoped `.agents/skills/`, a plugin, or a global skills dir). This skill's own
  `resources/template.md` (a sibling of this `SKILL.md`) stays local —
  it's only the *output* file that lives inside `sonarqube-issues`.
- The output file is always
  `<sonarqube-issues skill directory>/resources/projects/<org-lowercase>/map.md`.

### 2. Pull both sides fully paginated

- **GitHub**: call `search_repositories` with `query: "org:<ORG>"` and
  `minimal_output: true`. Page through with `page`/`perPage` until you've
  collected all `total_count` repos — don't stop at the first page.
- **SonarQube**: call `search_my_sonarqube_projects` with no `q` filter
  and `pageSize: 500`, paging via `pageIndex` while `paging.hasNextPage`
  is true.

### 3. Cross-reference by normalized name

- Normalize both sides: lowercase, strip a leading/trailing org-name
  token (e.g. an `<org> `, `<org>_`, or `<org>-` prefix), collapse
  `-`/`_`/space.
- Match a SonarQube project to a GitHub repo when the normalized names
  are equal, or one is a substring of the other with no other equally
  plausible candidate.
- Anything without a single confident match — on either side — goes into
  an "Unmapped — verify manually" list instead of being force-matched.
  Do not guess a mapping you aren't confident in; a wrong mapping is worse
  than no mapping, since `sonarqube-issues` trusts this file as a fast
  path without re-verifying it.

### 4. Write the resource file from the fixed template

This skill's own `resources/template.md` (a sibling of this `SKILL.md`)
is the canonical structure for map.md — read it first, every time. Write
(or overwrite) `sonarqube-issues/resources/projects/<org-lowercase>/map.md`
(the path resolved in Step 1) by copying that template verbatim and only
filling in its `<...>` placeholders and table rows/bullets:

- `<ORG>` / `<ORG_LOWER>` / `<ORG_URL>` / `<DATE>` in the header.
- One **Mapped projects** row per confidently-matched pair: `SonarQube
  key | GitHub repo | Notes`.
- One bullet per repo in **GitHub repos with no SonarQube project**.
- One bullet per entry in **Unmapped — verify manually** (or the
  template's exact "None as of last generation..." line if empty).

Do not rename, reorder, add, or remove section headers, and do not
deviate from the template's structure — this is what keeps every org's
map.md (and successive regenerations of the same one) mechanically
diffable instead of reformatted prose each time. If the template file
itself seems to need a structural change, edit `resources/template.md`
directly (not just this one org's output) and say so, so every existing
map.md is regenerated to match.

If the target map.md already existed, diff the new tables against the
old ones and report what changed (added/removed/renamed mappings, repos
that gained or lost SonarQube coverage) instead of silently overwriting —
the user should see what moved before trusting the refreshed file.

### 5. Report

Summarize: org, GitHub repo count, SonarQube project count, how many
mapped cleanly, how many are unmapped/ambiguous (and why), and the
resource file path written.

## Guardrails

- Never force a mapping you're not confident in — list it under
  "Unmapped — verify manually" instead of guessing. A stale-but-honest
  "unmapped" entry is safer than a wrong mapping baked into a cache.
- Never drop an existing mapping just because a repo didn't appear on the
  first GitHub page — page through fully before comparing (Step 2).
- This skill only writes files under
  `sonarqube-issues/resources/projects/<org>/`; it never edits
  `sonarqube-issues/SKILL.md` itself.
- Always generate map.md from `resources/template.md`, not from memory of
  what a previous map.md looked like — free-form reformatting defeats the
  point of a deterministic, diffable output.
- If the org can't be derived unambiguously (e.g. multiple git remotes
  pointing at different orgs, or none at all), ask the user rather than
  picking one.

## Example

```
git remote -v → https://github.example.com/acme-corp/api-service.git
  → org "acme-corp"

search_repositories(query="org:acme-corp", minimal_output=true)
  → total_count: 24, page through until all 24 are collected

search_my_sonarqube_projects(pageSize=500)
  → 7 projects, paging.hasNextPage=false

Normalize + match:
  acme-corp_api-service      ↔ acme-corp/api-service
  acme-corp_platform-core    ↔ acme-corp/platform-core
  acme-corp_customer-service ↔ acme-corp/customer-service
  acme-corp_pricing-service  ↔ acme-corp/pricing-service
  acme-corp_billing-jobs     ↔ acme-corp/billing-jobs
  acme-corp_infrastructure   ↔ acme-corp/infrastructure
  acme-corp_monitoring       ↔ acme-corp/monitoring
  (all 7 matched confidently; 17 GitHub repos have no SonarQube project)

Write sonarqube-issues/resources/projects/acme-corp/map.md with both
tables and an empty "Unmapped" section.

Report: "acme-corp org — 24 GitHub repos, 7 SonarQube projects, all 7
mapped cleanly, 0 unmapped. Wrote resources/projects/acme-corp/map.md."
```
