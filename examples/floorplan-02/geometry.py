import math,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from spatial.opening_details import opening_parts
from spatial.door_audit import enforce_door_bindings, write_audit_report

def boxes(m):
 enforce_door_bindings(m)
 out=[]
 def box(id,p,s,r=0,kind='wall',color=None):out.append(dict(id=id,position=p,size=s,rotation=r,kind=kind,color=color or m['materials'][kind]))
 for w in m['walls']:
  ax,ay=w['a'];bx,by=w['b'];L=math.hypot(bx-ax,by-ay);r=math.atan2(by-ay,bx-ax)
  holes=[h for h in m['openings'] if h['wall_id']==w['id']]
  cuts=sorted(set([0,L]+[v for h in holes for v in (h['offset'],h['offset']+h['width'])]))
  for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
   h=next((h for h in holes if h['offset']<=((a+b)/2)<=h['offset']+h['width']),None)
   spans=[(0,w['height'])] if not h else [(0,h['sill']),(h['sill']+h['height'],w['height'])]
   for j,(lo,hi) in enumerate(spans):
    if hi-lo>1e-5:box(f"{w['id']}:{i}:{j}",[ax+math.cos(r)*(a+b)/2,ay+math.sin(r)*(a+b)/2,(lo+hi)/2],[b-a,w['thickness'],hi-lo],r)
 for f in m['furniture']:
  x,y,z=f['position'];sx,sy,sz=f['size'];r=math.radians(f['rotation'])
  if f.get('components'):
   for c in f['components']:
    dx,dy,dz=[c['center'][i]*f['size'][i] for i in range(3)]
    box(f['id']+':'+c['name'],[x+dx*math.cos(r)-dy*math.sin(r),y+dx*math.sin(r)+dy*math.cos(r),z+dz],[c['size'][i]*f['size'][i] for i in range(3)],r,'furniture',c.get('color') or f['color'])
    out[-1].update(radius=c.get('radius',0),metallic=c.get('metallic',0))
  else:box(f['id'],[x,y,z+sz/2],[sx,sy,sz],r,'furniture',f['color'])
 out.extend(opening_parts(m))
 return out

def validate(m):
 enforce_door_bindings(m)
 ids=[w['id'] for w in m['walls']]+[h['id'] for h in m['openings']]
 assert len(ids)==len(set(ids)), 'Duplicate structural ID'
 for w in m['walls']:
  L=math.dist(w['a'],w['b']);previous=0
  for h in sorted([h for h in m['openings'] if h['wall_id']==w['id']],key=lambda h:h['offset']):
   assert 0<=h['offset'] and h['offset']+h['width']<=L+1e-3,(w['id'],h['id'])
   assert h['offset']>=previous and h['width']>0
   assert h['sill']>=0 and h['height']>0 and h['sill']+h['height']<=w['height']
   previous=h['offset']+h['width']
 assert all(h['wall_id'] in {w['id'] for w in m['walls']} for h in m['openings'])
 return True
if __name__=='__main__':
 import json,pathlib
 p=pathlib.Path(__file__).parent;m=json.loads((p/'space.json').read_text());write_audit_report(m,p);validate(m)
 (p/'geometry.json').write_text(json.dumps(boxes(m)))
 print('Validated',len(m['walls']),'walls,',len(m['openings']),'openings')
