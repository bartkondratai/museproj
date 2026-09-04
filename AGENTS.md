# Codex project instructions

## DeepSeek code-generation delegation

When a task is well-scoped net-new code generation—such as a function, component,
script, query, or similar implementation—delegate the initial implementation to
DeepSeek by running:

```sh
node scripts/ask-deepseek.js "<complete prompt>"
```

Before calling the script, gather and include the relevant file contents,
interfaces, repository conventions, constraints, and acceptance criteria in the
prompt. The script has no access to this conversation or the repository context
unless that context is pasted into the prompt.

Review the returned implementation before applying it. Check that it parses,
matches the repository's conventions, and uses APIs that exist in this codebase.
If it needs correction, re-prompt DeepSeek with the concrete issue and relevant
context. Do not silently replace the delegated implementation with an independently
written one.

Do not delegate planning, architecture decisions, debugging, investigation, or
research. This delegation rule applies only to net-new code generation.

Use the existing `scripts/ask-deepseek.js` and its existing Bitwarden/OpenRouter
key-resolution path. Do not modify that script, `.claude/agents/deepseek-coder.md`,
or `CLAUDE.md`; those belong to the Claude Code setup. Never print API keys,
Bitwarden passwords, or session tokens.
