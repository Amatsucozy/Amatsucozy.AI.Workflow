---
name: arch-doc-writer
description: Content rules for Amatsucozy architecture documentation sets. Read this skill when King is about to write architecture docs after a *cad command. Contains the architecture doc template, 7-file structure rules, and quality gate. Assumes Scout brief has already been read by King. Do not read source code directly — Scout already did that.
cache_control: ephemeral
---

# Architecture Doc Writer

Read by King before writing any file in `docs/architecture/`.

**Template:** `skills/arch-doc-writer/assets/architecture-doc-template.md` — use as base for every file.  
**File content guide:** `skills/arch-doc-writer/references/file-structure.md` — read to know what goes in each of the 7 files.

---

## Pre-write checks

1. Scout brief already in King's context? Required — do not proceed without it.
2. Note all TBD gaps from the scout brief — these become `> **TBD:**` markers in the docs.
3. Determine location:
   - Whole repo → `docs/architecture/`
   - Specific module → `docs/architecture/{topic}/`
4. Check `docs/architecture/README.md` for existing matching folder.
5. Confirm topic name (kebab-case) with user before creating a new folder.

---

## Generate all 7 files — one pass, never partial

```
docs/architecture/{topic}/
├── README.md               ← index + navigation only
├── architecture.md         ← high-level design + ASCII component diagram
├── api-specification.md    ← endpoints, schemas, error codes
├── implementation-guide.md ← patterns, gotchas, code examples
├── integration.md          ← external systems, contracts, auth, failure modes
├── operations.md           ← metrics, alerting, security, runbooks
└── deployment.md           ← infrastructure, CI/CD, env vars, rollback
```

Apply the template from `assets/architecture-doc-template.md` to each file.  
Read `references/file-structure.md` to know what content each file requires.

---

## Content rules

**No speculation.** Every unknown becomes: `> **TBD:** {specific question to resolve}`  
**No verbatim source.** The doc explains why and when — source already shows what.  
**ASCII diagram required in architecture.md** — component relationships, not a component name list.  
**Check recent design docs** — docs must reflect the current state of components, including any recent AMTCZ changes.

---

## Index update

After generating all files, update `docs/architecture/README.md`:

```markdown
- [{topic}](./{topic}/) — {one-line description}
```

Create `docs/architecture/README.md` if it does not exist.

---

## Quality gate

- [ ] All 7 files generated — no partial sets
- [ ] README.md contains only navigation links
- [ ] architecture.md has an ASCII component diagram
- [ ] All unknowns marked TBD — no guesses
- [ ] Index updated
- [ ] Topic folder name is kebab-case and confirmed with user
