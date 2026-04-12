---
name: arch-doc-writer
description: Governs the structure, content rules, and generation process for architecture documentation sets in the Amatsucozy workflow. Read this skill whenever *create-architecture-doc (*cad) is triggered. Covers scope assessment, source code investigation, sharded file generation, and index updates.
---

# Architecture Doc Writer

Defines how to create a complete, sharded architecture documentation set.
Read this before generating any files in `docs/architecture/`.

---

## Template

Always read `.amtcz/templates/architecture-doc-template.md` before generating any file.
Use it as the base content for each file, customising title and purpose per file role.

---

## Allowed information sources

- ✅ Source code (read and understand it — don't summarise from filenames)
- ✅ Existing `docs/architecture/` files
- ✅ The architecture doc template
- ✅ User-provided context about external dependencies

Do not reference or link to `docs/business/` — architecture docs are technical documents.

---

## Process

### Step 1: Scope assessment

Determine whether the request covers:
- **Whole repo** → target `docs/architecture/` directly
- **Specific project/module** → target `docs/architecture/[topic]/`

If the scope is too large to document coherently in one pass (e.g. "document the entire system"), propose a breakdown into sub-modules and confirm with the user before proceeding. Document sub-modules one at a time with explicit confirmation between each.

### Step 2: Location determination

For specific module requests:
1. Check `docs/architecture/` for an existing folder that matches the topic
2. If found: confirm whether to update it or create a new sub-folder
3. If not found: confirm the topic name (must be kebab-case) before creating

Never create a folder without confirming the name.

### Step 3: Source code investigation

Read the source code meticulously. This means opening and reading implementation files — not inferring from directory structure or file names.

During investigation, identify grey areas that are not resolvable from source alone:
- External libraries whose runtime behaviour affects the system (e.g. retry semantics of a client library)
- Configuration values that live outside the codebase (environment variables, infrastructure config)
- Integration contracts with external systems (APIs, message formats, auth mechanisms)
- Anything that would require a guess to document

**Proactively ask the user about grey areas before writing.** A doc with a confident gap is worse than one that admits uncertainty. Use "TBD — requires [specific information]" markers for anything that cannot be resolved from available sources.

### Step 4: Generate all seven files

Create all seven files in the target folder in a single pass. Do not generate partial sets.

```
[target]/
├── README.md               ← Index & navigation
├── architecture.md         ← High-level design & component map
├── api-specification.md    ← Endpoints, schemas, error codes
├── implementation-guide.md ← Code examples, patterns, gotchas
├── integration.md          ← External systems & contracts
├── operations.md           ← Monitoring, alerting, security, runbooks
└── deployment.md           ← Infrastructure, CI/CD, environment config
```

#### File purpose guide

**README.md** — index only. Lists all other files with one-line descriptions. Links to each. No architectural content here — its only job is navigation.

**architecture.md** — the centrepiece. High-level design rationale, component map (with ASCII diagram showing component relationships), key architectural decisions and why they were made, known trade-offs.

**api-specification.md** — every public interface: HTTP endpoints (method, path, request/response schemas, error codes), message queue formats, gRPC definitions, CLI arguments. Include example request/response pairs.

**implementation-guide.md** — for developers working in this codebase. Key patterns used, gotchas and non-obvious behaviours, code examples for common operations, test setup instructions.

**integration.md** — external systems this module talks to. For each: what the contract is, how auth works, what failure modes exist, how to test the integration locally.

**operations.md** — for people running this in production. Key metrics and what they mean, alerting thresholds, security boundaries, runbooks for known failure scenarios.

**deployment.md** — infrastructure definition, environment variables and their purpose, CI/CD pipeline stages, how to deploy to each environment, rollback procedure.

### Step 5: Index update

If this is a sub-module (not the whole repo), update `docs/architecture/README.md` to link to the new folder:

```markdown
## Modules
- [retry-worker](./retry-worker/) — Transient failure retry logic for the job worker
```

If `docs/architecture/README.md` does not exist, create it.

---

## Content quality rules

**No speculation.** If a fact isn't known from source code or user-provided context, mark it explicitly:
```
> **TBD:** Confirm the exact retry semantics of the `tenacity` library for connection timeouts.
```

**No copy-paste from source.** The doc explains *why* and *when*, not just *what*. Source code already shows what — the doc's job is to add the context that code cannot.

**ASCII diagrams in architecture.md.** The component map must include an ASCII diagram showing how components relate. Use the same style as design docs:

```
  External Client
       │
       ▼
  API Gateway ──→ Auth Service
       │
       ▼
  Worker Service ──→ RetryHandler ──→ Job Queue
       │
       └──────────────────────────→ Database
```

**Consistency with design docs.** If a recent `AMTCZ-` ticket modified the components being documented, the architecture doc must reflect the post-ticket state. Check `docs/tasks/` for relevant tickets before writing.

---

## Quality gate (self-check before finishing)

- [ ] All 7 files generated (no partial sets)
- [ ] README.md contains only navigation, no architectural content
- [ ] architecture.md contains an ASCII component diagram
- [ ] Grey areas are marked TBD, not filled with guesses
- [ ] No content copied verbatim from source code
- [ ] `docs/architecture/README.md` updated with link to new module
- [ ] Folder name is kebab-case and confirmed with user
- [ ] Consistent with any recent AMTCZ tickets that touched these components
