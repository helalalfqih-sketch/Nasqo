"""Create a fresh, private Docker RBAC lab. Never copy a business database.

The operator provides reviewed image IDs, public addon directories and a module
inventory. Existing workspaces are refused; no cleanup/removal is implemented.
Run on a disposable Docker host or the explicitly authorized development host.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--project', required=True)
    parser.add_argument('--odoo-image', required=True)
    parser.add_argument('--postgres-image', required=True)
    parser.add_argument('--inventory', required=True, type=Path)
    parser.add_argument('--addons', required=True, action='append', type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'nasqo-rbac-[a-z0-9-]+', args.project):
        raise SystemExit('Use a unique nasqo-rbac-* project name')
    for image in [args.odoo_image, args.postgres_image]:
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
            raise SystemExit('Use a locally inspected immutable image ID')
    root = args.workspace.resolve()
    if root.exists():
        raise SystemExit('Refusing an existing workspace; preserve it and choose a fresh path')
    inventory = json.loads(args.inventory.read_text())
    modules = inventory['modules']
    if not all(re.fullmatch(r'[a-z0-9_]+', m) for m in modules):
        raise SystemExit('Invalid module name in inventory')
    if not {'website_sale', 'sale_management', 'nasqo_store'}.issubset(modules):
        raise SystemExit('Expected NASQO runtime modules are missing')
    if shutil.disk_usage(root.parent).free < 3 * 1024**3:
        raise SystemExit('Insufficient free disk for an isolated lab')
    root.mkdir(mode=0o700)
    (root / 'addons').mkdir()
    (root / 'config').mkdir()
    (root / 'db-init').mkdir()
    (root / 'private').mkdir(mode=0o700)
    # Copy only the expected public source, preserving bytes and rejecting links.
    for name, expected in inventory['nasqo_source_hashes'].items():
        matches = [p / name for p in args.addons if (p / name / '__manifest__.py').is_file()]
        if len(matches) != 1:
            raise SystemExit('Ambiguous/missing addon source: ' + name)
        source = matches[0]
        target = root / 'addons' / name
        for relative, digest in expected.items():
            relative_path = Path(relative)
            if relative_path.is_absolute() or '..' in relative_path.parts:
                raise SystemExit('Unsafe relative source path')
            original = source / relative_path
            if original.is_symlink() or not original.is_file():
                raise SystemExit('Unsafe source file: ' + name)
            data = original.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise SystemExit('Source changed since inspection: ' + name)
            dest = target / relative_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    for name in ['nasqo_rbac_install_probe', 'nasqo_rbac_state_probe']:
        addon = root / 'addons' / name
        addon.mkdir()
        (addon / '__init__.py').write_text('')
        (addon / '__manifest__.py').write_text(repr({
            'name': name, 'version': '19.0.1.0.0', 'depends': ['base'],
            'license': 'LGPL-3', 'installable': True, 'application': False,
            'data': [],
        }))
    # A restrictive host umask must not prevent non-root container reads.
    # The enclosing workspace stays 0700; only public source is normalized.
    for directory in [root / 'addons', *(p for p in (root / 'addons').rglob('*') if p.is_dir())]:
        directory.chmod(0o755)
    for source_file in (root / 'addons').rglob('*'):
        if source_file.is_file():
            source_file.chmod(0o644)
    credentials = {name: secrets.token_urlsafe(32) for name in [
        'postgres', 'database', 'master', 'developer', 'merchant',
        'merchant_union', 'staff', 'portal', 'support_candidate', 'delegated_users',
    ]}
    private = root / 'private' / 'credentials.json'
    private.write_text(json.dumps(credentials))
    private.chmod(0o600)
    # Only the containing private workspace is traversable by its owner.
    # Read-only bind files must also be readable by the non-root container UIDs.
    for name in ['postgres', 'database']:
        p = root / 'config' / (name + '.password')
        p.write_text(credentials[name])
        p.chmod(0o644)
    database = 'nasqo_rbac_test'
    config = '\n'.join([
        '[options]', 'db_host = db', 'db_port = 5432',
        'db_user = ' + database, 'db_password = ' + credentials['database'],
        'db_name = ' + database, 'dbfilter =', 'list_db = False',
        'admin_passwd = ' + credentials['master'],
        'addons_path = /mnt/extra-addons', 'data_dir = /var/lib/odoo',
        'http_interface = 0.0.0.0', 'http_port = 8069',
        'proxy_mode = False', 'workers = 0', 'max_cron_threads = 0',
        'db_maxconn = 24', 'log_level = warn', 'log_db = False',
        'smtp_server = 127.0.0.1', 'smtp_port = 1',
    ]) + '\n'
    (root / 'config' / 'odoo.conf').write_text(config)
    (root / 'config' / 'odoo.conf').chmod(0o644)
    init = '''#!/bin/bash
set -euo pipefail
app_password="$(cat /run/secrets/app_password)"
psql -v ON_ERROR_STOP=1 -U postgres -d postgres -v "app_password=$app_password" <<'SQL'
CREATE ROLE nasqo_rbac_test LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE DATABASE nasqo_rbac_test OWNER postgres;
REVOKE ALL ON DATABASE nasqo_rbac_test FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE nasqo_rbac_test TO nasqo_rbac_test;
REVOKE ALL ON DATABASE postgres FROM PUBLIC;
GRANT CONNECT ON DATABASE postgres TO nasqo_rbac_test;
REVOKE CONNECT ON DATABASE template1 FROM PUBLIC;
SQL
psql -v ON_ERROR_STOP=1 -U postgres -d nasqo_rbac_test <<'SQL'
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO nasqo_rbac_test;
SQL
'''
    (root / 'db-init' / 'init.sh').write_text(init)
    (root / 'db-init').chmod(0o755)
    (root / 'db-init' / 'init.sh').chmod(0o644)
    common = {
        'image': args.odoo_image, 'networks': ['isolated'],
        'volumes': ['./config/odoo.conf:/etc/odoo/odoo.conf:ro',
                    './addons:/mnt/extra-addons:ro', 'filestore:/var/lib/odoo'],
        'mem_limit': '1g', 'cpus': 1.0, 'pids_limit': 256,
        'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges:true'],
        'logging': {'driver': 'json-file', 'options': {'max-size': '5m', 'max-file': '2'}},
    }
    install_modules = sorted(set(modules + ['nasqo_rbac_state_probe']))
    compose = {
        'services': {
            'db': {
                'image': args.postgres_image, 'networks': ['isolated'],
                'environment': {'POSTGRES_PASSWORD_FILE': '/run/secrets/bootstrap_password'},
                'volumes': ['postgres:/var/lib/postgresql/data',
                    './config/postgres.password:/run/secrets/bootstrap_password:ro',
                    './config/database.password:/run/secrets/app_password:ro',
                    './db-init:/docker-entrypoint-initdb.d:ro'],
                'command': ['postgres', '-c', 'shared_buffers=32MB', '-c', 'max_connections=40'],
                'mem_limit': '256m', 'cpus': 0.5,
                'healthcheck': {'test': ['CMD-SHELL', 'pg_isready -U postgres'], 'interval': '2s', 'timeout': '3s', 'retries': 30},
                'logging': common['logging'],
            },
            'install': {**common, 'command': ['odoo', '-c', '/etc/odoo/odoo.conf',
                '--no-http', '--stop-after-init', '--without-demo', '-i', ','.join(install_modules)]},
            'odoo': {**common, 'command': ['odoo', '-c', '/etc/odoo/odoo.conf']},
        },
        'networks': {'isolated': {'internal': True}},
        'volumes': {'postgres': {}, 'filestore': {}},
    }
    (root / 'compose.json').write_text(json.dumps(compose, indent=2))
    (root / 'provenance.json').write_text(json.dumps(inventory, indent=2))
    (root / 'lab.json').write_text(json.dumps({'project': args.project, 'database': database,
        'odoo_image_id': args.odoo_image, 'postgres_image_id': args.postgres_image,
        'synthetic_only': True, 'ports_published': False, 'outbound_network': False}))
    command = ['docker', 'compose', '-p', args.project, '-f', str(root / 'compose.json')]
    with (root / 'private' / 'setup.log').open('w') as log:
        def run(*tail):
            result = subprocess.run(command + list(tail), stdout=log, stderr=log)
            if result.returncode:
                raise SystemExit('Lab command failed; inspect the protected setup log')
        run('up', '-d', 'db')
        for _ in range(60):
            status = subprocess.run(command + ['exec', '-T', 'db', 'pg_isready', '-U', 'postgres'], stdout=log, stderr=log)
            if status.returncode == 0:
                break
            time.sleep(1)
        else:
            raise SystemExit('Isolated database did not become ready')
        print('LAB_PHASE PostgreSQL ready; installing synthetic Odoo database', flush=True)
        run('up', '--no-deps', '--abort-on-container-exit', '--exit-code-from', 'install', 'install')
        print('LAB_PHASE Odoo installation completed', flush=True)
        run('up', '-d', '--no-deps', 'odoo')
    print('LAB_READY ' + json.dumps({'workspace': str(root), 'project': args.project}))


if __name__ == '__main__':
    main()
