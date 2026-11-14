import bpy
from pathlib import Path
from mathutils import Vector
p=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(p/'output/space.blend'))
s=bpy.context.scene
bpy.ops.object.camera_add(location=(6.8,2.0,1.65))
c=bpy.context.object;c.name='sofa_in_living';c.rotation_euler=(Vector((9.75,4.4,.65))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=24;s.camera=c
bpy.data.objects['ceiling'].hide_render=False
s.cycles.samples=32;s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.filepath=str(p/'output/sofa-in-living.png')
bpy.ops.render.render(write_still=True)
