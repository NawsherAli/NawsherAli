# Setup: publishing the profile (about 10 minutes)

Everything is built and tested locally. Publishing needs your GitHub account, so these steps are yours to run.

## 1. Before publishing (security and reputation)
- [ ] **shredbottle:** Settings → Change visibility → Private. If it is deployed anywhere, run `php artisan passport:keys --force` there (the old private key is in `backup.zip`).
- [ ] **investo:** make it private.
- [ ] **dezesitemagniemandzien:** already private. Confirm the production database password was changed.

## 2. Create the profile repository
1. github.com/new → name it exactly **`NawsherAli`** → Public → don't add a README → Create.
2. On your computer:
```bash
cd NawsherAli          # the folder from this delivery (already a git repo with history)
git remote add origin https://github.com/NawsherAli/NawsherAli.git
git push -u origin main
```
3. Repo → Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save.
4. Actions tab → **update-profile** → **Run workflow**. About 30 seconds later the TELEMETRY card shows your real numbers.

## 3. Profile settings (github.com/settings/profile)
- Bio: `Senior Backend & API Architect · Laravel · FastAPI · Multi-tenant SaaS · AI integration`
- Company: `Mediatiz Foundation` (fixes "Fundation")
- Location: `Islamabad, Pakistan`
- Social link: `https://www.linkedin.com/in/nawsher-ali-saas-architect/` (replaces the old /nawsher-ali-5146ab183)
- Optional: tick **Include private contributions on my profile** if your work repos are on GitHub. This shows counts only, never code.

## 4. Items needing your review
| Item | Where | Why |
|---|---|---|
| Career facts: ~5 yrs, 700K+, 3 tenant levels, 685 tests | `[[career_facts]]` | Taken from your CV. Remove any you'd rather not publish |
| Mediatiz LMS card facts (RBAC 7 tiers, 4-stage payments, AI & n8n) | `[[work]]` | Public CV facts. Confirm your employer is comfortable with them being on GitHub |
| Migrova "~20% faster page loads" | `[[work]]` | You chose to keep the approximate metric on the CV. Same rule here |
| Build queue repos (laravel-tenancy-kit, fastapi-rag-gateway) | `[[lab]]` | Shown as PLANNED. Delete the entries if you won't build them soon |
| "Microservices" in the title and stack | `[identity]`, `[[stack]]` | Matches your CV title. Be ready to discuss an example |
| Website link | `links.website` | Left empty on purpose: iotaiy.com is an agency site that doesn't present you |

## 5. Preview
`docs/preview/` has desktop dark, desktop light and mobile renders made from this exact README.
