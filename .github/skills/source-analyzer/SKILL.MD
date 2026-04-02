---
name: source-analyzer
type: orchestrator
dependencies: [ "parsers/*" ]
description: Scans the codebase to generate or update a `context.md` file.
---

# Skill: Source Analyzer (Writer)

## Procedures
1. **Inventory**: Walk the directory tree (ignoring `node_modules`, `bin`, `obj`, `dist`).
2. **Language Detection**: Identify file extensions (`.cs` -> csharp, `.ts` -> angular).
3. **Delegation**: For each relevant file, invoke the matching `parsers/` skill to extract structural data.
4. **Context Construction**:
    - Group by **Layer** (e.g., Backend vs Frontend).
    - Map **Interface/Class** to **File Path**.
    - Map **Method/Function** to **Class** and describe its functionality.
5. **Persistence**: Write the final mapping to `context.md` in the project root.

## Output Schema
| Layer | Entity | File Path | Functional Description |
| :--- | :--- | :--- | :--- |
| {Layer} | {Class/Interface} | {Path} | {MethodName}: {Action} |