# Actual M2 UI evidence

Requested follow-up: show the implemented result using real screenshots while
the available NASQO Codespaces are offline. No public preview is deployed.

`tests/isolation/screenshots.py` runs only when `GITHUB_ACTIONS=true` and the
current runner's M2 report is PASS. The existing workflow first provisions its
two synthetic tenants and tests isolation/restore. The capture step then uses
the runner's Chrome/Chromium with fresh anonymous profiles and loopback-only
tenant name resolution. It does not change fixtures, views or runtime routing.

The step checks HTTP 200, the rendered shop grid and own/foreign fixture markers,
or empty login/password inputs. It checks PNG dimensions and records the checkout
SHA, pinned Odoo SHA, browser version, timestamp and file hashes. It never emits
raw browser output, DOM, cookies or profiles. The artifact allowlist contains
only four PNGs and `provenance.json`, retained for seven days.

| File | Actual page |
|---|---|
| store-a-desktop.png | Alpha /shop, 1440 x 1000 |
| store-b-desktop.png | Beta /shop, 1440 x 1000 |
| store-a-login.png | Alpha /web/login, blank anonymous form |
| store-a-mobile-width.png | Alpha /shop, 420 x 900 desktop-browser viewport |

The mobile-width capture is not device/touch emulation or a complete responsive
acceptance test. These captures show the standard Odoo UI, default sample contact
details and synthetic M2 product identifiers. Arabic/RTL, YER configuration,
merchant signup and full checkout remain M3+ work. Screenshots do not add proof
of those capabilities or substitute for the M2 integration assertions.

## Verification status

Capture code and workflow have been prepared. Actual capture execution and
visual inspection are pending; update this section only after observing them.

Reproduce on the disposable GitHub runner after `bash scripts/m2/run.sh`:

```bash
python3 -B -m tests.isolation.screenshots
```

Chrome's capture flags are documented in the official
[Headless command-line reference](https://developer.chrome.com/docs/automation-and-testing/headless-cli).
No new Python/browser automation package is required. The runner browser version
is recorded, not version-pinned; image appearance may vary between runner images.
