import bpy,json,pathlib,math,sys
from mathutils import Vector
from geometry import boxes,validate
P=pathlib.Path(__file__).parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
m=json.loads(pathlib.Path(args[0] if args else P/'space.json').read_text());validate(m)
out=P/'output';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.world.color=(.6,.6,.6)
def mat(name,color):
 c=color.lstrip('#');rgb=[int(c[i:i+2],16)/255 for i in (0,2,4)]
 ma=bpy.data.materials.new(name);ma.diffuse_color=(*rgb,1);ma.use_nodes=True;ma.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*rgb,1);return ma
mats={}
for n,b in enumerate(boxes(m),1):
 bpy.ops.mesh.primitive_cube_add(size=1,location=b['position']);o=bpy.context.object;o.name=b['id'];o.dimensions=b['size'];o.rotation_euler[2]=b['rotation'];o.pass_index=n
 if b['color'] not in mats:mats[b['color']]=mat(b['color'],b['color'])
 o.data.materials.append(mats[b['color']])
 if b.get('radius'):
  bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
  bevel=o.modifiers.new('Soft upholstery edges','BEVEL');bevel.width=min(b['radius'],min(b['size'])/2);bevel.segments=6
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
  for face in o.data.polygons:face.use_smooth=True
 if b.get('metallic'):mats[b['color']].node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=b['metallic']

def surface(name,z,material):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(x,y,z) for x,y in m['outline']],[],[list(range(len(m['outline'])))])
 mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.data.materials.append(material);return o
surface('floor',0,mat('floor',m['materials']['floor']))
roof=surface('ceiling',2.8,mat('ceiling','#eeeeee'));roof.hide_render=True;roof.hide_viewport=True
for x,y in [(2,6),(5,6),(8,3),(11,3),(11,6),(13,2)]:
 bpy.ops.object.light_add(type='AREA',location=(x,y,2.65));bpy.context.object.data.energy=180;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=3
bpy.ops.object.light_add(type='SUN',rotation=(.4,-.5,.5));bpy.context.object.data.energy=1.3
cameras=[]
for c in m['cameras']:
 bpy.ops.object.camera_add(location=c['position']);o=bpy.context.object;o.name=c['id'];o.rotation_euler=(Vector(c['target'])-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='PERSP';o.data.lens=36/(2*math.tan(math.radians(c['fov'])/2));cameras.append(o)
scene.camera=cameras[0]
layer=scene.view_layers[0];layer.use_pass_z=True;layer.use_pass_normal=True;layer.use_pass_object_index=True
bpy.ops.wm.save_as_mainfile(filepath=str(out/'space.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'space.glb'),export_format='GLB',export_cameras=True,export_lights=True,use_visible=True)
for c in cameras:
 scene.camera=c;roof.hide_render=c.name=='overview'
 scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/(c.name+'.png'));bpy.ops.render.render(write_still=True)
 scene.render.image_settings.media_type='MULTI_LAYER_IMAGE';scene.render.image_settings.file_format='OPEN_EXR_MULTILAYER';scene.render.filepath=str(out/(c.name+'.exr'));bpy.data.images['Render Result'].save_render(scene.render.filepath,scene=scene)
(out/'render_manifest.json').write_text(json.dumps({'space_revision':m['revision'],'cameras':m['cameras'],'passes':['Combined','Depth (metres)','Normal (world)','IndexOB'],'note':'EXR channels need conversion to the target generation API conventions; not ready-made ControlNet input.'},indent=2))
print('COMPLETE')
