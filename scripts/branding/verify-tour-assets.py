import requests
from urllib.parse import urljoin,urlparse
import os
base=os.environ.get('NASQO_TEST_BASE_URL','http://127.0.0.1:8069').rstrip('/')
for debug in ['', 'assets']:
 response=requests.get(base+'/web/bundle/web_tour.interactive',params={'lang':'ar_001','debug':debug},timeout=90)
 assert response.status_code==200
 entries=response.json()
 assert isinstance(entries,list) and entries
 for entry in entries:
  assert isinstance(entry,dict) and entry.get('src') and entry.get('type')
  url=urljoin(base,entry['src'])
  assert urlparse(url).netloc==urlparse(base).netloc
  result=requests.get(url,timeout=90)
  assert result.status_code==200 and result.content
 print('PASS web_tour.interactive JSON and referenced assets:',debug or 'normal',len(entries))
