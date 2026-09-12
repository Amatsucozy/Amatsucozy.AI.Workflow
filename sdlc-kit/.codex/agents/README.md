# Codex SDLC agents

These standalone TOML definitions mirror the four roles in `.claude/agents/`:

| Agent | Responsibility |
|---|---|
| `researcher` | Locate relevant code and return a research brief without edits or builds. |
| `engineer` | Implement one approved phase within its declared scope; report C# diagnostics. |
| `reviewer` | Independently execute verification gates, builds, tests, and acceptance checks. |
| `pr-reviewer` | Draft evidence-based comments on another author's PR for human approval. |

The companion [`../../AGENTS.md`](../../AGENTS.md) adapts the kit's project
instructions for Codex, including experience routing and MCP references.
Place it at the target project root, merging with existing instructions.

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
The 10 Codex skill counterparts live in [`../../.agents/skills/`](../../.agents/skills/).
Copy that directory to your target project's `.agents/skills/`, or copy its
skill folders to `~/.agents/skills/` for personal use. Codex discovers them
when launched from the target project (from `sdlc-kit/` when using this kit).
Invoke a skill with `$skill-name`, for example `$sdlc-orchestrator` or
`$run-build`. This uses the documented
[Codex skill location and invocation format](https://learn.chatgpt.com/docs/build-skills).

The counterparts preserve the task documents, build/test verdict contracts,
session scoring rubric, and SonarQube mapping template. They adapt agent
dispatch, tool discovery, shell usage, and report paths for Codex. Configure
amtcz for build/test tools and Roslyn for semantic C# operations; SonarQube
skills need SonarQube access, and project mapping also needs GitHub search.
Skill instructions do not install agents or MCP servers.

Agents prefer installed Codex skills, then the kit's `.agents/skills/`, and
can read `.claude/skills/<name>/SKILL.md` as a legacy fallback. Copying these agent files alone
does not install skills or configure MCP servers. Project map and Roslyn
orientation references prefer `AGENTS.md`, with `CLAUDE.md` as a fallback.

The researcher sets a read-only sandbox. The other roles inherit the session's
sandbox so implementation tools and permitted build/test outputs can work;
reviewers still must not edit source files. Role-specific tool restrictions
are instructions, not enforced tool allowlists. Parent runtime permission
overrides can supersede agent sandbox defaults.
