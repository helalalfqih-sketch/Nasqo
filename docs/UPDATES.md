# Safe change and release policy

## Branches
- `main`: reviewed stable project configuration, not an automatic deployment target.
- `chore/odoo19-ecommerce-foundation`: initial foundation for review.
- `feature/<topic>`: custom work; `update/odoo19-<date>`: upstream pin changes.
- Merge through a reviewed pull request. Never force-push shared branches.
- Recommended GitHub rules: require review and the `Static foundation checks` status, block force pushes and deletion. These are recommendations; branch protection has NOT been enabled by this scaffold.

## Modules
Keep custom code in `addons/nasqo_*`; extend models/views instead of editing core. Split storefront/theme, delivery, accounting and messaging into separate modules when needed, with explicit dependencies and licenses. Do not add Enterprise modules to this Community project. Third-party code belongs in a separately pinned dependency, not pasted into core.

## Upstream update gate
1. Create an update branch, record current upstream SHA and proposed 19.0 SHA. Review the upstream diff, dependency/security changes and compatibility. Never track `master` or floating `latest`.
2. Change `upstream.json` in the update branch. Preserve previous checkout; fetch a fresh pinned checkout using the script in a separate worktree.
3. Run static checks. In an isolated DB test initial install and module upgrade, checkout/cart, anonymous/customer/staff permissions, product variants, inventory, taxes, delivery, Arabic/RTL and invoice output. Use sandbox payment/email credentials only.
4. Record exact test commands, versions, pass/fail/skipped counts and artifacts. Static checks alone are NOT readiness evidence.
5. Obtain review, merge only approved commits and tag releases. Deployment requires separate explicit approval; no automatic deploy exists here.

## Release and rollback
Back up database AND filestore as one consistent recovery point and verify restore in isolation before production changes. Preserve previous application/image/config versions. Module upgrades may alter schemas/data: rolling code back alone is not a safe rollback. Restore the matching database/filestore backup where required, with a plan for transactions after the backup. Never test destructive rollback on production.

## Secrets
No live data, credentials, session files, private keys, customer exports or server-specific configuration in this public repository. Use ignored local config and an approved secret manager. Gitignore is not a secret scanner: review every staged diff and run an approved secret scan before publishing. If a secret is exposed, revoke/rotate it; deleting the file alone is insufficient.

## Remaining validation
Source is pinned but not vendored. The original static foundation checks do not
establish runtime readiness. Separate live integration on foundation commit
`ca09ad2` passed install/upgrade and login/shop checks; M2 adds its own independent
tenant/restore suite. See `AI_HANDOFF.md` for observed results. Checkout, financial
policies, production security and deployment still require their own gates.
No production release is authorized by passing CI.
