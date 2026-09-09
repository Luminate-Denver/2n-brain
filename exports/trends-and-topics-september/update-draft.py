"""Update approved September copy in the existing draft; no email send."""
import json,urllib.request
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[1]
e={}
for line in (R/'.env').read_text().splitlines():
 if '=' in line and not line.strip().startswith('#'):
  k,v=line.split('=',1);e[k.strip()]=v.strip().strip('\"').strip("'")
b=e['AC_API_URL'].rstrip('/');h={'Api-Token':e['AC_API_KEY'],'Content-Type':'application/json'}
def call(path,data=None):
 req=urllib.request.Request(b+path,headers=h,data=json.dumps(data).encode() if data else None,method='PUT' if data else 'GET')
 with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
assert str(call('/api/3/campaigns/46')['campaign']['status'])=='0'
html=(D/'trends-and-topics-september-v1.html').read_text();assert '—' not in html
call('/api/3/messages/57',{'message':{'html':html,'subject':'2^n Family Office Brief: September 2026','fromname':'2^n: trends&topics','fromemail':'mb@2pwrn.com','reply2':'mb@2pwrn.com','format':'mime','charset':'utf-8','encoding':'8bit','language_code':'en'}})
assert call('/api/3/messages/57')['message']['html']==html
assert str(call('/api/3/campaigns/46')['campaign']['status'])=='0'
print('Draft 46 updated and verified. No test sent.')
