"""Regression for the incorrectly placed door behind floorplan 02's sofa."""
import json,math,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class BedroomDoorLocationTest(unittest.TestCase):
 def test_source_and_published_copies(self):
  base=json.loads((ROOT/'examples/floorplan-02/space.json').read_text())
  for folder in ['.','demos/floorplan-02','examples/floorplan-02']:
   m=json.loads((ROOT/folder/'space.json').read_text());self.assertEqual(m,base)
   walls={w['id']:w for w in m['walls']};door=next(h for h in m['openings'] if h['id']=='bed_b_door')
   self.assertEqual(door['wall_id'],'bed_b_entry_wall')
   self.assertFalse(any(h['wall_id']=='bed_b_south' for h in m['openings']))
   entry=walls[door['wall_id']];self.assertEqual(entry['a'],walls['bed_b_south']['a']);self.assertEqual(entry['b'],walls['bath_bed']['b'])
   g=json.loads((ROOT/folder/'geometry.json').read_text());wall=[b for b in g if b['id'].startswith('bed_b_south:')]
   self.assertEqual(len(wall),1);self.assertAlmostEqual(wall[0]['size'][0],math.dist(walls['bed_b_south']['a'],walls['bed_b_south']['b']))
   self.assertEqual(wall[0]['size'][2],2.8)
   leaf=next(b for b in g if b['id']=='bed_b_door:leaf');self.assertAlmostEqual(leaf['rotation'],math.pi/2)
 def test_exports_contain_solid_wall_and_reoriented_door(self):
  for f in ['output/space-detailed.gltf','examples/floorplan-02/output/space-detailed.gltf']:
   g=json.loads((ROOT/f).read_text());nodes={n['name']:n for n in g['nodes']};self.assertEqual(len([n for n in nodes if n.startswith('bed_b_south:')]),1)
   self.assertAlmostEqual(nodes['bed_b_door:leaf']['rotation'][2],math.sin(math.pi/4))
if __name__=='__main__':unittest.main()
