# Git Recon — source-control awareness for the orchestrator

All commands are output-capped by design (context hygiene). `$BASE` is the
branch-point against the default branch — compute it once per session:

```bash
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); \
BASE=$(git merge-base HEAD "origin/${DEFAULT:-main}" 2>/dev/null || git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null); \
[ -z "$BASE" ] && echo "WARN: no base ref found — branch comparisons below are unreliable"
```

## The recon block (run at invocation/resume — one command, ~15 lines out)

```bash
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); \
BASE=$(git merge-base HEAD "origin/${DEFAULT:-main}" 2>/dev/null || git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null); \
[ -z "$BASE" ] && echo "WARN: no base ref — comparisons unreliable"; \
echo "branch : $(git branch --show-current)  ($(git log -1 --format='%h %cr'))"; \
echo "sync   : $(git status -sb | head -1 | grep -o '\[.*\]' || echo 'in sync / no upstream')"; \
echo "dirty  : $(git status --porcelain | wc -l) file(s) uncommitted"; \
echo "commits on branch:"; git log --oneline "$BASE"..HEAD | head -10; \
echo "files vs base:"; git diff --name-status "$BASE"...HEAD | head -20; \
echo "diff size: $(git diff --stat "$BASE"...HEAD | tail -1)"
```

## Targeted commands

| Question | Command |
|---|---|
| What's uncommitted right now? | `git status --porcelain \| head -20` |
| Uncommitted diff, summarized | `git diff --stat \| tail -5` (staged: add `--cached`) |
| Commits this branch, phase markers visible | `git log --oneline "$BASE"..HEAD \| head -15` |
| Phase-boundary commits only | `git log --oneline --grep '^<id>: phase' "$BASE"..HEAD` |
| Diff of one phase | `git diff --stat <phaseN-sha>..<phaseN+1-sha> \| tail -5` |
| All files changed on branch | `git diff --name-status "$BASE"...HEAD \| head -40` |
| Scope check vs plan | `git diff --name-only "$BASE"...HEAD \| sort` → compare against the plan's Scope lists; anything unlisted is scope-drift |
| Anything unpushed? | `git log --oneline @{u}..HEAD 2>/dev/null \| wc -l` |
| Last touch per task file | `git log -1 --format='%h %cr %s' -- docs/tasks/<id>/` |
| Who else changed my scope files upstream? | `git fetch -q && git log --oneline HEAD..origin/main -- <scope paths> \| head -5` |
| Stashes lying around | `git stash list \| head -3` |
| Rollback target for phase N | `git log --format='%H' --grep '^<id>: phase N' -1` |

## Usage rules

- Recon block: once at invocation, and after any resume — not every turn.
- Turn reports pull "Changed this turn" from `git diff --stat | tail -3`, nothing more.
- Never run recon inside subagents — they receive their scope in the dispatch;
  source-control awareness is orchestrator judgment.
- The "who else changed my scope files" check is worth running before dispatching
  a phase on a long-lived branch — upstream drift in scope files is a re-plan
  signal, cheaper caught before implementation than at a gate.
