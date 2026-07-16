# Context Graph Schemas

Reference schemas for both levels of the context graph.
Source-indexer writes these. Source-navigator reads them.

---

## Master Schema — `.amtcz/context.md`

```markdown
# Repository Master Context

**Repo:** {RepoName} | **Type:** {monorepo | polyrepo} | **Last Updated:** {YYYY-MM-DD}

## Project Map

| Project | Path | Owns | Tech | Context |
|---------|------|------|------|---------|
| API | /src/api | HTTP endpoints, auth routes, request validation, API versioning | C#/.NET | /src/api/context.md |
| Core | /src/core | Business logic, domain services, interfaces, validation rules | C#/.NET | /src/core/context.md |
| Worker | /src/worker | Background jobs, email dispatch, PDF export, scheduled tasks | Python | /src/worker/context.md |
| Frontend | /src/frontend | UI components, routing, state management, API integration | Angular | /src/frontend/context.md |

## External References

| Name | Location | Owns | Notes |
|------|----------|------|-------|
| SharedLib | https://github.com/org/shared-lib | Shared DTOs, base classes, enums | [NOT LINKED] |
| AuthProvider | https://github.com/org/auth | JWT issuance, token validation | [NOT LINKED] |
```

**Column rules:**
- `Project` — short display name, title case
- `Path` — relative to repo root, no trailing slash
- `Owns` — 3–6 comma-separated plain-language phrases; this is the
  primary lookup field for source-navigator
- `Tech` — framework/language, e.g. `C#/.NET`, `Python/FastAPI`,
  `Angular`, `Node/Express`
- `Context` — relative path to the project's context.md, or `[NOT INDEXED]`
  if not yet built, or `[REMOVED]` if the project no longer exists on disk

---

## Project-Level Schema — `/{project}/context.md`

```markdown
# {ProjectName} — Context Map

**Last Indexed:** {YYYY-MM-DD}

## Entity Map

| Layer | Class / Interface | File | Public Methods |
|-------|-------------------|------|----------------|
| Controller | UserController | /src/api/Controllers/UserController.cs | GetById(id), Create(dto), Delete(id) |
| Controller | AuthController ⚠️ mixed | /src/api/Controllers/AuthController.cs | Login(request), Refresh(token) |
| Interface | IUserService | /src/api/Interfaces/IUserService.cs | GetById(id), Create(dto), Delete(id) |
| Interface | IUserRepository | /src/api/Interfaces/IUserRepository.cs | FindById(id), Save(entity), Delete(id) |
| Model | UserDto | /src/api/Models/UserDto.cs | — |
| Model | CreateUserRequest | /src/api/Models/CreateUserRequest.cs | — |
| Service | UserService | /src/api/Services/UserService.cs | GetById(id), Create(dto), Delete(id) |
| Repository | UserRepository | /src/api/Repositories/UserRepository.cs | FindById(id), Save(entity), Delete(id) |

## Route Map

| Method | Route | Handler |
|--------|-------|---------|
| GET | /api/users/{id} | UserController.GetById |
| POST | /api/users | UserController.Create |
| DELETE | /api/users/{id} | UserController.Delete |
| POST | /api/auth/login | AuthController.Login |
| POST | /api/auth/refresh | AuthController.Refresh |
| GET | /api/orders/{id} | [UNRESOLVED] |
```

**Column rules:**
- `Layer` — exactly one value from the Layer Taxonomy in SKILL.md
- `Class / Interface` — exact name as declared in source; append ` ⚠️ mixed`
  if the class spans multiple layers
- `File` — path relative to repo root
- `Public Methods` — comma-separated `name(params)` signatures;
  write `—` if none exist
- Route `Handler` — `ClassName.MethodName`; write `[UNRESOLVED]` if the
  binding cannot be traced to a specific class

**Sorting:**
Entity Map rows must be sorted: Layer (alphabetical), then Class name
(alphabetical) within each layer group.

Route Map rows must be sorted: by Route path, then by Method.
