---
name: source-fast-search
description: Answers project-related questions using the master map and sharded context files.
cache_control: ephemeral
---

# Skill: Source Fast Search (Sharded Reader)

## Logic
1. **Master Map Verification**: 
    - Always check `/.amtcz/context.md` first.
    - If missing, stop and notify the user: *"I don't have a project context map yet. Please use `*index-project` to initialize the environment."*
2. **Project Identification**:
    - Match user keywords (e.g., "API," "auth," "frontend") against the "Project Name" and "Tech Stack" in the master map.
3. **Sharded Retrieval**:
    - Retrieve the "Local Context Map" path for the relevant project.
    - Open only that specific `context.md`.
    - Match specific logic or class requests against the "Functional Description" column.
4. **Unindexed Project Handling**:
    - If the user asks about a project that is listed in the Master Map but has no local `context.md` link, respond with:
      *"I know about the '{project}' module, but it hasn't been indexed for deep search yet. Would you like me to run `*index-project {project}` now?"*

## Execution Rules
- **Token Efficiency**: Never perform a recursive file search if the answer can be located via the sharded context files.
- **Direct Access**: If a file path is found in the context map, open that file directly to answer detailed implementation questions.

## Success Criteria
- Provide the exact File Path and Class Name within 1-2 turns.
- Avoid "hallucinating" structure by strictly adhering to what is documented in the maps.