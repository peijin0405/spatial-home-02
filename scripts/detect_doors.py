"""Run geometric door proposals and write JSON + a review overlay."""
import argparse,json,pathlib,sys
import cv2
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from spatial.door_detection import Config,detect_swing_doors,match_to_walls
from spatial.door_audit import audit_door_bindings

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('image');p.add_argument('--output',required=True);p.add_argument('--min-radius',type=float,default=32);p.add_argument('--max-radius',type=float,default=260);p.add_argument('--ignore-colored-annotations',action='store_true');p.add_argument('--space');p.add_argument('--calibration',help='JSON 2x3 affine matrix; required with --space');args=p.parse_args()
 if bool(args.space)!=bool(args.calibration):p.error('--space and --calibration must be provided together')
 image=cv2.imread(args.image)
 if image is None:p.error('Cannot read image')
 candidates=detect_swing_doors(image,Config(min_radius=args.min_radius,max_radius=args.max_radius,ignore_colored_annotations=args.ignore_colored_annotations))
 if args.space:candidates=match_to_walls(candidates,json.loads(pathlib.Path(args.space).read_text()),json.loads(pathlib.Path(args.calibration).read_text()))
 out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
 report={'schema_version':1,'image':str(args.image),'coordinate_system':'input pixels: x right, y down','review_required':True,'limitations':['Geometric proposals, not calibrated probabilities','Sliding doors, heavily occluded arcs and perspective distortion require other detectors or manual review','No automatic edits to space.json'],'candidates':candidates}
 if args.space:
  report['model_binding_audit']=audit_door_bindings(json.loads(pathlib.Path(args.space).read_text()))
  report['unresolved_candidate_ids']=[c['id'] for c in candidates if c['status']!='needs_review' or len(c.get('existing_opening_ids',[]))!=1]
 (out/'doors.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 overlay=image.copy()
 for c in candidates:
  h=tuple(round(v) for v in c['hinge_px']);leaf=tuple(round(v) for v in c['leaf_tip_px']);closed=tuple(round(v) for v in c['closed_tip_px'])
  cv2.circle(overlay,h,4,(0,0,255),-1);cv2.line(overlay,h,leaf,(0,160,0),2);cv2.line(overlay,h,closed,(255,100,0),2);cv2.putText(overlay,c['id'].removeprefix('door_candidate_')+':'+str(c['score']),h,cv2.FONT_HERSHEY_SIMPLEX,.45,(0,0,255),1)
 if not cv2.imwrite(str(out/'doors-overlay.png'),overlay):raise OSError('Cannot save overlay')
 print(f'{len(candidates)} candidates; review {out}/doors-overlay.png; no model changed')
if __name__=='__main__':main()
