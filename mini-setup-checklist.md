# Mac Mini Setup Checklist — parity with this MacBook Pro

Goal: `bartoszs-mac-mini` can run Claude Desktop / Claude Code on this repo with
the same Bitwarden, CLI, and deploy access as this machine. Tailscale is already
connected (confirmed in your screenshot), so network reachability is done.

Run these steps **on the mini**, not from here — I can't reach that machine.

## 1. Apps

- [ ] Install **Claude Desktop** (claude.ai/download) — log in with the same
      Anthropic account.
- [ ] Install **Claude Code** CLI: `npm install -g @anthropic-ai/claude-code`
      (or however you installed it here — confirm with `which claude` on this
      machine if unsure).
- [ ] Install **Bitwarden desktop app** and/or CLI (`brew install bitwarden-cli`
      gives you `bw`; confirm path matches `/opt/homebrew/bin/bw` referenced in
      [docs/SECRETS-BITWARDEN.md](docs/SECRETS-BITWARDEN.md)).
- [ ] Install other CLIs this repo uses: `wrangler`, `supabase`, `gh`, `node`/`npm`.
      On this machine they're all Homebrew-installed:
      ```bash
      brew install wrangler supabase gh node
      ```

## 2. Bitwarden access (org: ALPU.CA)

- [ ] Log into Bitwarden (desktop + CLI: `bw login`) with the account that has
      access to the ALPU.CA org — same email as on this machine.
- [ ] Set up the **auto-unlock script** so Claude Code sessions on the mini can
      unlock Bitwarden without manual password entry, matching this machine's
      setup described in [docs/SECRETS-BITWARDEN.md](docs/SECRETS-BITWARDEN.md):
      - Store the Bitwarden master password in macOS Keychain:
        ```bash
        security add-generic-password -a "<your-email>" -s "bitwarden-cli" -w "<MASTER_PASSWORD>" -U
        ```
      - Create `~/bin/bw-unlock` — a script that reads the password from
        Keychain via `security find-generic-password` and pipes it to
        `bw unlock --passwordenv` to return a session token. (I didn't copy
        the exact script contents here since reading it required a keychain
        access I don't have — grab it directly from `~/bin/bw-unlock` on this
        Mac and copy it over, e.g. via Tailscale `scp` or Taildrop.)
      - Verify: `export BW_SESSION=$(~/bin/bw-unlock)` then `bw list items`
        should work without a password prompt.
- [ ] Confirm you can see the org collections listed in
      [docs/SECRETS-BITWARDEN.md](docs/SECRETS-BITWARDEN.md) (DevOps-alpacapps,
      DevOps-shared, etc.) — `bw list items --search "Chase"` or similar as a
      smoke test.

## 3. Repo + gitignored local files

Clone the repo on the mini, then copy over the files that are intentionally
**not** in git (see `.gitignore`) — pull these from Bitwarden or copy directly
from this machine (Taildrop is fine since you're both on the same tailnet):

- [ ] `docs/CREDENTIALS.md` — API keys / credentials doc (loaded on-demand by
      Claude Code per `CLAUDE.md`)
- [ ] `.mcp.json` — MCP server config, if this repo defines one
- [ ] `CLAUDE.local.md` — any private local directives, if present
- [ ] `HOMEAUTOMATION.local.md` — if present/relevant
- [ ] `scripts/gmail-credentials.json` — Gmail OAuth creds, if used
- [ ] Check for a `.machine-name` file (gitignored) — this repo's convention
      for machine-specific identification; create one on the mini if the setup
      docs expect it.

None of these appear to exist as tracked files in this repo currently (they're
git-ignored by design), so check on this machine (`ls -la` for each path above)
to see which actually exist before copying.

## 4. Claude Code project config

- [ ] Copy `.claude/launch.json` (already tracked/untracked here — check
      `git status`) so the mini can run the same dev server config
      (`static-site` → `scripts/dev-server.js` on port 8787).
- [ ] Copy `.claude/agents/` (custom subagents, e.g. `deepseek-coder`) if not
      committed to git.
- [ ] If you use an `OPENROUTER_API_KEY` or similar env var for
      `scripts/ask-deepseek.js`, set it in the mini's shell profile — check
      this machine's `~/.zshrc`/`~/.zprofile` for the exact var name.

## 5. Deploy credentials

- [ ] `gh auth login` on the mini (same GitHub account) if you'll push/PR from
      there.
- [ ] `wrangler login` (Cloudflare Pages) if you'll deploy manually from the
      mini — though per `docs/DEPLOY.md`, CI deploys on push to `main`, so this
      may not be required for normal workflow.
- [ ] `supabase login` if you'll run migrations/queries directly from the mini.

## 6. Verify

- [ ] Open this repo in Claude Code on the mini, run a trivial read (`ls`,
      `git log`) to confirm it loads `CLAUDE.md` correctly.
- [ ] Run `export BW_SESSION=$(~/bin/bw-unlock) && bw list items | head` to
      confirm secrets access works end-to-end.
- [ ] Run `npm run css:build` or start the dev server
      (`node scripts/dev-server.js`) to confirm local tooling works.

---

**Not copyable by me:** actual secret values, the Keychain-stored master
password, and OAuth tokens — those need to move via Bitwarden itself, Taildrop,
or a password manager, never through this chat.
