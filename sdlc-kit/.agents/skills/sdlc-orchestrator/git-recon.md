# Git Recon

Run before initial research and on resume, in the task worktree. Use the
available shell and cap displayed output with `Select-Object -First N` in
PowerShell or `head -n N` in POSIX shells. Run dependent commands sequentially
and check exit status before using their output. These are read-only checks;
fetch is separate and only needed to refresh remote state.

1. Read `git branch --show-current`, `git status --short --branch`, and
   `git log -1 --format="%h %cr %s"`. An empty branch means detached HEAD.
2. Resolve the remote default with
   `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`.
   Preserve the returned ref (including nested branch names). If absent,
   inspect available refs with `git branch -r` and repository configuration;
   do not assume main/master when neither exists.
3. Run `git merge-base HEAD <resolved-default-ref>` and retain the resulting
   SHA as the task base. If no base exists, report unavailable comparisons;
   do not run range commands with an empty base.
4. Show at most 10 entries from `git log --oneline <base>..HEAD`, 20 rows
   from `git diff --name-status <base>...HEAD`, and the summary line of
   `git diff --stat <base>...HEAD`.
5. Inspect upstream only if `git rev-parse --verify "@{u}"` succeeds.
   Quote `"@{u}"` in PowerShell so it is passed literally to Git.

## Targeted Checks

| Question | Command |
|---|---|
| Uncommitted files, including untracked | `git status --porcelain` |
| Unstaged/staged summary | `git diff --stat` / `git diff --cached --stat` |
| Phase boundaries | `git log --oneline --grep="^<id>: phase" <base>..HEAD` |
| Phase diff | `git diff --stat <previous-sha>..<phase-sha>` |
| Scope drift | `git diff --name-only <base>...HEAD` compared to plan Scope |
| Unpushed commits | `git log --oneline "@{u}..HEAD"` after upstream check |
| Last task-file change | `git log -1 --format="%h %cr %s" -- docs/tasks/<id>/` |
| Upstream scope changes | `git log --oneline HEAD..<default-ref> -- <scope-paths>` |
| Stashes | `git stash list` (display at most 3) |
| Phase checkpoint | `git log --format=%H --grep="^<id>: phase N" -1` |

Include untracked task files when reporting changes; diff alone omits them.
Do not stash, reset, switch over user changes, or rewrite history as recon.
For new task work, fetch the required remote and create the task branch from
its resolved default ref, using an isolated worktree if needed. Resumed work
keeps its existing branch. Record the actual base for later final reports.
Workers receive the relevant base, diff range, and scope in their dispatch;
full source-control recon stays in the main thread.
