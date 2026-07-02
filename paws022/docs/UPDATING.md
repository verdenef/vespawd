# When POS (paws022) updates

POS version is tracked as **`instructionsVersion`** (e.g. `1.1.7`) in the template repo and in your `%USERPROFILE%\.pos\config.json`.

## How you know there is an update

| Signal | What it means |
|--------|----------------|
| Friend / course announcement | Maintainer bumped the template on GitHub |
| `git pull` in your **template clone** shows new commits | Template files changed |
| **`pos-check-update.ps1`** reports a mismatch | Your saved config version ≠ template version |
| `instructionsVersion` in [pos.config.json.example](../pos.config.json.example) is higher than yours | Same |

There is no automatic push notification yet — run the check script or `pos-update` occasionally.

```powershell
cd C:\path\to\your\paws022-clone
.\scripts\pos-check-update.ps1    # check only
.\scripts\pos-update.ps1         # pull + refresh config (alias: pos-upd after install-pos-command)
```

### One-command update (`pos-update.ps1`)

| Flag | Effect |
|------|--------|
| _(none)_ | `git pull` in template clone, bump `instructionsVersion` in `~/.pos/config.json` |
| `-SyncProjects` | Also run `pos-sync.ps1` on each POS app under `projectsDir` (integrated or sidecar `paws022/`) |
| `-SkipPull` | Skip `git pull` (config + sync only) |
| `-DryRun` | Show what would run |
| `-TemplatePath` | Override template folder |

**Still manual:** re-copy planner/documenter prompts into Gemini/ChatGPT/etc.

## What to do (by situation)

### A. You only use the template clone (building POS)

```powershell
cd C:\path\to\paws022
git pull
```

Done for the template repo itself.

---

### B. Machine setup (`~/.pos/config.json`) — once per PC

After pulling the template:

```powershell
cd C:\path\to\paws022
.\scripts\pos-check-update.ps1
```

If outdated:

1. Re-run **`Setup-POS.bat`** (choose **Already installed** in the prompts), or:
2. `.\scripts\pos-setup.ps1` → choose **Already installed** → update toolchain/paths if needed
3. Confirm `instructionsVersion` in `%USERPROFILE%\.pos\config.json` matches the template

---

### C. External planner & documenter (Gemini, ChatGPT, etc.)

When **`instructionsVersion`** bumps, re-copy prompt text (assignments depend on this):

| File | Action |
|------|--------|
| [.ai/planner_prompt.md](../.ai/planner_prompt.md) | Paste into planner tool |
| [.ai/documenter_prompt.md](../.ai/documenter_prompt.md) | Paste into documenter tool |

See [EXTERNAL_AGENTS_SETUP.md](EXTERNAL_AGENTS_SETUP.md). Your Gems do **not** auto-update.

---

### D. An app project you already created

Pulling the template does **not** change old app folders. Per app:

```powershell
cd C:\path\to\paws022
.\scripts\pos-sync.ps1 -TargetPath "C:\path\to\your-app"
```

| Updates | Does not touch |
|---------|----------------|
| `executor_rules.md`, `pos.mdc`, `AGENTS.md` | `src/`, `project_context.md` |
| Adds missing `HANDOFF`, `PROJECT_LAYOUT`, etc. if absent | Your task files content |

After a **large** POS release, consider re-running [ADOPT_BOOTSTRAP_PROMPT.md](ADOPT_BOOTSTRAP_PROMPT.md) in the executor IDE if docs/memory should be refreshed (optional).

---

## Quick checklist

- [ ] `.\scripts\pos-update.ps1` (add `-SyncProjects` for app repos)
- [ ] Re-copy planner + documenter prompts if version bumped
- [ ] Skim [START.md](../START.md) / [decisions.md](decisions.md) for breaking workflow changes

## Maintainers

See [PUBLISH.md](../PUBLISH.md) — bump `instructionsVersion` in `pos.config.json.example` and `setup/wizard-data.json`, then tell users to pull and run the checklist above.
