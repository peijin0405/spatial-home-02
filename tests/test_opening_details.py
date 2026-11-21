import copy,json,math,pathlib,unittest
from spatial.opening_details import opening_parts
ROOT=pathlib.Path(__file__).resolve().parents[1]
class OpeningDetailsTest(unittest.TestCase):
 def model(self):
  return {'walls':[{'id':'w','a':[2,3],'b':[2,8],'height':2.8,'thickness':.2}], 'openings':[{'id':'d','wall_id':'w','offset':.5,'width':1,'height':2.1,'sill':0,'type':'door'}]}
 def test_hinged_and_rotated_coordinates(self):
  m=self.model();before=copy.deepcopy(m);parts=opening_parts(m);leaf=next(b for b in parts if b['component']=='leaf')
  self.assertEqual(m,before);self.assertAlmostEqual(leaf['rotation'],math.pi/2);self.assertAlmostEqual(leaf['position'][0],2);self.assertAlmostEqual(leaf['position'][1],4)
  self.assertFalse(any('glass' in b['component'] for b in parts))
 def test_window_and_sliding_door(self):
  for sill in (0,.8):
   m=self.model();m['openings'][0].update(type='window',sill=sill,height=1.4)
   parts=opening_parts(m);self.assertEqual(sum(b['opacity']<1 for b in parts),2);self.assertEqual(sum(b['component'].startswith('track') for b in parts),4)
   self.assertTrue(all(b['position'][2]-b['size'][2]/2>=sill-1e-8 for b in parts))
 def test_explicit_styles(self):
  m=self.model();m['openings'][0]['details']={'style':'none'};self.assertEqual(opening_parts(m),[])
  m['openings'][0]['details']['style']='glass_door';self.assertEqual(sum(b['opacity']<1 for b in opening_parts(m)),1)
  m['openings'][0]['details']['style']='typo'
  with self.assertRaises(ValueError):opening_parts(m)
 def test_small_opening_rejected(self):
  m=self.model();m['openings'][0]['width']=.1
  with self.assertRaises(ValueError):opening_parts(m)
 def test_published_models_and_export(self):
  for name in ['floorplan-01','floorplan-02']:
   p=ROOT/'examples'/name;m=json.loads((p/'space.json').read_text());expected=opening_parts(m);geometry=json.loads((p/'geometry.json').read_text())
   self.assertEqual([b for b in geometry if b['kind']=='opening_detail'],expected)
   self.assertEqual(json.loads((ROOT/'demos'/name/'geometry.json').read_text()),geometry)
   g=json.loads((p/'output/space-detailed.gltf').read_text());names={n.get('name') for n in g['nodes']}
   self.assertTrue(all(b['id'] in names for b in expected))
   self.assertEqual(sum(a['alphaMode']=='BLEND' for a in g['materials'] if 'alphaMode' in a),sum(b['opacity']<1 for b in expected))
   for b in expected:self.assertTrue(all(v>0 and math.isfinite(v) for v in b['size']))
if __name__=='__main__':unittest.main()
