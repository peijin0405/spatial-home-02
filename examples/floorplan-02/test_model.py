import unittest,json,pathlib,tempfile,copy
import server
from geometry import boxes,validate
ROOT=pathlib.Path(__file__).parent
class ModelTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();server.P=pathlib.Path(self.tmp.name)
  self.m=json.loads((ROOT/'space.json').read_text());(server.P/'space.json').write_text(json.dumps(self.m))
 def tearDown(self):self.tmp.cleanup()
 def test_openings_are_empty(self):
  validate(self.m)
  for h in self.m['openings']:
   w=next(w for w in self.m['walls'] if w['id']==h['wall_id'])
   for b in boxes(self.m):
    if b['id'].startswith(w['id']+':'):
     import math
     t=math.dist(w['a'],b['position'][:2]);mid=h['offset']+h['width']/2
     if abs(t-mid)<b['size'][0]/2-1e-4:
      self.assertTrue(b['position'][2]+b['size'][2]/2<=h['sill']+1e-4 or b['position'][2]-b['size'][2]/2>=h['sill']+h['height']-1e-4)
 def test_material_keeps_structure(self):
  m=copy.deepcopy(self.m);m['materials']['wall']='#abcdef';saved=server.commit(m)
  self.assertEqual(saved['walls'],self.m['walls']);self.assertEqual(saved['openings'],self.m['openings']);self.assertEqual(saved['revision'],self.m['revision']+1)
 def test_lock(self):
  self.m['walls'][0]['a'][0]+=1
  with self.assertRaises(ValueError):server.commit(self.m)
 def test_outside_room(self):
  self.m['furniture'][0]['position'][0]=100
  with self.assertRaises(AssertionError):server.commit(self.m)
 def test_valid_move(self):
  f=next(f for f in self.m['furniture'] if f['id']=='table');f['position'][1]+=.15
  server.commit(self.m)
 def test_stale_version(self):
  server.commit(copy.deepcopy(self.m))
  with self.assertRaises(ValueError):server.commit(self.m)
if __name__=='__main__':unittest.main()
