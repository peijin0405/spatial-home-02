"""Choose reproducible camera presets without GPU, ML or new runtime dependencies."""
import argparse,importlib.util,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from spatial.camera_planner import CameraConfig,plan_cameras
from spatial.door_audit import enforce_door_bindings

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('example');p.add_argument('--room',required=True);p.add_argument('--targets',nargs='+',required=True);p.add_argument('--output',required=True);p.add_argument('--max-positions',type=int,default=180);p.add_argument('--aspect',type=float,default=1.6);args=p.parse_args()
 root=pathlib.Path(args.example).resolve();model=json.loads((root/'space.json').read_text());audit=enforce_door_bindings(model)
 spec=importlib.util.spec_from_file_location('planning_geometry',root/'geometry.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo);geo.validate(model)
 result=plan_cameras(model,geo.boxes(model),args.room,args.targets,CameraConfig(max_positions=args.max_positions,aspect=args.aspect));result['door_audit_status']=audit['status']
 out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'camera_count':len(result['cameras']),'search_stats':result['search_stats']},ensure_ascii=False))
 return 0 if result['status']=='ok' else 3 if result['status']=='requires_review' else 2
if __name__=='__main__':sys.exit(main())
