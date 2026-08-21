# System Design — BeArt&Music

> Text companion to the [`/systeminfo`](./index.html) page. Keep both in sync — see the
> update rule in `CLAUDE.md`.

## How it fits together

The browser and mobile app both call `beartandmusic.pl`. Cloudflare Pages serves the
static site and routes internal-only pages (residents, associates, admin, directory,
login, system info) to the Cloudflare Access-gated `in.beartandmusic.pl` subdomain via
`functions/_middleware.js`. Nearly everything else goes through **Supabase**: it's the
single database, the auth provider, the file store, and the host for ~60 edge functions
that talk to every external vendor below. A few things — cameras, Sonos, the 3D printer,
and two-way camera talkback — go through the **Home Server** instead, since those
devices only exist on the local network and Supabase edge functions can't reach them
directly; the Home Server bridges out over Tailscale.

```
Browser / Mobile App
        │
        ▼
Cloudflare Pages + Access  (public: beartandmusic.pl · internal: in.beartandmusic.pl)
        │
        ▼
Supabase (Postgres DB · Auth · Storage · ~60 edge functions · centralized REST API)
        │
        ├──► Cloudflare R2 (object storage)
        ├──► Payments: Stripe / Square / PayPal
        ├──► Comms: Resend / Telnyx
        ├──► AI: Gemini / Vapi / Brave Search
        ├──► Docs: SignWell
        ├──► Smart home cloud APIs: Nest / Tesla / LG ThinQ / Govee
        │
        ▼
Home Server (Tailscale bridge to the LAN)
        │
        ▼
Physical devices: Sonos, UniFi cameras, FlashForge printer, Anova oven, Glowforge

Standalone: Hostinger VPS (OpenClaw chatbot — Discord/WhatsApp/Telegram)
Standalone, deprecated: DigitalOcean droplet (legacy pollers, migrating to Hostinger + Oracle)
```

## Hosting & Data

| Service | Cost | What it does |
|---|---|---|
| Cloudflare Pages | Free | Hosts this static site. Deploys automatically on every push to `main`. No server-side code — every page is plain HTML/JS calling Supabase directly. |
| Cloudflare Access | Free | Gates `in.beartandmusic.pl` to authorized accounts only, at the edge — before any page code runs. |
| Supabase | Free tier | Postgres database, authentication, file storage, and ~60 Deno edge functions. The backend for essentially everything in the app. |
| Cloudflare R2 | Free tier | S3-compatible object storage for documents (manuals, guides) that PAI can look up. 10 GB free, zero egress fees. |

## Payments

| Service | Cost | What it does |
|---|---|---|
| Stripe | Pay-as-you-go | ACH & card payments from tenants, plus Stripe Connect payouts to associates. 0.8% capped at $5 per ACH transaction. |
| Square | Pay-as-you-go | Alternate payment processor for tenant payments. 2.6% + $0.10 per transaction. |
| PayPal | Pay-as-you-go | Associate payouts via the Payouts API. $0.25 per payout. |

## Communications & AI

| Service | Cost | What it does |
|---|---|---|
| Resend | Free tier | Sends and receives all system email (45+ branded templates). Inbound routing forwards or auto-processes based on address prefix. |
| Telnyx | Pay-as-you-go | SMS in and out — tenant notifications, bulk announcements, and inbound conversations. |
| Google Gemini | Pay-as-you-go | Powers PAI (the property AI): chat, smart-home commands, identity verification from ID photos, payment matching, and AI-generated images. |
| Vapi | Pay-as-you-go | Voice AI platform — lets PAI take and make phone calls. ~$0.10–$0.30 per call. |
| Brave Search | Free tier | Real-time web search tool for PAI — current events, local info, prices. 2,000 free queries/month. |
| SignWell | Free tier | E-signatures for lease and event agreements. 25 documents/month free. |

## Smart Home & Devices

| Service | Cost | What it does |
|---|---|---|
| Google Nest | Free | 3 thermostats via the Smart Device Management API, controlled directly from a Supabase edge function. |
| Tesla Fleet API | Free | 6 vehicles polled every 5 minutes; lock/unlock/flash commands from the resident app. |
| LG ThinQ | Free | Washer/dryer status polled every 30s, with push notifications when a cycle ends. |
| Govee | Free | Cloud API for lighting groups and scenes, proxied through an edge function. |
| Sonos / Music Assistant | Free | 12 zones. Music Assistant on the Home Server is the primary control plane; Sonos's own HTTP API is a fallback for announcements. |
| UniFi Cameras | Free | 3 PTZ cameras streamed via go2rtc on the Home Server, plus two-way talkback audio over FFmpeg. |
| Anova Oven | Free | Precision oven controlled over a WebSocket API, per-request (no polling worker needed). |
| Glowforge | Free | Laser cutter status via an undocumented, reverse-engineered cloud API. Read-only. |
| FlashForge Printer | Free | 3D printer controlled over raw TCP G-code, bridged to the web through the Home Server proxy. |

## Servers & Infrastructure

| Service | Cost | What it does |
|---|---|---|
| Home Server | Local | Runs on the local network; the only thing that can reach LAN-only devices (cameras, printer, Sonos). Reachable remotely over Tailscale. |
| Hostinger VPS | Hosted | Runs OpenClaw, a multi-channel chatbot gateway (Discord, WhatsApp, Telegram, Slack) fronted by Caddy with auto-HTTPS. |
| DigitalOcean Droplet | Deprecated | Legacy background workers (bug scout, pollers). Being migrated to Hostinger + Oracle. |

## Domain routing

| Domain | Purpose |
|---|---|
| `beartandmusic.pl` | Public-facing pages |
| `in.beartandmusic.pl` | Internal pages (residents, associates, admin, directory, login, system info) — Cloudflare Access-gated |

Routing is enforced by `functions/_middleware.js`, which redirects internal paths to the
`in.` subdomain and public paths to the root domain regardless of which one a request
arrives on. See `docs/DEPLOY.md` for the one-time Cloudflare dashboard setup this
requires.

---
*For full API keys, table schemas, and deploy commands, see `docs/INTEGRATIONS.md` and
`docs/KEY-FILES.md` — this doc is the plain-English overview.*
