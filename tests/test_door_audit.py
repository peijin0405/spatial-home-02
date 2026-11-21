import copy,importlib.util,json,math,pathlib,shutil,tempfile,unittest
from spatial.door_audit import audit_door_bindings,enforce_door_bindings,DoorBindingError
ROOT=pathlib.Path(__file__).resolve().parents[1]
def fixture():
 return {'revision':1,'source':'source.png','calibration':{'pixel_to_world':[[.01,0,0],[0,-.01,2]]},
 'walls':[{'id':'vertical','a':[1,0],'b':[1,2]},{'id':'wrong','a':[0,1],'b':[2,1]}],
 'openings':[{'id':'door','type':'door','wall_id':'vertical','offset':1,'width':.8,
 'source_evidence':{'source_image':'source.png','hinge_px':[100,100],'leaf_tip_px':[20,100],'closed_tip_px':[100,20],'review_status':'confirmed'}}]}
class DoorAuditTest(unittest.TestCase):
 def test_valid_and_non_mutating(self):
  m=fixture();before=copy.deepcopy(m);self.assertEqual(enforce_door_bindings(m)['status'],'validated');self.assertEqual(m,before)
 def test_wrong_wall_is_blocked_even_if_door_fits(self):
  m=fixture();m['openings'][0].update(wall_id='wrong',offset=.2)
  with self.assertRaises(DoorBindingError) as ctx:enforce_door_bindings(m)
  self.assertIn('direction_mismatch',{e['code'] for e in ctx.exception.report['errors']})
 def test_missing_wall_and_ambiguity(self):
  for mode in ('missing','ambiguous'):
   m=fixture()
   if mode=='missing':m['walls']=m['walls'][1:]
   else:m['walls'].append({'id':'parallel','a':[1.04,0],'b':[1.04,2]})
   with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
 def test_endpoint_offset_width_and_source_checks(self):
  for mutate in [lambda h:h.update(offset=.4),lambda h:h.update(width=.4),lambda h:h['source_evidence'].update(source_image='other.png'),lambda h:h['source_evidence'].update(review_status='pending')]:
   m=fixture();mutate(m['openings'][0])
   with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
 def test_bad_calibration(self):
  for matrix in (None,[[0,0,0],[0,0,0]],[[float('nan'),0,0],[0,1,0]]):
   m=fixture();m['calibration']['pixel_to_world']=matrix
   with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
 def test_legacy_is_draft_not_validated(self):
  m=fixture();m['openings'][0].pop('source_evidence');r=enforce_door_bindings(m);self.assertEqual(r['status'],'requires_review')
 def test_reversed_wall_endpoints(self):
  m=fixture();m['walls'][0].update(a=[1,2],b=[1,0]);m['openings'][0]['offset']=.2
  self.assertEqual(enforce_door_bindings(m)['status'],'validated')
 def test_detection_reconciliation(self):
  m=fixture();c={'id':'c','hinge_px':[100,100],'leaf_tip_px':[20,100],'closed_tip_px':[100,20]};m['door_candidates']=[c]
  with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
  c['review']={'status':'accepted','opening_id':'door'};enforce_door_bindings(m)
  c['closed_tip_px']=[180,100]
  with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
  c['review']={'status':'rejected','reason':'furniture symbol'};enforce_door_bindings(m)
 def test_western_bedroom_source_and_topology(self):
  m=json.loads((ROOT/'examples/floorplan-02/space.json').read_text());h=next(h for h in m['openings'] if h['id']=='bed_a_door');self.assertEqual(h['wall_id'],'bed_a_entry_wall')
  r=enforce_door_bindings(m);binding=next(b for b in r['bindings'] if b['opening_id']=='bed_a_door');self.assertAlmostEqual(binding['angle_degrees'],0)
  self.assertFalse(any(h['id']=='bed_a_door' and h['wall_id']=='bed_a_south' for h in m['openings']))
  h['wall_id']='bed_a_south';h['offset']=2.7975
  with self.assertRaises(DoorBindingError):enforce_door_bindings(m)
 def test_export_and_direct_boxes_cannot_bypass_audit(self):
  spec=importlib.util.spec_from_file_location('detailed_export',ROOT/'scripts/export_detailed_gltf.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  m=json.loads((ROOT/'examples/floorplan-02/space.json').read_text());next(h for h in m['openings'] if h['id']=='bed_a_door').update(wall_id='bed_a_south',offset=2.7975)
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'space.json').write_text(json.dumps(m));shutil.copyfile(ROOT/'examples/floorplan-02/geometry.py',p/'geometry.py');(p/'output').mkdir();out=p/'output/space-detailed.gltf';out.write_text('previous artifact')
   with self.assertRaises(DoorBindingError):module.export(p)
   self.assertEqual(out.read_text(),'previous artifact');self.assertEqual(json.loads((p/'door-audit.json').read_text())['status'],'blocked')
  spec=importlib.util.spec_from_file_location('geometry_audit_test',ROOT/'examples/floorplan-02/geometry.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
  with self.assertRaises(DoorBindingError):geo.boxes(m)
if __name__=='__main__':unittest.main()
