---
name: parser-angular
type: provider
description: Extracts Angular Component/Service metadata and UI logic.
---

# Skill: Angular Parser

## Extraction Rules
- **Components**: 
    - Identify via `@Component`. 
    - Link `templateUrl` and `styleUrls` as metadata.
    - Functional mapping: Note `@Input/@Output` as the "API" of the component.
- **Services**: 
    - Identify via `@Injectable`.
    - Functional mapping: Note public methods and their `HttpClient` calls.
- **Models**: 
    - Identify `export interface` or `export class` for data shapes.
- **Output**: Return standardized JSON: `{ "entity": string, "path": string, "functions": string[] }`