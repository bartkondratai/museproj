# Deployment Workflow

## Cloudflare Pages (Static Site)

Deploys from `main` branch via GitHub Actions → Cloudflare Pages. Push to main and it's live.

### Push Workflow
```bash
git add -A && git commit -m "message"
./scripts/push-main.sh   # pull --rebase, then push
```

### Post-Push Verification
1. Wait ~60s for CI to run (Tailwind build + Cloudflare Pages deploy)
2. `git pull --rebase origin main`
3. Read `version.json` — report version

### Version Format
`vYYMMDD.NN H:MMa` — date + daily counter + Austin time.
CI bumps automatically via GitHub Action on every push. **Never bump locally.**

### Post-Push Output Format
- **Main branch:** "Deployed to main — ..." with test URLs
- **Feature branch:** "Pushed to branch `name` (not yet deployed)" with changed files list

### Cloudflare Pages Setup

1. Create a Cloudflare Pages project connected to your GitHub repo
2. Build command: `npm run css:build`
3. Build output directory: `.` (root — the entire repo is the site)
4. Add GitHub secrets:
   - `CLOUDFLARE_API_TOKEN` — API token with Pages edit permissions
   - `CLOUDFLARE_ACCOUNT_ID` — Your Cloudflare account ID
5. Set GitHub variable `CLOUDFLARE_PAGES_PROJECT` to your project name

### Preview Deployments
Every pull request automatically gets a preview deployment URL:
`https://<branch>.<project>.pages.dev`

## Live URLs

One Cloudflare Pages project serves both domains. `functions/_middleware.js` routes by
hostname: internal paths (`/residents`, `/associates`, `/spaces/admin`, `/clauded`,
`/directory`, `/login`, `/systeminfo`, `/intranet`) redirect to the intranet subdomain;
everything else redirects to the public domain.

| Environment | URL |
|---|---|
| Public site | https://beartandmusic.pl/ |
| Intranet (staff/residents, Cloudflare Access-gated) | https://in.beartandmusic.pl/ |
| Cloudflare Pages preview | https://YOUR_PROJECT.pages.dev/ |
| Resident portal | https://in.beartandmusic.pl/residents/ |
| Associates | https://in.beartandmusic.pl/associates/ |
| Admin | https://in.beartandmusic.pl/spaces/admin/manage.html |
| System info | https://in.beartandmusic.pl/systeminfo/ |
| Public spaces | https://beartandmusic.pl/spaces/ |
| Payments | https://beartandmusic.pl/pay/ |
| Repository | https://github.com/USERNAME/REPO |

### One-time manual step (Cloudflare dashboard)

Attach `in.beartandmusic.pl` as a **custom domain on this same Pages project** (Pages →
project → Custom domains). If `in.beartandmusic.pl` is currently attached to a different
Pages project (e.g. a placeholder `beartandmusic-intranet` project), remove it there first
— a custom domain can only point at one project at a time. Then configure a Cloudflare
Access application scoped to `in.beartandmusic.pl/*` restricting it to authorized accounts;
the middleware only handles routing, not authentication.

## Tailwind CSS

After adding new Tailwind classes, run: `npm run css:build`
