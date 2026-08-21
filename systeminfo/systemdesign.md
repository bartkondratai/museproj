# System Design — BeArt&Music

> Text companion to the [`/systeminfo`](./index.html) page. Keep both in sync — see the
> update rule in `CLAUDE.md`.
>
> This lists only services with a real account and real credentials (verified against the
> Bitwarden vault). The repo also contains edge functions and code paths for Stripe,
> Square, PayPal, Telnyx, SignWell, Vapi, and various smart-home vendors (Tesla, Nest, LG
> ThinQ, Govee, Sonos, Anova, Glowforge) — those are leftover scaffolding from the
> `alpacapps-infra` template this project was cloned from, with no account behind them.
> They're intentionally excluded below; add them back only once real credentials exist.

## How it fits together

**GitHub** holds the source and runs the deploy on every push to `main`. The browser
calls `beartandmusic.pl` for the public site; internal-only paths redirect to
`in.beartandmusic.pl`, which Cloudflare Access gates behind Google sign-in, restricted to
a single allowed account. Everything server-side goes through **Supabase**: it's the
database, the auth provider, the file store, and the host for the edge functions. Those
functions call out to **Resend** for email and **OpenRouter** for AI-assisted features.

Two AI coding agents maintain this repo: **Claude Code** (reads `CLAUDE.md`) does most of
the direct work, and **Codex** (reads `AGENTS.md`) delegates well-scoped code generation
to **DeepSeek v4 Flash** via OpenRouter. DeepSeek is not a separate service — it's a model
accessed through the OpenRouter gateway already listed below.

```
GitHub (repo + Actions CI) ──deploys──► Cloudflare Pages

Browser
   │
   ▼
Cloudflare Pages + Access  (public: beartandmusic.pl · internal: in.beartandmusic.pl)
   │                        Access login: Google OAuth, bart.kondrat@gmail.com only
   ▼
Supabase (Postgres DB · Auth · Storage · Edge Functions)
   │
   ├──► Resend (email)
   └──► OpenRouter (DeepSeek v4 Flash & other models)

Dev tooling (not runtime services): Claude Code, Codex → OpenRouter/DeepSeek
```

## Hosting & Identity

| Service | Cost | What it does |
|---|---|---|
| Cloudflare Pages | Free | Hosts this static site. Deploys automatically via GitHub Actions on every push to `main`. |
| Cloudflare DNS | Free | DNS and SSL for `beartandmusic.pl` and `in.beartandmusic.pl`. |
| Cloudflare Access | Free | Gates `in.beartandmusic.pl` at the edge, before any page code runs. |
| Google OAuth | Free | Identity provider for Cloudflare Access — sign-in restricted to `bart.kondrat@gmail.com`. |

## Source Control & CI

| Service | Cost | What it does |
|---|---|---|
| GitHub | Free | Hosts the repo. GitHub Actions builds Tailwind, bumps the version, and deploys to Cloudflare Pages on every push to `main`. |

## Backend

| Service | Cost | What it does |
|---|---|---|
| Supabase | Free tier | Postgres database, authentication, file storage, and the edge functions this app calls. |

## Communications & AI

| Service | Cost | What it does |
|---|---|---|
| Resend | Free tier | Sends and receives system email. |
| OpenRouter | Pay-as-you-go | Multi-model LLM gateway. Currently routes to DeepSeek v4 Flash for AI-assisted edge functions and code-generation delegation. |

## AI Coding Agents (dev tooling, not runtime services)

| Agent | Instructions file | What it does |
|---|---|---|
| Claude Code | `CLAUDE.md` | Primary agent for building and maintaining this repo — runs migrations, pushes deploys directly. |
| Codex | `AGENTS.md` | Secondary coding agent — delegates well-scoped code generation to DeepSeek v4 Flash via OpenRouter (`scripts/ask-deepseek.js`). |

## Domain routing

| Domain | Purpose |
|---|---|
| `beartandmusic.pl` | Public-facing pages |
| `in.beartandmusic.pl` | Internal pages — Cloudflare Access-gated (Google OAuth, single allowed account) |

Routing is enforced by `functions/_middleware.js`. See `docs/DEPLOY.md` for Cloudflare
setup details.

---
*Source of truth for "what's actually active": the Bitwarden vault. If a service has no
credential item there, it's not part of this deployment yet, even if code for it exists
in the repo.*
