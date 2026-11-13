"""Print scanner outcomes without disclosing matched secrets/source snippets."""
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit('BLOCKED: scanner did not produce a report')
report = json.loads(path.read_text())
vulnerabilities = set()
secret_count = 0
for result in report.get('Results', []):
    secret_count += len(result.get('Secrets', []))
    if result.get('Vulnerabilities'):
        print('Vulnerability target:', result.get('Target'), 'type:', result.get('Type'))
    for item in result.get('Vulnerabilities', []):
        vulnerabilities.add((item['VulnerabilityID'], item['PkgName'], item['Severity']))
print(f'High/critical vulnerabilities: {len(vulnerabilities)}; secret findings: {secret_count}')
for identifier, package, severity in sorted(vulnerabilities):
    print(identifier, package, severity)
if vulnerabilities or secret_count:
    raise SystemExit('FAIL: review findings before accepting this update')
print('PASS: scanner reported no selected findings (not a full security certification)')
