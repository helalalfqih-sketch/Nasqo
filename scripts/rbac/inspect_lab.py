"""Inspect only a named audit lab; print metadata and credential-match counts."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    root = args.workspace.resolve()
    lab = json.loads((root / 'lab.json').read_text())
    project = lab['project']
    if not re.fullmatch(r'nasqo-rbac-[a-z0-9-]+', project) or lab['database'] != 'nasqo_rbac_test':
        raise SystemExit('Refusing a non-audit environment')
    credentials = json.loads((root / 'private/credentials.json').read_text())
    result = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'lab': lab, 'containers': {}, 'known_credential_matches': {}}
    for service in ['db', 'install', 'odoo']:
        name = project + '-' + service + '-1'
        info = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
        assert info['Config']['Labels']['com.docker.compose.project'] == project
        result['containers'][service] = {
            'state': info['State']['Status'], 'exit_code': info['State']['ExitCode'],
            'oom_killed': info['State']['OOMKilled'], 'image': info['Image'],
            'networks': list(info['NetworkSettings']['Networks']),
            'ports_published': bool(info['HostConfig']['PortBindings']),
            'volumes': [m['Name'] for m in info['Mounts'] if m['Type'] == 'volume'],
            'bind_destinations': [m['Destination'] for m in info['Mounts'] if m['Type'] == 'bind'],
        }
        logs = subprocess.run(['docker', 'logs', name], capture_output=True)
        data = logs.stdout + logs.stderr
        result['known_credential_matches'][service + '_docker_logs'] = sum(
            data.count(value.encode()) for value in credentials.values())
    network = json.loads(subprocess.check_output(['docker', 'network', 'inspect', project + '_isolated']))[0]
    result['network_internal'] = network['Internal']
    query = """SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication
        FROM pg_roles WHERE rolname = 'nasqo_rbac_test';"""
    result['database_role_flags'] = subprocess.check_output([
        'docker', 'exec', project + '-db-1', 'psql', '-U', 'postgres',
        '-d', lab['database'], '-Atc', query], text=True).strip()
    config = configparser.ConfigParser()
    config.read(root / 'config/odoo.conf')
    result['safe_config'] = {key: config['options'][key] for key in [
        'db_name', 'list_db', 'proxy_mode', 'max_cron_threads', 'smtp_server', 'smtp_port']}
    provenance = json.loads((root / 'provenance.json').read_text())
    result['source_snapshot_matches'] = all(
        hashlib.sha256((root / 'addons' / name / relative).read_bytes()).hexdigest() == digest
        for name, files in provenance['nasqo_source_hashes'].items()
        for relative, digest in files.items())
    for relative in ['result.json', 'followup.json', 'private/fixtures.json', 'private/fixtures.log',
                     'private/http.log', 'private/followup.log',
                     'private/setup.log', 'private/setup-resume.log']:
        path = root / relative
        if path.exists():
            data = path.read_bytes()
            result['known_credential_matches'][relative] = sum(
                data.count(value.encode()) for value in credentials.values())
    result['scan_limit'] = 'Exact generated lab credentials only; not a general secret or dependency vulnerability scan.'
    (root / 'infrastructure.json').write_text(json.dumps(result, indent=2) + '\n')
    print('NASQO_RBAC_INFRASTRUCTURE:' + json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
