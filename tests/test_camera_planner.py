import copy,importlib.util,json,math,pathlib,unittest
from spatial.camera_planner import CameraConfig,plan_cameras,prepare_box,intersects_segment,safe_position,project,basis,inside
ROOT=pathlib.Path(__file__).resolve().parents[1]
def model():
 return {'revision':1,'outline':[[0,0],[8,0],[8,6],[0,6]],'rooms':[{'id':'room','polygon':[[0,0],[8,0],[8,6],[0,6]]}], 'walls':[],'openings':[],'furniture':[{'id':'sofa','position':[6,3,0],'size':[1,2,1],'rotation':0}]}
def block(ident,p,s,rotation=0,opacity=1):return {'id':ident,'position':p,'size':s,'rotation':rotation,'kind':'wall','opacity':opacity}
class CameraPlannerTest(unittest.TestCase):
 def test_rotated_ray_box(self):
  b=prepare_box(block('w',[0,0,1],[2,.2,2],math.pi/2))
  self.assertTrue(intersects_segment([-2,0,1],[2,0,1],b));self.assertFalse(intersects_segment([-2,2,1],[2,2,1],b))
 def test_body_avoids_low_furniture_and_glass(self):
  for opacity in (1,.22):
   b=prepare_box(block('box',[1,1,.3],[1,1,.6],opacity=opacity))
   self.assertFalse(safe_position([1,1,1.6],[b],.2));self.assertTrue(safe_position([3,3,1.6],[b],.2))
 def test_valid_stable_and_not_mutating(self):
  m=model();before=copy.deepcopy(m);cfg=CameraConfig(max_positions=60);a=plan_cameras(m,[],'room',['sofa'],cfg);self.assertEqual(a,plan_cameras(m,[],'room',['sofa'],cfg));self.assertEqual(m,before);self.assertEqual(a['status'],'ok')
  for c in a['cameras']:
   self.assertTrue(inside(c['position'][:2],m['rooms'][0]['polygon']));self.assertEqual(c['roll_degrees'],0);self.assertFalse(c['cutaway'])
   self.assertGreaterEqual(c['metrics']['sampled_visibility']['sofa'],.75)
 def test_wall_blocked_room_returns_no_view(self):
  m=model();m['rooms'][0]['polygon']=[[0,0],[3,0],[3,6],[0,6]]
  p=[block('wall',[4,3,1.4],[.2,6,2.8])]
  result=plan_cameras(m,p,'room',['sofa']);self.assertEqual(result['status'],'no_feasible_view');self.assertEqual(result['cameras'],[])
 def test_glazing_does_not_hide_target(self):
  m=model();m['rooms'][0]['polygon']=[[0,0],[3,0],[3,6],[0,6]]
  result=plan_cameras(m,[block('glass',[4,3,1.4],[.01,6,2.8],opacity=.22)],'room',['sofa']);self.assertEqual(result['status'],'ok')
 def test_projection_rejects_behind(self):
  axes=basis([0,0,1],[1,0,1]);self.assertIsNone(project([-1,0,1],[0,0,1],axes,60,1.6,.05,100));self.assertEqual(project([1,0,1],[0,0,1],axes,60,1.6,.05,100),(0,0))
 def test_invalid_inputs(self):
  for room,targets in [('missing',['sofa']),('room',['unknown']),('room',[])]:
   with self.assertRaises(ValueError):plan_cameras(model(),[],room,targets)
  with self.assertRaises(ValueError):plan_cameras(model(),[],'room',['sofa'],CameraConfig(aspect=0))
 def test_real_examples_and_balcony_failure(self):
  for n,targets in [('floorplan-01',['sofa','table']),('floorplan-02',['sofa','dining'])]:
   p=ROOT/'examples'/n;m=json.loads((p/'space.json').read_text());parts=json.loads((p/'geometry.json').read_text());r=plan_cameras(m,parts,'living',targets);self.assertEqual(r['status'],'ok' if n=='floorplan-01' else 'requires_review')
   for c in r['cameras']:
    self.assertTrue(safe_position(c['position'],[prepare_box(b) for b in parts],.2));self.assertTrue(all(v>=.75 for v in c['metrics']['sampled_visibility'].values()))
   if n=='floorplan-02':self.assertEqual(plan_cameras(m,parts,'balcony',targets)['status'],'no_feasible_view')
if __name__=='__main__':unittest.main()
