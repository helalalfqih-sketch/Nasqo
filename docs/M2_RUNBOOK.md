# M2 — isolated operator pilot

Requires Linux, Python 3, Git, Docker Engine/Compose v2 and GnuPG. Use a disposable
Codespace or CI runner with synthetic data only. The CLI rejects remote Docker
contexts and checks both the source SHA and an unmodified upstream checkout.
The full automated suite uses a unique state directory on every run and does not
delete old volumes. Allow at least 4 cores / 7 GiB for the sequential pilot.
New projects build the small reviewed PostgreSQL image from `docker/postgres/`;
the build context contains no repository state or credentials. Existing generated
Compose files are not rewritten. Do not convert prior Debian volumes to Alpine.

## Full acceptance suite

```bash
python3 -B -m unittest discover -s tests -v
bash scripts/m2/run.sh
```

The runner exercises worker failure/retry, two actual installs/upgrades, positive
and negative HTTP/ORM checks, private files, DB permissions, GPG encryption and
isolated restore. The sanitized report is `artifacts/m2-results.json`. The GitHub
workflow publishes it in the job log/summary; credentials and backups are not
uploaded. Failure stops the suite; subsequent checks are unexecuted, not PASS.

## Manual provisioning

Fetch source once if absent: `bash scripts/fetch_upstream.sh`. Make only the public
source readable by the non-root container: `chmod a+rx vendor` and
`chmod -R a+rX vendor/odoo`. Never relax permissions on `.m2` state or key files.

```bash
python3 -B -m provisioning.cli provision alpha --key manual-alpha-request-001
python3 -B -m provisioning.cli provision beta --key manual-beta-request-0001
python3 -B -m provisioning.cli status
python3 -B -m provisioning.cli gateway
curl --fail -H 'Host: alpha.nasqo.test' http://127.0.0.1:18069/shop
curl --fail -H 'Host: beta.nasqo.test' http://127.0.0.1:18069/shop
```

Default state `.m2/` is ignored. Private registry/state directories must be owned
by the operator and mode 0700. Credentials use 0600. The per-tenant `odoo.conf`
is 0444 inside its private 0700 directory so the non-root Odoo container can read
its own config. Docker operators remain trusted and can inspect all containers.
Login is `operator`; each store's generated password is in its own ignored
`credentials.json`. Never paste credentials into tickets, chat, CI or Git.

The gateway is loopback-only. In Codespaces keep any forwarded port **Private**.
Directly browsing a generic forwarded hostname is intentionally rejected; use
the terminal Host-header checks above. Public DNS/TLS and browser UX are backlog.

Same key + same slug returns the same operation/resources. Reusing a key with a
different slug, or a slug with a different key, fails. A crash before activation
records `failed_needs_review`, stops Odoo, and leaves resources for inspection.
After inspecting the cause, retry the original command/key; completed installation
is detected from the database. A live `active` tenant is never reinitialized by
provision. The operator lock serializes provisioning, backup, restore and routing.
One named operator container per tenant prevents a second writer after a worker
crash. Timeouts attempt to stop it; a surviving name blocks another job until the
operator investigates. Readiness failures include only a credential-redacted tail.

## Offline backup and safe restore

```bash
python3 -B -m provisioning.cli backup alpha --key-file .m2/recovery.key
python3 -B -m provisioning.cli restore alpha --archive .m2/backups/ARCHIVE.gpg --key-file .m2/recovery.key
```

Replace `ARCHIVE.gpg` with the exact path printed by backup. First backup generates
a random 256-bit recovery key. Keep the key separately from the encrypted archive
when exporting; this pilot does not upload anything off-host. Loss of the key
means loss of recovery. GnuPG AES-256 with integrity checking protects the complete
archive; hashes additionally check the paired DB/filestore contents.

Backup intentionally stops the tenant's Odoo writer while taking the dump and
filestore snapshot, then verifies restart in `finally`. Expect a short outage.
No concurrent writers other than this operator are supported. Recovery validates
encryption/integrity, exact members, identity, source version, size and safe tar
paths **before** creating any resources. Cross-tenant restore is refused.

Restore creates fresh named volumes/networks without any host port or gateway
route. Cron and mail servers are disabled and outbound networks are internal;
the restored admin password is rotated. Failed restore resources are quarantined
and retained for diagnosis, never silently deleted. This is a 512 MiB synthetic
pilot using in-memory buffers, not a streaming production backup service.

## Recovery and limitations

No `down -v`, reset, prune, DROP DATABASE or destructive cleanup is provided.
Use `docker compose -p PROJECT -f COMPOSE_FILE ps` to inspect only the recorded
project, or `stop` to pause it without deleting volumes. Existing foundation
Codespaces v2 commands use their separate `nasqo-odoo19-development-v2` project
and new volumes; bootstrap refuses an old v1 workspace rather than migrating it.

The local ChatGPT executor used for initial implementation lacks Docker, psql
and sudo. Its sandbox also blocks Unix sockets required by `gpg-agent`.
The same commands therefore require a normal Docker-enabled Codespace or the
GitHub runner; absence of local execution is not runtime PASS evidence.
