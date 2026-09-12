# Codex SDLC agents

These standalone TOML definitions mirror the four roles in `.claude/agents/`:

| Agent | Responsibility |
|---|---|
| `researcher` | Locate relevant code and return a research brief without edits or builds. |
| `engineer` | Implement one approved phase within its declared scope; report C# diagnostics. |
| `reviewer` | Independently execute verification gates, builds, tests, and acceptance checks. |
| `pr-reviewer` | Draft evidence-based comments on another author's PR for human approval. |

Copy the TOML files into your target project's `.codex/agents/` directory, or
into `~/.codex/agents/` for personal use. When working from `sdlc-kit/`, they
already occupy the project directory. Ask Codex explicitly to use the named
agent, supplying the inputs required by its Input Contract. For example:
“Use the researcher agent to map the invoice creation flow.”

The agents use the current [Codex custom-agent format](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents).
No separate role registration in `config.toml` is needed. Model and reasoning
effort are inherited; Claude's `haiku` and `sonnet` settings are not carried over.

Configure the `roslyn` MCP server in the target Codex environment for semantic
C# operations. The reviewer also requires the `run-build` and `run-test` skills.
Agents prefer installed Codex skills and can read the corresponding repository
`.claude/skills/<name>/SKILL.md` when available. Copying these agent files alone
does not install skills or configure MCP servers. Project map and Roslyn
orientation references prefer `AGENTS.md`, with `CLAUDE.md` as a fallback.

The researcher sets a read-only sandbox. The other roles inherit the session's
sandbox so implementation tools and permitted build/test outputs can work;
reviewers still must not edit source files. Role-specific tool restrictions
are instructions, not enforced tool allowlists. Parent runtime permission
overrides can supersede agent sandbox defaults.
