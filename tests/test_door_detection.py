import copy,math,pathlib,unittest
import cv2
import numpy as np
from spatial.door_detection import Config,detect_swing_doors,match_to_walls
ROOT=pathlib.Path(__file__).resolve().parents[1]

def symbol(dashed=False):
 im=np.full((280,280,3),255,np.uint8)
 cv2.line(im,(128,10),(128,58),(0,0,0),10)
 cv2.line(im,(128,128),(128,255),(0,0,0),10)
 cv2.line(im,(128,128),(198,128),(0,0,0),2)
 if dashed:
  for a in range(270,360,12):cv2.ellipse(im,(128,128),(70,70),0,a,a+7,(0,0,0),2)
 else:cv2.ellipse(im,(128,128),(70,70),0,270,360,(0,0,0),2)
 return im

class DoorDetectionTest(unittest.TestCase):
 def test_solid_dashed_scaled_rotated(self):
  for dashed in (False,True):
   for scale,angle in [(1,0),(.7,90),(1.5,180),(1,33)]:
    with self.subTest(dashed=dashed,scale=scale,angle=angle):
     matrix=cv2.getRotationMatrix2D((140,140),angle,scale)
     im=cv2.warpAffine(symbol(dashed),matrix,(280,280),borderValue=(255,255,255))
     hinge=matrix@np.array([128,128,1]);r=70*scale
     candidates=detect_swing_doors(im,Config(min_radius=30,max_radius=120))
     self.assertTrue(any(math.dist(c['hinge_px'],hinge)<14 and abs(c['radius_px']-r)<15 for c in candidates),candidates)
 def test_negative_blank_circle_rectangle(self):
  for kind in ('blank','circle','rectangle'):
   im=np.full((280,280,3),255,np.uint8)
   if kind=='circle':
    cv2.circle(im,(140,140),70,(0,0,0),3);cv2.line(im,(70,140),(210,140),(0,0,0),2)
   if kind=='rectangle':cv2.rectangle(im,(50,50),(230,230),(0,0,0),8)
   self.assertEqual(detect_swing_doors(im),[],kind)
 def test_wall_matching_is_non_mutating_and_ambiguous(self):
  c={'hinge_px':[10,10],'closed_tip_px':[90,10]};model={'walls':[{'id':'w','a':[0,0],'b':[2,0]}],'openings':[{'id':'old','wall_id':'w','offset':.1,'width':.8}]};before=copy.deepcopy(model)
  transform=[[.01,0,0],[0,-.01,.1]]
  result=match_to_walls([c],model,transform)[0];self.assertEqual(result['status'],'needs_review');self.assertEqual(result['existing_opening_ids'],['old']);self.assertEqual(model,before)
  model['walls'].append({'id':'parallel','a':[0,.05],'b':[2,.05]});self.assertEqual(match_to_walls([c],model,transform)[0]['status'],'ambiguous_wall')
  with self.assertRaises(ValueError):match_to_walls([c],model,[[0,0,0],[0,0,0]])
 def test_floorplan_two_visible_swing_symbols(self):
  im=cv2.imread(str(ROOT/'examples/floorplan-02/source.png'))
  found=detect_swing_doors(im,Config(min_radius=50,max_radius=140,ignore_colored_annotations=True))
  # Independently annotated visible swing symbols, not generated model openings.
  hinges=[(158,525),(487,492),(995,494)]
  for h in hinges:self.assertTrue(any(math.dist(c['hinge_px'],h)<18 for c in found),h)
  self.assertTrue(all(any(math.dist(c['hinge_px'],h)<18 for h in hinges) for c in found),found)
if __name__=='__main__':unittest.main()
