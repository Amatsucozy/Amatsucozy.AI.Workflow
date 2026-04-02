---
name: source-fast-search
type: discovery
description: Answers project-related questions using the `context.md` file.
---

# Skill: Source Fast Search (Reader)

## Logic
1. **Check**: Look for `context.md` in the root directory.
2. **Branching**:
    - **IF FOUND**: Parse the file. Match user keywords (e.g., "Order processing") against the "Functional Description" column. Provide the exact file and class name.
    - **IF MISSING**: Inform the user: *"I don't have a context map for this project yet. Use the 'source-analyzer' skill to index it for quick retrieval."*
3. **Execution**: If the user asks for code details found in the map, only open the specific file identified.

## Success Criteria
- Minimize tokens by reading the 1KB `context.md` instead of 1MB of source code.