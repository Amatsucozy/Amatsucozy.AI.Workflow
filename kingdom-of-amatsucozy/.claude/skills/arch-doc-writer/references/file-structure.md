# Architecture Doc File Structure

Read when generating the 7-file architecture documentation set.

---

## README.md — Index only

Navigation only. No architectural content.

```markdown
# {Module} — Architecture

{One sentence description.}

## Contents
- [architecture.md](./architecture.md) — high-level design and component map
- [api-specification.md](./api-specification.md) — endpoints and schemas
- [implementation-guide.md](./implementation-guide.md) — code examples and patterns
- [integration.md](./integration.md) — external systems and contracts
- [operations.md](./operations.md) — monitoring, alerting, security
- [deployment.md](./deployment.md) — infrastructure and CI/CD
```

---

## architecture.md

- Overview: what this module does and why it exists
- ASCII component diagram: relationships between components (not a list of names)
- Key architectural decisions and rationale
- Known trade-offs

---

## api-specification.md

- Every public interface: HTTP endpoints (method, path, request/response schemas, error codes)
- Message queue formats: payload structure, routing keys
- Example request/response pairs for each endpoint

---

## implementation-guide.md

- Key patterns used and why they were chosen
- Non-obvious behaviours and gotchas
- Code examples for common operations
- Test setup instructions

---

## integration.md

For each external system this module talks to:
- Contract (API, message format, protocol)
- How authentication works
- Failure modes and how they are handled
- How to test the integration locally

---

## operations.md

- Key metrics and what they mean
- Alerting thresholds and escalation paths
- Security boundaries and access controls
- Runbooks for known failure scenarios

---

## deployment.md

- How resources are provisioned
- Environment variables and their purpose
- CI/CD pipeline stages
- Deploy procedure per environment
- Rollback steps
