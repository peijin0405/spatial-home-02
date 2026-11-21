"""Deterministic, dependency-free camera proposals for Z-up interior box scenes.
Visibility is sampled geometric visibility, not a photometric beauty guarantee.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import math

@dataclass(frozen=True)
class CameraConfig:
    eye_height: float = 1.6
    clearance: float = .20
    grid_step: float = .6
    max_positions: int = 180
    vertical_fovs: tuple = (50., 60., 70.)
    aspect: float = 1.6
    frame_margin: float = .08
    min_visibility: float = .75
    min_occupancy: float = .06
    max_occupancy: float = .65
    near: float = .05
    far: float = 100.
    top_k: int = 3
    min_quality: float = .70

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a)
    return tuple(x/n for x in a) if n>1e-9 else (0.,0.,0.)
def inside(p,polygon):
    x,y=p;yes=False
    for i,a in enumerate(polygon):
        b=polygon[i-1]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes

def prepare_box(b):
    return (b['position'],tuple(s/2 for s in b['size']),math.cos(b['rotation']),math.sin(b['rotation']),b)

def local(p,box):
    center,_,c,s,_=box;x,y,z=sub(p,center)
    return (x*c+y*s,-x*s+y*c,z)

def intersects_segment(start,end,box):
    """Slab test in the oriented box's local coordinates; endpoint excluded."""
    a=local(start,box);b=local(end,box);v=sub(b,a);lo=0.;hi=1.-1e-5
    for i,half in enumerate(box[1]):
        if abs(v[i])<1e-10:
            if abs(a[i])>half:return False
        else:
            t0=(-half-a[i])/v[i];t1=(half-a[i])/v[i]
            lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
            if lo>hi:return False
    return True

def safe_position(position,boxes,clearance):
    """Reserve a standing footprint, not merely a point at eye height.
    Rugs below 8 cm are excluded; closed transparent glass remains physical.
    """
    for box in boxes:
        center,half,_,_,_=box
        if center[2]+half[2]<=.08 or center[2]-half[2]>=position[2]+.15:continue
        x,y,_=local(position,box)
        if math.hypot(max(0,abs(x)-half[0]),max(0,abs(y)-half[1]))<clearance:return False
    return True

def target_points(f):
    """Bounding corners + face centres; furniture is a semantic target proxy."""
    r=math.radians(f['rotation']);c,s=math.cos(r),math.sin(r);sx,sy,sz=f['size'];x,y,z=f['position']
    def point(u,v,w):return (x+u*sx*c-v*sy*s,y+u*sx*s+v*sy*c,z+w*sz)
    corners=[point(u,v,w) for u in (-.5,.5) for v in (-.5,.5) for w in (0,1)]
    samples=corners+[point(u,v,w) for u,v,w in [(0,0,1),(-.5,0,.5),(.5,0,.5),(0,-.5,.5),(0,.5,.5)]]
    return corners,samples,point(0,0,.5)

def basis(position,target):
    forward=unit(sub(target,position));right=unit((forward[1],-forward[0],0))
    up=(right[1]*forward[2],-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0])
    return forward,right,up

def project(point,position,axes,fov,aspect,near,far):
    forward,right,up=axes;v=sub(point,position);depth=dot(v,forward)
    if not near<depth<far:return None
    half=math.tan(math.radians(fov)/2)
    return (dot(v,right)/(depth*half*aspect),dot(v,up)/(depth*half))

def _validate(config):
    if not all(math.isfinite(v) and v>0 for v in [config.eye_height,config.clearance,config.grid_step,config.aspect,config.near,config.far]):raise ValueError('Invalid camera dimensions')
    if config.near>=config.far or not 0<=config.frame_margin<.4 or not 0<config.min_visibility<=1:raise ValueError('Invalid view limits')
    if not 0<config.min_occupancy<config.max_occupancy<=1:raise ValueError('Invalid occupancy limits')
    if not 0<=config.min_quality<=1:raise ValueError('Invalid quality threshold')
    if config.max_positions<1 or config.top_k<1 or not config.vertical_fovs or any(not 20<=f<=90 for f in config.vertical_fovs):raise ValueError('Invalid search budget or FOV')

def plan_cameras(model,parts,room_id,target_ids,config=CameraConfig()):
    _validate(config)
    room=next((r for r in model['rooms'] if r['id']==room_id),None)
    if room is None:raise ValueError('Unknown camera room: '+room_id)
    furniture={f['id']:f for f in model['furniture']}
    if not target_ids or len(set(target_ids))!=len(target_ids):raise ValueError('Use nonempty, distinct target IDs')
    if any(t not in furniture for t in target_ids):raise ValueError('Unknown target furniture ID')
    targets={t:target_points(furniture[t]) for t in target_ids}
    boxes=[prepare_box(b) for b in parts]
    # Transparent glazing is physically solid but does not fully occlude sight.
    occluders={t:[b for b in boxes if b[4].get('opacity',1)>=.5 and not (b[4]['kind']=='furniture' and (b[4]['id']==t or b[4]['id'].startswith(t+':')))] for t in target_ids}
    poly=room['polygon'];xs=[p[0] for p in poly];ys=[p[1] for p in poly]
    step=max(config.grid_step,math.sqrt((max(xs)-min(xs))*(max(ys)-min(ys))/config.max_positions))
    positions=[]
    nx=max(3,math.ceil((max(xs)-min(xs))/step));ny=max(3,math.ceil((max(ys)-min(ys))/step))
    for ix in range(nx):
        for iy in range(ny):
            xy=(min(xs)+(ix+.5)*(max(xs)-min(xs))/nx,min(ys)+(iy+.5)*(max(ys)-min(ys))/ny)
            if inside(xy,poly) and inside(xy,model['outline']):positions.append((*xy,config.eye_height))
    if len(positions)>config.max_positions:positions=[positions[int(i*len(positions)/config.max_positions)] for i in range(config.max_positions)]
    stats={'sampled_positions':len(positions),'collision_rejected':0,'occlusion_rejected':0,'composition_rejected':0,'feasible_views':0}
    options=[]
    for position in positions:
        if not safe_position(position,boxes,config.clearance):stats['collision_rejected']+=1;continue
        visible={t:[not any(intersects_segment(position,p,b) for b in occluders[t]) for p in points[1]] for t,points in targets.items()}
        visibility={t:sum(v)/len(v) for t,v in visible.items()}
        if min(visibility.values())<config.min_visibility:stats['occlusion_rejected']+=1;continue
        centers=[p[2] for p in targets.values()]
        aims=[tuple(sum(p[i] for p in centers)/len(centers) for i in range(3))]
        if len(centers)==2:aims += [tuple(centers[0][i]*w+centers[1][i]*(1-w) for i in range(3)) for w in (.35,.65)]
        for aim in aims:
            for gaze_height in (.9,1.2):
                target=(aim[0],aim[1],gaze_height);axes=basis(position,target);pitch=math.degrees(math.asin(axes[0][2]))
                if not -18<=pitch<=5:continue
                for fov in config.vertical_fovs:
                    rectangles=[];ok=True
                    for ident,points in targets.items():
                        screen=[project(p,position,axes,fov,config.aspect,config.near,config.far) for p in points[0]]
                        if any(p is None or max(abs(p[0]),abs(p[1]))>1-2*config.frame_margin for p in screen):ok=False;break
                        rectangles.append((min(p[0] for p in screen),min(p[1] for p in screen),max(p[0] for p in screen),max(p[1] for p in screen)))
                    if not ok:stats['composition_rejected']+=1;continue
                    left=min(r[0] for r in rectangles);bottom=min(r[1] for r in rectangles);right=max(r[2] for r in rectangles);top=max(r[3] for r in rectangles)
                    occupancy=(right-left)*(top-bottom)/4
                    if not config.min_occupancy<=occupancy<=config.max_occupancy:stats['composition_rejected']+=1;continue
                    areas=[(r[2]-r[0])*(r[3]-r[1])/4 for r in rectangles]
                    # Each requested target must remain large enough to read.
                    if min(areas)<.012:stats['composition_rejected']+=1;continue
                    framing=max(0,1-abs(occupancy-.28)/.28)
                    centre=max(0,1-abs((left+right)/2)-abs((bottom+top)/2+.15)*.5)
                    balance=min(areas)/max(areas)
                    front_scores=[]
                    for ident in target_ids:
                        f=furniture[ident];back=next((c for c in f.get('components',[]) if c.get('name') in ('shell_back','back')),None)
                        if back:
                            r=math.radians(f['rotation']);x,y=back['center'][:2];front=unit((-x*math.cos(r)+y*math.sin(r),-x*math.sin(r)-y*math.cos(r),0));v=sub(position,targets[ident][2]);front_scores.append((dot(front,unit((v[0],v[1],0)))+1)/2)
                    front=sum(front_scores)/len(front_scores) if front_scores else .5
                    score=.30*min(visibility.values())+.22*framing+.18*centre+.10*balance+.12*front+.08*(1-(fov-50)/40)
                    stats['feasible_views']+=1
                    options.append({'position':list(position),'target':list(target),'up':[0,0,1],'vertical_fov':fov,'aspect':config.aspect,'near':config.near,'far':config.far,'pitch_degrees':pitch,'yaw_degrees':math.degrees(math.atan2(axes[0][1],axes[0][0])),'roll_degrees':0,'score':round(score,5),'metrics':{'sampled_visibility':visibility,'occupancy':round(occupancy,4),'target_screen_areas':dict(zip(target_ids,areas)),'front_preference':round(front,4)},'cutaway':False})
    selected=[]
    for option in sorted(options,key=lambda o:-o['score']):
        if any(math.dist(option['position'],p['position'])<.8 for p in selected):continue
        option['id']='auto_'+str(len(selected)+1);selected.append(option)
        if len(selected)>=config.top_k:break
    snapshot={k:model[k] for k in ('walls','openings','furniture','outline')}
    return {'schema_version':1,'status':('ok' if selected[0]['score']>=config.min_quality else 'requires_review') if selected else 'no_feasible_view','room_id':room_id,'target_ids':target_ids,'model_revision':model['revision'],'scene_snapshot':snapshot,'scene_sha256':hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest(),'config':asdict(config),'search_stats':stats,'cameras':selected,'limitations':['Discrete search; failure is not proof that no camera exists','Visibility uses sparse rays and furniture bounds, not rendered pixels','Geometric composition score is a heuristic, not a guarantee of beauty','A standing footprint is checked, but walkable path/reachability is not checked','Transparent glass is assumed see-through; no reflection/transmission evaluation']}
