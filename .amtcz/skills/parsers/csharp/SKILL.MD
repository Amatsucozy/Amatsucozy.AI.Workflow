---
name: parser-csharp
type: provider
description: Extracts .NET Class/Interface mapping and XML documentation.
---

# Skill: .NET Parser

## Extraction Rules
- **Entities**: Identify `public interface` and `public class`.
- **Functional Context**:
    - Use `/// <summary>` tags if available.
    - For Controllers: Map `[Route]` and `[Http*]` attributes to the functional description.
    - For Services: Identify dependencies in the constructor to explain "Functional Connectivity."
- **Output**: Return standardized JSON: `{ "entity": string, "path": string, "functions": string[] }`