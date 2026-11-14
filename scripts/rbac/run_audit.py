"""Run fixtures or HTTP probes in a previously prepared private audit lab.

Credentials travel from a host-local private file through stdin only. Raw
process logs remain in that private workspace; only marked JSON is returned.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--phase', required=True, choices=['fixtures', 'http', 'followup'])
    args = parser.parse_args()
    root = args.workspace.resolve()
    lab = json.loads((root / 'lab.json').read_text())
    project = lab['project']
    if not re.fullmatch(r'nasqo-rbac-[a-z0-9-]+', project) or lab['database'] != 'nasqo_rbac_test':
        raise SystemExit('Refusing a non-audit environment')
    container = project + '-odoo-1'
    inspected = subprocess.run(['docker', 'inspect', container], capture_output=True, text=True, check=True)
    info = json.loads(inspected.stdout)[0]
    if info['Config']['Labels']['com.docker.compose.project'] != project or info['HostConfig']['PortBindings']:
        raise SystemExit('Unexpected container identity or published ports')
    networks = info['NetworkSettings']['Networks']
    if list(networks) != [project + '_isolated']:
        raise SystemExit('Unexpected network attachment')
    net = json.loads(subprocess.check_output(['docker', 'network', 'inspect', project + '_isolated']))[0]
    if not net['Internal'] or info['Image'] != lab['odoo_image_id']:
        raise SystemExit('Unexpected image or network egress')
    credentials = json.loads((root / 'private' / 'credentials.json').read_text())
    payload = 'credentials = ' + repr(credentials) + '\n'
    scripts = Path(__file__).resolve().parent
    if args.phase == 'fixtures':
        if (root / 'private' / 'fixtures.json').exists():
            raise SystemExit('Fixtures already recorded; preserve existing state')
        payload += (scripts / 'fixtures.py').read_text()
        tail = ['/entrypoint.sh', 'odoo', 'shell', '-c', '/etc/odoo/odoo.conf',
                '-d', lab['database'], '--no-http']
        marker = 'NASQO_RBAC_FIXTURES:'
        target = root / 'private' / 'fixtures.json'
    else:
        fixtures = json.loads((root / 'private' / 'fixtures.json').read_text())
        script = 'http_audit.py' if args.phase == 'http' else 'followup_audit.py'
        payload += 'fixtures = ' + repr(fixtures) + '\n' + (scripts / script).read_text()
        tail = ['python3', '-']
        marker = 'NASQO_RBAC_RESULT:' if args.phase == 'http' else 'NASQO_RBAC_FOLLOWUP:'
        target = root / ('result.json' if args.phase == 'http' else 'followup.json')
    process = subprocess.run(['docker', 'exec', '-i', container] + tail,
                             input=payload, capture_output=True, text=True, timeout=900)
    raw_log = root / 'private' / (args.phase + '.log')
    raw_log.write_text(process.stdout + process.stderr)
    raw_log.chmod(0o600)
    matches = [line[len(marker):] for line in process.stdout.splitlines() if line.startswith(marker)]
    if process.returncode or len(matches) != 1:
        raise SystemExit('Audit phase failed; inspect its protected log after redacting credentials')
    result = json.loads(matches[0])
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    if any(value in serialized for value in credentials.values()):
        raise SystemExit('Refusing an output containing a private audit credential')
    target.write_text(serialized + '\n')
    target.chmod(0o600)
    print(marker + json.dumps(result, sort_keys=True))
    if args.phase != 'fixtures' and result['summary']['fail']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
