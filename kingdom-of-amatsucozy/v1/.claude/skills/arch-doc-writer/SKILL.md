---
name: arch-doc-writer
description: Content rules for Amatsucozy architecture documentation sets. Read this skill when King is about to write architecture docs after a *cad command. Assumes Scout brief has already been written. Defines 7-file sharded structure, content requirements per file, and index update rules. Do not read source code — Scout already did that.
---

# Architecture Doc Writer

Read by King before writing any file in `docs/architecture/`.  
Template: `.amtcz/templates/architecture-doc-template.md`  
Scout brief already read? Required before proceeding.

---

## Pre-write checks

1. Scout brief at `/.amtcz/briefs/{feature}-scout.md` — read it, note affected files and gaps
2. Location: whole repo → `docs/architecture/` · specific module → `docs/architecture/{topic}/`
3. Confirm topic name (kebab-case) with user before creating a new folder
4. Check `docs/architecture/README.md` for existing matching folder

---

## Generate all 7 files (one pass — never partial)

```
{target}/
├── README.md               ← index + navigation only
├── architecture.md         ← high-level design + ASCII component diagram
├── api-specification.md    ← endpoints, schemas, error codes
├── implementation-guide.md ← patterns, gotchas, code examples
├── integration.md          ← external systems, contracts, auth, failure modes
├── operations.md           ← metrics, alerting, security, runbooks
└── deployment.md           ← infrastructure, CI/CD, env vars, rollback
```

For per-file content requirements → `skills/arch-doc-writer/references/file-structure.md`

---

## Content rules

**No speculation.** Mark unknowns: `> **TBD:** {question}`  
**No source verbatim.** The doc explains why and when — source already shows what.  
**ASCII diagram in architecture.md** — component relationships, not a component list.  
**Check recent design docs** — docs must reflect post-AMTCZ state of components.

---

## Index update

After generating files, update `docs/architecture/README.md`:

```markdown
- [{topic}](./{topic}/) — {one-line description}
```

Create `docs/architecture/README.md` if it does not exist.

---

## Quality gate

- [ ] All 7 files generated
- [ ] README.md contains only navigation
- [ ] architecture.md has ASCII component diagram
- [ ] TBD markers on all unknowns — no guesses
- [ ] Index updated
- [ ] Folder name confirmed with user (kebab-case)
