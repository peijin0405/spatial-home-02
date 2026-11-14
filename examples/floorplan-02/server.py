from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import pathlib,json,os,math,threading,fcntl
from contextlib import contextmanager
from geometry import validate,boxes
P=pathlib.Path(__file__).parent;os.chdir(P);lock=threading.Lock()
def inside(p,poly):
 x,y=p;c=False
 for i,a in enumerate(poly):
  b=poly[i-1]
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:c=not c
 return c

@contextmanager
def transaction():
 with lock:
  with (P/'.write.lock').open('a') as handle:
   fcntl.flock(handle,fcntl.LOCK_EX)
   try:yield
   finally:fcntl.flock(handle,fcntl.LOCK_UN)

def commit(m):
 with transaction():
  old=json.loads((P/'space.json').read_text())
  if m['revision']!=old['revision']:raise ValueError('版本冲突，请刷新页面')
  for k in old:
   if k not in ['furniture','materials','cameras'] and m.get(k)!=old[k]:raise ValueError('结构和来源信息不可通过设计接口修改：'+k)
  if {f['id'] for f in m['furniture']}!={f['id'] for f in old['furniture']}:raise ValueError('家具 ID 不可增删')
  validate(m)
  for f in m['furniture']:
   assert all(isinstance(n,(int,float)) and math.isfinite(n) for n in f['position']+f['size']+[f['rotation']]),'家具参数非法'
   assert all(n>0 for n in f['size']),'尺寸必须为正'
   poly=next(r['polygon'] for r in m['rooms'] if r['id']==f['room_id'])
   # only reject new placements; traced original placeholders may need further review
   prev=next(a for a in old['furniture'] if a['id']==f['id'])
   if any(f[k]!=prev[k] for k in ['position','size','rotation','room_id']):
    x,y,z=f['position'];sx,sy,sz=f['size'];r=math.radians(f['rotation'])
    assert z>=0 and z+sz<=m['assumptions']['ceiling_height'],'家具高度越界'
    for dx,dy in [(-sx/2,-sy/2),(-sx/2,sy/2),(sx/2,-sy/2),(sx/2,sy/2)]:
     assert inside((x+dx*math.cos(r)-dy*math.sin(r),y+dx*math.sin(r)+dy*math.cos(r)),poly),f['name']+' 超出所属房间'
    # conservative planar rectangle SAT against all wall pieces overlapping object height
    def overlap(b):
     if z>=b['position'][2]+b['size'][2]/2 or z+sz<=b['position'][2]-b['size'][2]/2:return False
     rr=b['rotation'];axes=[(math.cos(r),math.sin(r)),(-math.sin(r),math.cos(r)),(math.cos(rr),math.sin(rr)),(-math.sin(rr),math.cos(rr))]
     for ax,ay in axes:
      d=abs((x-b['position'][0])*ax+(y-b['position'][1])*ay)
      a=sx/2*abs(math.cos(r)*ax+math.sin(r)*ay)+sy/2*abs(-math.sin(r)*ax+math.cos(r)*ay)
      bb=b['size'][0]/2*abs(math.cos(rr)*ax+math.sin(rr)*ay)+b['size'][1]/2*abs(-math.sin(rr)*ax+math.cos(rr)*ay)
      if d>=a+bb-1e-5:return False
     return True
    assert not any(overlap(b) for b in boxes(m) if b['kind']=='wall'),f['name']+' 与墙体相交'
  (P/'history').mkdir(exist_ok=True);(P/'history'/f"space-v{old['revision']}.json").write_text(json.dumps(old,ensure_ascii=False,indent=2))
  m['revision']+=1
  temp=P/'space.tmp';temp.write_text(json.dumps(m,ensure_ascii=False,indent=2));temp.replace(P/'space.json')
  (P/'geometry.json').write_text(json.dumps(boxes(m)))
  return m
class Handler(SimpleHTTPRequestHandler):
 def do_POST(self):
  if self.path!='/api/save':self.send_error(404);return
  try:
   if int(self.headers.get('Content-Length',0))>1000000:raise ValueError('请求过大')
   m=json.loads(self.rfile.read(int(self.headers['Content-Length'])));result=commit(m);code=200
  except Exception as e:result={'error':str(e)};code=400
  self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(result,ensure_ascii=False).encode())
if __name__=='__main__':
 print('http://127.0.0.1:8770',flush=True);ThreadingHTTPServer(('127.0.0.1',8770),Handler).serve_forever()
