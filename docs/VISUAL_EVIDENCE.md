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

Run [43491076054](https://github.com/helalalfqih-sketch/Nasqo/actions/runs/43491076054)
completed successfully on branch commit `d267dda` (tested merge checkout
`7e1d0f66be1a29c2e152c553856c2070fb7db9c0`). All eleven M2 groups and four
HTTP/DOM/PNG capture checks passed. M1, static and security workflows also passed.
Artifact `14069214428` contains the four actual PNGs and their provenance; the
downloaded ZIP and each PNG hash were verified. Browser: Chrome 157.0.8103.50.

Manual visual review: Alpha/Beta shop and the mobile-width shop render their own
synthetic product, USD default price and standard Odoo layout. **Login visual
acceptance FAIL:** the login capture contains the site header/footer but no
visible form. The DOM-presence check found blank inputs; that does not prove
visibility or completed JavaScript initialization. The pinned Odoo login template
initially hides the form until its UserSwitch component starts. Browser console,
asset loading and readiness need a targeted investigation before accepting login
UI behavior. No CSS/DOM was altered to manufacture a successful screenshot.

These images must be described as foundation evidence, not a finished storefront.
The login issue is an additional open visual gate. The next test change should
assert computed visibility and browser readiness, with diagnostic capture on
failure; it must not equate DOM presence with a usable login page.

Reproduce on the disposable GitHub runner after `bash scripts/m2/run.sh`:

```bash
python3 -B -m tests.isolation.screenshots
```

Chrome's capture flags are documented in the official
[Headless command-line reference](https://developer.chrome.com/docs/automation-and-testing/headless-cli).
No new Python/browser automation package is required. The runner browser version
is recorded, not version-pinned; image appearance may vary between runner images.
