# Git Recon — source-control awareness for the orchestrator

All commands are output-capped to keep context small.

## Recon block (one command, ~15 lines out)

Sets `$DEFAULT` and `$BASE` (the branch point against the default branch) for
the commands below.

```bash
DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); DEFAULT=${DEFAULT:-main}; \
BASE=$(git merge-base HEAD "origin/$DEFAULT" 2>/dev/null || git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null); \
[ -z "$BASE" ] && echo "WARN: no base ref — comparisons unreliable"; \
echo "branch : $(git branch --show-current)  ($(git log -1 --format='%h %cr'))"; \
echo "sync   : $(git status -sb | head -1 | grep -o '\[.*\]' || echo 'in sync / no upstream')"; \
echo "dirty  : $(git status --porcelain | wc -l) file(s) uncommitted"; \
echo "commits on branch:"; git log --oneline "$BASE"..HEAD | head -10; \
echo "files vs base:"; git diff --name-status "$BASE"...HEAD | head -20; \
echo "diff size: $(git diff --stat "$BASE"...HEAD | tail -1)"
```

Run it at invocation, after a resume, and before the first researcher
dispatch — that last run catches a dirty tree or wrong branch before the task
branch is created over it. During implementation a
`git branch --show-current` check is enough. Never run recon inside
subagents; they get their scope in the dispatch.

## Targeted commands

| Question | Command |
|---|---|
| Uncommitted files | `git status --porcelain \| head -20` |
| Uncommitted diff, summarized | `git diff --stat \| tail -5` (staged: add `--cached`) |
| Commits on this branch | `git log --oneline "$BASE"..HEAD \| head -15` |
| Phase-boundary commits | `git log --oneline --grep '^<id>: phase' "$BASE"..HEAD` |
| Diff of one phase | `git diff --stat <phaseN-sha>..<phaseN+1-sha> \| tail -5` |
| All files changed on branch | `git diff --name-status "$BASE"...HEAD \| head -40` |
| Scope check vs plan | `git diff --name-only "$BASE"...HEAD \| sort` → anything not in a plan Scope list is scope-drift |
| Unpushed commits | `git log --oneline @{u}..HEAD 2>/dev/null \| wc -l` |
| Last touch per task file | `git log -1 --format='%h %cr %s' -- docs/tasks/<id>/` |
| Upstream changes to scope files | `git fetch -q && git log --oneline HEAD.."origin/$DEFAULT" -- <scope paths> \| head -5` |
| Stashes | `git stash list \| head -3` |
| Rollback target for phase N | `git log --format='%H' --grep '^<id>: phase N' -1` |
| Refresh default branch before branching | `git fetch origin && git checkout "$DEFAULT" && git pull origin "$DEFAULT"` |

On a long-lived branch, check upstream changes to scope files before
dispatching a phase — drift there is a re-plan signal, cheaper caught before
implementation than at a gate.
