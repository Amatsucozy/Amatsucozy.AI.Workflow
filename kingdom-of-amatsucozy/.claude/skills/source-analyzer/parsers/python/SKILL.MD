---
name: parser-python
type: provider
description: Extracts Python Class, Method, and Function mapping using docstrings and decorators.
---

# Skill: Python Logic Extractor

## Extraction Rules
1. **Classes**: Identify by `class Name:`. 
   - Capture inheritance (e.g., `class UserService(BaseService):`) to provide context on shared logic.
2. **Functions/Methods**: Identify by `def function_name(args):`.
3. **Functional Context**:
    - **Docstrings**: Prioritize the `""" Triple Quote """` block immediately following the definition (PEP 257).
    - **Decorators**: For Web Frameworks, map route decorators (e.g., `@app.get("/")`, `@router.post`) to the functional description.
    - **Type Hints**: Use type hints (e.g., `def get_user(id: int) -> User:`) to describe data flow.
4. **Script Level**: If a file has no classes, treat top-level functions as the primary "Entities."

## Standardized Output
Return a JSON object for the Orchestrator:
{
  "type": "Python",
  "entity": "[ClassName or 'Global Functions']",
  "path": "[FilePath]",
  "summary": "[Module-level docstring or brief overview]",
  "functions": [
    "method_name(args): [Docstring summary or logic guess]"
  ]
}