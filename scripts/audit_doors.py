"""Audit a space JSON without changing it. Exit 2 on conflicts, 1 if unreviewed."""
import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from spatial.door_audit import audit_door_bindings
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('space');args=parser.parse_args()
 report=audit_door_bindings(json.loads(pathlib.Path(args.space).read_text()))
 print(json.dumps(report,ensure_ascii=False,indent=2))
 sys.exit(2 if report['errors'] else 1 if report['warnings'] else 0)
