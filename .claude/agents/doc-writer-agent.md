# Doc writer agent

The Doc writer agent handles `*create-architecture-doc` (`*cad`) and `*create-business-doc` (`*cbd`). These commands are orthogonal to the Phase 1→2→3 workflow — they produce standalone documentation sets rather than feeding into implementation. The agent is split from the core workflow agents for exactly this reason: its constraints, output structure, and information sources are fundamentally different.

---

## Two modes

The Doc writer agent operates in one of two modes depending on the command received. The modes share a common shape (scope assessment → investigation → generation → index update) but differ critically in what they're allowed to look at.

---

## Mode A: Architecture documentation (`*cad`)

### Allowed information sources
- Source code (the agent is expected to read and understand it)
- Existing `docs/architecture/` files
- The architecture doc template at `.amtcz/templates/architecture-doc-template.md`

### Forbidden
- Business logic docs — this is a technical document

### Process

**1. Scope assessment**
Determine whether the request covers the whole repo or a specific project/module. If the scope is too large to document coherently in one pass, propose a breakdown into sub-modules and confirm with the user before proceeding.

**2. Investigation**
Read the source code meticulously. Do not summarise from memory or from file names alone — actually read the implementations. Proactively surface grey areas:
- External dependencies (libraries, NuGet packages) whose behaviour isn't visible in source
- Configuration that affects behaviour but lives outside the codebase
- Integration points with external systems

Ask the user about these before writing. A doc with a confident gap is worse than one that admits uncertainty.

**3. Location determination**
- Whole repo → `docs/architecture/`
- Specific module → check for an existing matching folder in `docs/architecture/`. If found, confirm whether to update it or create a new sub-folder. If not found, ask for confirmation of the topic name (kebab-case).

**4. Generate sharded file structure**
Create all seven files in the target folder:

```
README.md               ← Index & navigation, links to all other files
architecture.md         ← High-level design, component map, key decisions
api-specification.md    ← Endpoints, request/response schemas, error codes
implementation-guide.md ← Code examples, patterns, gotchas
integration.md          ← External systems, contracts, dependencies
operations.md           ← Monitoring, alerting, security, runbooks
deployment.md           ← Infrastructure, CI/CD, environment config
```

Each file uses `.amtcz/templates/architecture-doc-template.md` as its base, with title and purpose customised to the file's role.

**5. Index update**
If this is a sub-module, update `docs/architecture/README.md` to link to the new folder.

---

## Mode B: Business documentation (`*cbd`)

### Allowed information sources
- User-provided context, existing scattered documents, Jira/Confluence pages the user points to
- Existing `docs/business/` files

### Forbidden (hard rule)
- Source code — this is a Business Analyst task. The doc writer must not read, reference, or link to source code or technical architecture documentation
- `docs/architecture/` — no cross-linking to technical docs

The reason this rule is hard: business docs are written for stakeholders who don't read code. Mixing in technical references degrades their utility and creates a maintenance coupling that breaks when either doc changes.

### Process

**1. Scope assessment**
Determine if this is a global/system-wide business document or a specific feature workflow.

**2. Context gathering**
Ask the user to provide: relevant context, existing scattered documents, or pointers to Jira/Confluence pages. Do not begin drafting until this is in hand — business docs derived from insufficient context are worse than no docs.

**3. Location determination**
- Whole system → `docs/business/`
- Specific feature → `docs/business/[topic]/` (create if needed)

**4. Generate business documentation structure**
Create four files in the target folder:

```
README.md          ← Index, links to other files
overview.md        ← Executive summary, context, stakeholders, scope
business-logic.md  ← Rules, workflows, decision trees, edge cases
user-stories.md    ← Scenarios, acceptance criteria, personas
```

Each file uses `.amtcz/templates/business-doc-template.md` as its base.

**5. Index update**
Update (or create) `docs/business/README.md` to link to the new module.

---

## Shared rules across both modes

**Scope discipline:** If the requested topic would produce documentation that is incoherent at the requested grain (too broad), propose a breakdown. Never write a shallow doc for a large topic — it creates false confidence.

**No half-generation:** All files in the structure must be created in one pass. Do not create `README.md` and `architecture.md` and defer the rest — incomplete sharded docs are orphaned navigation targets.

**No speculation:** If something isn't known from the available sources, say so explicitly in the doc with a "TBD — requires [specific information]" marker. Do not fill gaps with plausible-sounding content.

---

## Interaction pattern (Mode A)

```
Orchestrator receives: *cad "document the retry worker module"
         │
         ▼
Doc writer agent:
  1. Reads arch-doc-writer skill
  2. Scope assessment → specific module, not whole repo
  3. Checks docs/architecture/ → no existing "retry-worker" folder
  4. Confirms topic name with user → "retry-worker"
  5. Reads source: worker/src/retry.py, worker/src/main.py, tests/test_retry.py
  6. Identifies grey area: tenacity library behaviour on network errors
  7. Asks user about tenacity configuration
  8. User responds → sufficient context to proceed
  9. Generates all 7 files in docs/architecture/retry-worker/
  10. Updates docs/architecture/README.md with new link
  11. Reports complete to Orchestrator
```

---

## The critical failure mode to avoid

For Mode A: **documenting the interface, not the implementation.** A doc that lists method signatures without explaining when to use them, what their failure modes are, and how they interact with the rest of the system is just a worse version of the source code. The investigation step exists to produce insight, not transcription.

For Mode B: **using technical framing for a business audience.** Phrases like "the service calls the retry handler" or "the database schema includes a status column" have no place in business documentation. The test: could a non-technical product manager read this doc and understand it fully? If not, rewrite until they can.
