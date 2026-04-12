---
name: business-doc-writer
description: Governs the structure, content rules, and generation process for business documentation sets in the Amatsucozy workflow. Read this skill whenever *create-business-doc (*cbd) is triggered. Covers scope assessment, context gathering, business doc generation, and index updates. CRITICAL: this skill forbids reading source code or referencing technical architecture docs.
---

# Business Doc Writer

Defines how to create a complete business documentation set.
Read this before generating any files in `docs/business/`.

---

## Template

Always read `.amtcz/templates/business-doc-template.md` before generating any file.
Use it as the base content for each file, customising title and purpose per file role.

---

## Allowed information sources

- ✅ User-provided context and descriptions
- ✅ Existing scattered documents the user provides
- ✅ Jira/Confluence pages the user points to
- ✅ Existing `docs/business/` files

## Forbidden information sources (hard rule)

- ❌ Source code — do not open, read, or reference any code files
- ❌ `docs/architecture/` — do not read or link to technical architecture documentation
- ❌ Database schemas, API specs, or implementation guides

**Why this rule is hard:** Business documentation is written for stakeholders who do not read code. If it references technical implementation details, it becomes inaccessible to its intended audience and creates a maintenance dependency — every refactor potentially invalidates the business doc. The business doc must describe *what the system does* from the user's perspective, not *how it does it*.

The test: could a non-technical product manager or business analyst read this document and understand it fully, without access to the codebase? If not, rewrite until they can.

---

## Process

### Step 1: Scope assessment

Determine whether the request is:
- **Global/system-wide** — covers the whole system's business logic → target `docs/business/` directly
- **Specific feature** — covers a single workflow or feature → target `docs/business/[topic]/`

Ask the user to confirm scope if unclear.

### Step 2: Context gathering

Ask the user to provide:
- A description of the feature or system in business terms
- Any existing scattered documentation (copy-paste, links, attachments)
- Pointers to Jira epics, Confluence pages, or product specs
- Key stakeholders and user personas involved

**Do not begin drafting until sufficient context is in hand.** A business doc derived from insufficient context is worse than no doc — it creates false confidence. If context is thin, ask targeted questions:

- Who are the users of this feature and what problem does it solve for them?
- What are the key business rules (conditions, thresholds, exceptions)?
- What are the main user workflows, step by step?
- What are the acceptance criteria for each workflow?
- What edge cases or exceptions have been identified?

### Step 3: Location determination

For specific feature requests:
1. Check `docs/business/` for an existing folder matching the topic
2. If found: confirm whether to update it or create a new sub-folder
3. If not found: confirm the topic name (kebab-case) before creating

### Step 4: Generate all four files

Create all four files in the target folder in a single pass. Do not generate partial sets.

```
[target]/
├── README.md          ← Index & navigation
├── overview.md        ← Executive summary & context
├── business-logic.md  ← Rules, workflows, decisions
└── user-stories.md    ← Scenarios & acceptance criteria
```

#### File purpose guide

**README.md** — index only. Lists the other three files with one-line descriptions. Links to each. No business content here.

**overview.md** — the executive summary. What is this feature or system? Who are the users? What business problem does it solve? What is the scope (what it does and doesn't cover)? Who are the key stakeholders? What are the high-level success metrics?

**business-logic.md** — the heart of the doc. All business rules, conditions, thresholds, and exceptions. Workflows described step-by-step in plain language. Decision trees for branching logic. Special cases and how they're handled. This section must be complete enough that a new team member could understand how the system behaves without asking anyone.

Format complex workflows as numbered steps:
```
## Order approval workflow
1. Customer submits order
2. System checks inventory availability
   - If available: proceed to step 3
   - If unavailable: notify customer, offer backorder option
3. System validates payment method
   ...
```

**user-stories.md** — user-facing scenarios and acceptance criteria. Each story follows the format:

```
## [Story title]
**As a** [persona]
**I want to** [action]
**So that** [outcome]

### Acceptance criteria
- [ ] Given [context], when [action], then [result]
- [ ] ...
```

### Step 5: Index update

Update (or create) `docs/business/README.md` to link to the new module:

```markdown
## Features
- [order-approval](./order-approval/) — Order approval workflow and business rules
```

---

## Content quality rules

**Plain language only.** No technical jargon. No references to classes, functions, tables, or APIs. Describe behaviour from the user's perspective.

- Bad: "The `OrderService.approve()` method checks the `inventory_count` column"
- Good: "The system checks whether the requested quantity is available in stock"

**No speculation.** If a business rule is unclear from the provided context, mark it explicitly:
```
> **TBD:** Confirm with the Product team whether orders over €10,000 require manual approval.
```

Never invent business rules to fill gaps.

**Consistency.** Use consistent terminology throughout. If the user calls it "order" in their context, call it "order" everywhere — not "purchase," "transaction," or "request."

**Complete workflows.** Describe the full end-to-end path, including:
- What triggers the workflow
- Every step the user or system takes
- All branching conditions (happy path AND exceptions)
- How the workflow ends (success states and failure states)

---

## Quality gate (self-check before finishing)

- [ ] All 4 files generated (no partial sets)
- [ ] README.md contains only navigation
- [ ] No source code referenced or read
- [ ] No links to `docs/architecture/`
- [ ] All business rules stated explicitly (no "TBD" unless genuinely unknown)
- [ ] Workflows describe full end-to-end paths including exception handling
- [ ] User stories include concrete acceptance criteria
- [ ] Plain language throughout — passes the non-technical reader test
- [ ] `docs/business/README.md` updated with link to new module
- [ ] Folder name is kebab-case and confirmed with user
- [ ] Terminology is consistent with user-provided context
