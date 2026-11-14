"""Agent-safe operations. All updates pass through the same locked-structure validator."""
import argparse,json,pathlib
from server import commit
p=argparse.ArgumentParser();p.add_argument('operation',choices=['move','material','inspect']);p.add_argument('--id');p.add_argument('--x',type=float);p.add_argument('--y',type=float);p.add_argument('--rotation',type=float);p.add_argument('--color');a=p.parse_args()
root=pathlib.Path(__file__).parent;m=json.loads((root/'space.json').read_text())
if a.operation=='inspect':print(json.dumps(m,ensure_ascii=False,indent=2));raise SystemExit
if a.operation=='move':
 f=next(f for f in m['furniture'] if f['id']==a.id)
 for i,v in enumerate([a.x,a.y]):
  if v is not None:f['position'][i]=v
 if a.rotation is not None:f['rotation']=a.rotation
elif a.operation=='material':
 if a.id not in ['wall','floor','furniture']:raise ValueError('unknown material')
 m['materials'][a.id]=a.color
 if a.id=='furniture':
  for f in m['furniture']:f['color']=a.color
print('Saved revision',commit(m)['revision'])
