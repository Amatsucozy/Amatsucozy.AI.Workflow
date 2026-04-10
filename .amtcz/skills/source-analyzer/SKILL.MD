---
name: source-analyzer
type: orchestrator
parameters:
  - name: project_name
    optional: true
    description: "The folder name of the specific project to index (e.g., 'project_Csharp')."
dependencies: [ "parsers/*" ]
description: "Scans the codebase to generate sharded context.md files and a master index map."
---

# Skill: Targeted Source Analyzer (Writer)

## Procedures
1. **Master Map Knowledge Acquisition**: 
    - **Check**: Look for the existence of `/.amtcz/context.md`.
    - **IF FOUND**: Read the "Project Path Map" to determine the indexing status of all modules.
    - **IF MISSING**: Proceed to Step 2 for initial repository discovery.

2. **Target Selection Logic**:
    - **IF `project_name` is provided**: Validate the directory exists. Index ONLY this folder.
    - **IF NO `project_name` is provided**:
        - **Scenario A (Master Map Exists)**: Scan the "Project Path Map" table for the first project currently marked as `[NOT INDEXED]`. Select this as the target.
        - **Scenario B (Master Map Missing)**: Identify all project folders in the root using markers (e.g., `.csproj`, `package.json`, `requirements.txt`). Select the first one alphabetically.
        - **Scenario C (All Indexed)**: If the Master Map shows all projects are already linked to local maps, notify the user: *"All detected projects are already indexed. Use `*idx [name]` to force a refresh on a specific module."*

3. **System Notification**: 
    - Immediately inform the user of the selection: *"No project specified. Based on the Master Map, I am indexing the next unindexed project: `{target_project}`."*

4. **Local Indexing**:
    - Invoke the matching `parsers/` skill (csharp, angular, or python) for all files within the selected project.
    - Generate a detailed mapping of Classes, Interfaces, and Methods.

5. **Persistence & Master Map Update**:
    - **Local Map**: Write the detailed analysis to `/{target_project}/context.md`.
    - **Master Map**: Update or create `/.amtcz/context.md`.
        - **General Idea**: Provide a factual 2-3 sentence summary of the repository's purpose.
        - **Project Path Map**: Update the "Local Context Map" link for the target project. Ensure all other detected but unindexed projects are listed as `[NOT INDEXED]`.

## 🛡️ Anti-Hallucination Guardrails
- **Zero-Inference Rule**: Do not guess tech stacks or purposes. If markers are missing, list as `Tech Stack: Unknown`.
- **Factual Mapping**: Only list "Local Context Map" paths that actually exist on disk.
- **State Integrity**: When run without a name, strictly index the **first** `[NOT INDEXED]` entry to ensure predictable progress.
- **No Ghost Entities**: Only include classes/methods explicitly identified by language parsers.

## Master Map Schema (`/.amtcz/context.md`)
# Repository Master Context

**General Idea**: [A high-level summary of the repository's purpose]

## Project Path Map
| Project Name | Path | Tech Stack | Local Context Map |
| :--- | :--- | :--- | :--- |
| {Name} | {Path} | {Tech} | {Path}/context.md OR [NOT INDEXED] |

## Local Map Schema (`/{project}/context.md`)
| Layer | Entity | File Path | Functional Description |
| :--- | :--- | :--- | :--- |
| {Layer} | {Class/Interface} | {Path} | {MethodName}: {Action} |