# Handoff — CMS setup, in progress

Written because this Claude Code session ran low on context mid-task. Read this first if you're
picking up where it left off. Delete this file once the CMS rollout is fully done and the README's
"For content editors" section is updated to match reality (it's currently written as if the CMS
isn't wired up yet — it's much further along than that now).

## What's actually done (verified, live, working)

- Sveltia CMS admin built at `admin/config.yml` + `admin/index.html` — full schema covering every
  field in `data/race-config.json`, verified two ways (valid YAML that loaded cleanly in the CMS
  itself, and a recursive script cross-checking every real key/array-item against the schema —
  nothing gets dropped on save).
- `tools/render.py` got an `img_filename()` helper so sponsor/gallery image fields work whether
  they're a bare filename or a full path (what the CMS image widget saves) — confirmed
  byte-identical rebuild for existing data.
- **Cloudflare Worker deployed**: `https://sveltia-cms-auth.kirschner-devilliers.workers.dev`
  (source: `/tmp/sveltia-cms-auth`, cloned from `github.com/sveltia/sveltia-cms-auth`). All three
  secrets are set on it (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `ALLOWED_DOMAINS`) — confirmed
  via `npx wrangler secret list` from that directory. `wrangler` is authenticated locally as
  kirschner.devilliers@thedelta.io (Cloudflare account), no reinstall/login needed.
- **GitHub OAuth App** exists (named "Midvaal MadMac CMS", client ID `Ov23liYPEVccUr8719VB`) with
  callback URL pointed at the Worker above. This is the *second* OAuth App created during this
  session — the first attempt had a client ID that didn't match what got typed into the Worker
  secret (an old-format hex ID vs GitHub's current `Ov23...` format) and 404'd; that's what the
  troubleshooting in the chat transcript was about. If auth breaks again, re-check that the Client
  ID on `github.com/settings/developers` matches what `GITHUB_CLIENT_ID` is actually set to on the
  Worker — they're independent and nothing keeps them in sync automatically.
- `admin/config.yml` → `backend.base_url` points at the real Worker URL (not a placeholder).
- **GitHub Actions workflow** (`.github/workflows/build-deploy.yml`) exists, builds, and deploys
  successfully — verified via `gh run watch` on a real `workflow_dispatch` run (full success, both
  the live site and `/admin/` confirmed responding correctly afterward). It runs `render.py` (and
  `build-routes.py` if GPX changed) on every push touching the content/asset paths, and fails
  closed — a broken `render.py` run stops before `deploy-pages`, so bad content can't take the
  site down.
- **GitHub Pages build source switched** from "Deploy from branch" to "GitHub Actions"
  (`build_type: workflow`, confirmed via `gh api repos/.../pages`). The Action now owns publishing.
  `index.html` is still committed to the repo (harmless — just no longer the thing actually being
  served; the Action regenerates it fresh from `race-config.json` at deploy time regardless).
- The user successfully logged into `/admin/` via "Sign In with GitHub" — the OAuth round-trip
  works end to end.
- `gh` CLI auth was refreshed with the `workflow` scope (needed to push changes to
  `.github/workflows/*` — the default scope doesn't allow it and the first push attempt was
  rejected until this was added).

## What's NOT done yet — this is the next step

**No one has actually made a content edit through the CMS and confirmed it commits.** The user was
about to do this (open `/admin/`, tweak one FAQ answer, hit save) when the session ran low on
context. That's the last unverified link in the chain. To confirm it worked:

```bash
cd "/Users/kirschnerdevilliers/Claude Code/madmac-2026"
git log --oneline -5 -- data/race-config.json
```

If a new commit shows up there that wasn't made by a `git push` from this machine, the save worked.
Then check the GitHub Actions tab (or `gh run list --workflow=build-deploy.yml --limit 1`) to
confirm it triggered and succeeded, and that the live site actually reflects the change:
`https://kirschnerdevilliers.github.io/Meyerton-MadMac-Marathon/`

## After that's confirmed, remaining rollout steps (from the original plan)

1. Onboard any other real editors as repo Collaborators with Write access (Settings → Collaborators
   on the GitHub repo) — right now only the account that did this setup can log into `/admin/`.
2. Update `README.md` → "For content editors" section — it currently says the OAuth/Worker/Action
   pieces aren't done yet. They are. Rewrite that section to just say "go to `/admin/`, log in, edit,
   save" and drop the numbered list of remaining infra steps.
3. Consider whether this `HANDOFF.md` file should be deleted once the above is confirmed and
   written up properly — it's a temporary artifact, not meant to be permanent project documentation.

## Where things live (for a fresh session with no memory of this)

- Repo: `kirschnerdeVilliers/Meyerton-MadMac-Marathon` (public), local clone at
  `/Users/kirschnerdevilliers/Claude Code/madmac-2026`
- Live site: `https://kirschnerdevilliers.github.io/Meyerton-MadMac-Marathon/`
- CMS admin: `https://kirschnerdevilliers.github.io/Meyerton-MadMac-Marathon/admin/`
- Auth worker source (not in this repo): `/tmp/sveltia-cms-auth` — this is in `/tmp`, so it may not
  survive a reboot; if it's gone, just re-clone `github.com/sveltia/sveltia-cms-auth` and
  `npx wrangler deploy` again (the deployed Worker itself is unaffected either way, this is just the
  local source used to deploy/manage it).
- The original planning document for this whole CMS addition is at
  `/Users/kirschnerdevilliers/.claude/plans/landing-page-brief-curious-flurry.md`, under the
  "Addendum: Git-based CMS for content editors" heading — the plan that was approved before any of
  this work started.
