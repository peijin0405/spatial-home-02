"""Export current generated geometry (including glass) without a Blender install.
Usage: python3 scripts/export_detailed_gltf.py examples/floorplan-01
"""
import base64,importlib.util,json,math,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from spatial.door_audit import write_audit_report

def export(directory):
 p=pathlib.Path(directory).resolve();m=json.loads((p/'space.json').read_text())
 spec=importlib.util.spec_from_file_location('export_geometry',p/'geometry.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 audit=write_audit_report(m,p)
 module.validate(m);parts=module.boxes(m)
 vertices=[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5],[-.5,-.5,.5],[.5,-.5,.5],[.5,.5,.5],[-.5,.5,.5]]
 faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
 # Flat face normals avoid unsupported normal synthesis in importers.
 positions=[];normals=[]
 for face in faces:
  a,b,c=[vertices[i] for i in face];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
  n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
  for vertex in (a,b,c):positions.extend(vertex);normals.extend(n)
 binary=bytearray();views=[];accessors=[]
 def attribute(values,kind='VEC3'):
  offset=len(binary);binary.extend(struct.pack('<'+'f'*len(values),*values));views.append(dict(buffer=0,byteOffset=offset,byteLength=len(binary)-offset,target=34962))
  a=dict(bufferView=len(views)-1,componentType=5126,count=len(values)//3,type=kind,min=[min(values[i::3]) for i in range(3)],max=[max(values[i::3]) for i in range(3)]);accessors.append(a);return len(accessors)-1
 pos=attribute(positions);normal=attribute(normals)
 materials=[];meshes=[];nodes=[]
 for b in parts:
  alpha=b.get('opacity',1);color=b['color'];rgb=[(int(color[i:i+2],16)/255)**2.2 for i in (1,3,5)]
  materials.append(dict(pbrMetallicRoughness=dict(baseColorFactor=rgb+[alpha],metallicFactor=b.get('metallic',0),roughnessFactor=.15 if alpha<1 else .85),alphaMode='BLEND' if alpha<1 else 'OPAQUE',doubleSided=alpha<1))
  meshes.append(dict(primitives=[dict(attributes={'POSITION':pos,'NORMAL':normal},material=len(materials)-1)]));r=b['rotation']
  nodes.append(dict(name=b['id'],mesh=len(meshes)-1,translation=b['position'],scale=b['size'],rotation=[0,0,math.sin(r/2),math.cos(r/2)]))
 # Ear-clipping keeps the non-convex footprint rather than filling exterior recesses.
 polygon=[list(v) for v in m['outline']]
 cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 if sum(a[0]*polygon[(i+1)%len(polygon)][1]-polygon[(i+1)%len(polygon)][0]*a[1] for i,a in enumerate(polygon))<0:polygon.reverse()
 triangles=[]
 while len(polygon)>3:
  for i,b in enumerate(polygon):
   a=polygon[i-1];c=polygon[(i+1)%len(polygon)]
   if abs(cross(a,b,c))<1e-10:polygon.pop(i);break
   if cross(a,b,c)<0:continue
   if any(all(cross(u,v,q)>=-1e-10 for u,v in [(a,b),(b,c),(c,a)]) for j,q in enumerate(polygon) if j not in {(i-1)%len(polygon),i,(i+1)%len(polygon)}):continue
   triangles.extend([a,b,c]);polygon.pop(i);break
  else:raise ValueError('Invalid floor outline')
 triangles.extend(polygon)
 fp=attribute([v for point in triangles for v in (*point,-.015)]);fn=attribute([v for _ in triangles for v in (0,0,1)])
 color=m['materials']['floor'];materials.append({'pbrMetallicRoughness':{'baseColorFactor':[(int(color[i:i+2],16)/255)**2.2 for i in (1,3,5)]+[1],'metallicFactor':0,'roughnessFactor':.9},'doubleSided':True})
 meshes.append({'primitives':[{'attributes':{'POSITION':fp,'NORMAL':fn},'material':len(materials)-1}]});nodes.append({'name':'floor','mesh':len(meshes)-1})
 root=len(nodes);nodes.append({'name':'Metres Z-up to Y-up','rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':list(range(root))})
 g=dict(extras={'door_audit':audit},asset={'version':'2.0','generator':'spatial-home opening details'},scene=0,scenes=[{'nodes':[root]}],nodes=nodes,meshes=meshes,materials=materials,bufferViews=views,accessors=accessors,buffers=[{'byteLength':len(binary),'uri':'data:application/octet-stream;base64,'+base64.b64encode(binary).decode()}])
 out=p/'output/space-detailed.gltf';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(g));return out
if __name__=='__main__':print(export(sys.argv[1]))
