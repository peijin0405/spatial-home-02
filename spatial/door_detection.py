"""Geometric swing-door proposals, not a universal floorplan recognizer.

Pixels use x-right/y-down. Scores are geometric evidence, not calibrated
probabilities. Never mutate walls or automatically approve an opening.
"""
from dataclasses import dataclass
import math
import cv2
import numpy as np
from spatial.door_audit import wall_fit

@dataclass(frozen=True)
class Config:
    min_radius: float = 32  # input-image pixels
    max_radius: float = 260
    max_dimension: int = 1600
    sweeps: tuple = (90,)
    min_score: float = .64
    max_lines: int = 1200
    ignore_colored_annotations: bool = False


def detect_swing_doors(image, config=Config()):
    if image is None or image.size == 0:
        raise ValueError('Empty image')
    if not 0 < config.min_radius < config.max_radius or config.max_dimension < 64:
        raise ValueError('Invalid radius or image-size limits')
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY) if image.ndim==3 else image.copy()
    if config.ignore_colored_annotations and image.ndim==3:
        colorful=image.max(axis=2).astype(float)-image.min(axis=2).astype(float)>50
        gray[colorful]=255
    scale=min(1.,config.max_dimension/max(gray.shape))
    gray=cv2.resize(gray,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    # Otsu avoids turning JPEG noise and pale backgrounds into dense edges.
    _,ink=cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    distance=cv2.distanceTransform(255-ink,cv2.DIST_L2,5)
    thickness=cv2.distanceTransform(ink,cv2.DIST_L2,5)
    wall_distance=cv2.distanceTransform(np.where(thickness>=2.8,0,255).astype('uint8'),cv2.DIST_L2,5)
    lo=max(8,config.min_radius*scale);hi=config.max_radius*scale
    edges=cv2.Canny(gray,60,160)
    lines=cv2.HoughLinesP(edges,1,np.pi/720,threshold=max(10,int(lo*.5)),minLineLength=lo,maxLineGap=4)
    if lines is None:return []
    lines=sorted(lines.reshape(-1,4).tolist(),key=lambda p:-(p[2]-p[0])**2-(p[3]-p[1])**2)
    lines=[p for p in lines if lo<=math.hypot(p[2]-p[0],p[3]-p[1])<=hi][:config.max_lines]
    # Wall-gap seeds recover leaves merged into longer window/wall lines by Hough.
    thick=thickness>=2.8
    for transpose in (False,True):
        raster=thick.T if transpose else thick
        for row in range(0,raster.shape[0],4):
            filled=np.flatnonzero(raster[row])
            if len(filled)<2:continue
            jumps=np.flatnonzero((np.diff(filled)>=lo)&(np.diff(filled)<=hi))
            for j in jumps:
                left,right=filled[j]+3,filled[j+1]-3
                for hinge,closed in [(left,right),(right,left)]:
                    for sign in (-1,1):
                        start=[hinge,row];end=[hinge,row+sign*abs(closed-hinge)]
                        if transpose:start.reverse();end.reverse()
                        lines.append(start+end)
    def sample(points):
        xy=np.rint(points).astype(int);valid=(xy[:,0]>=0)&(xy[:,0]<gray.shape[1])&(xy[:,1]>=0)&(xy[:,1]<gray.shape[0])
        result=np.full(len(points),999.,dtype=float);result[valid]=distance[xy[valid,1],xy[valid,0]];return result
    proposals=[];seen=set()
    for x1,y1,x2,y2 in lines:
        seeds=[]
        for a,b in [((x1,y1),(x2,y2)),((x2,y2),(x1,y1))]:
            for shift in (0,.06):
                seeds.append((np.array(a)-shift*(np.array(b)-a),b))
        for start,end in seeds:
            hinge=np.array(start,dtype=float);vector=np.array(end)-hinge;base=np.linalg.norm(vector);angle=math.atan2(vector[1],vector[0])
            leaf_samples=hinge+vector*np.linspace(.12,.90,24)[:,None]
            if np.mean(sample(leaf_samples)<=2.8)<.7:continue
            key=(*np.rint(hinge/3).astype(int),round(angle/.05),round(base/4))
            if key in seen:continue
            seen.add(key)
            for multiplier in (.96,1.,1.04):
                radius=base*multiplier
                if radius>hi:continue
                tolerance=max(1.8,min(3.5,radius*.018))
                for sweep in config.sweeps:
                    for sign in (-1,1):
                        theta=angle+sign*np.radians(sweep)*np.linspace(.08,.92,96)
                        unit=np.column_stack((np.cos(theta),np.sin(theta)))
                        hits=sample(hinge+radius*unit)<=tolerance
                        coverage=float(hits.mean());bins=float(np.mean(hits.reshape(8,12).mean(axis=1)>=.20))
                        if coverage<.28 or bins<.75:continue
                        # A thick wall, filled furniture or a text block is not an isolated arc.
                        delta=max(6.,radius*.12)
                        side=float(np.mean(sample(hinge+(radius-delta)*unit)<=tolerance)+np.mean(sample(hinge+(radius+delta)*unit)<=tolerance))/2
                        contrast=max(0.,coverage-side)
                        if contrast<.35:continue
                        # Reject circles (table/sink) using the equally-sized opposite sector.
                        opposite=angle-sign*np.radians(sweep)*np.linspace(.08,.92,96)
                        opposite_hits=float(np.mean(sample(hinge+radius*np.column_stack((np.cos(opposite),np.sin(opposite))))<=tolerance))
                        if opposite_hits>.9:continue
                        score=.45*coverage+.3*bins+.25*min(1.,contrast/.5)
                        if score<config.min_score:continue
                        closed_angle=angle+sign*math.radians(sweep)
                        closed=hinge+radius*np.array([math.cos(closed_angle),math.sin(closed_angle)])
                        jambs=np.rint([hinge,closed]).astype(int)
                        if any(not (0<=x<gray.shape[1] and 0<=y<gray.shape[0]) or wall_distance[y,x]>max(7.,radius*.14) for x,y in jambs):continue
                        span=hinge+(closed-hinge)*np.linspace(.18,.82,12)[:,None]
                        xy=np.rint(span).astype(int)
                        if np.mean(wall_distance[xy[:,1],xy[:,0]]<2)>.2:continue
                        interior=hinge+(radius*np.linspace(.2,.8,8))[:,None,None]*unit[None,::4,:]
                        clutter=float(np.mean(sample(interior.reshape(-1,2))<=1.5))
                        if clutter>.12:continue
                        proposals.append(dict(hinge_px=(hinge/scale).round(2).tolist(),leaf_tip_px=((hinge+radius*vector/base)/scale).round(2).tolist(),closed_tip_px=(closed/scale).round(2).tolist(),radius_px=round(radius/scale,2),sweep_degrees=sign*sweep,score=round(score,3),evidence={'arc_coverage':round(coverage,3),'angular_bins':bins,'arc_contrast':round(contrast,3),'opposite_arc':round(opposite_hits,3),'sector_clutter':round(clutter,3)},status='needs_review',type='swing_door'))
    # Merge duplicate edges of the same leaf; keep spatially distinct double-door leaves.
    kept=[]
    for p in sorted(proposals,key=lambda p:-p['score']):
        if any(math.dist(p['hinge_px'],q['hinge_px'])<max(8,.20*p['radius_px']) and abs(p['radius_px']-q['radius_px'])<.2*p['radius_px'] and math.dist(p['closed_tip_px'],q['closed_tip_px'])<.25*p['radius_px'] for q in kept):continue
        p['id']=f'door_candidate_{len(kept)+1}';kept.append(p)
    return kept


def match_to_walls(candidates, model, pixel_to_world, tolerance=.15):
    """Propose wall offsets using an explicit 2x3 affine calibration in metres.
    Report existing openings without modifying them. No nearest-wall guessing
    when distance, orientation, or endpoint bounds fail.
    """
    transform=np.asarray(pixel_to_world,dtype=float)
    if transform.shape!=(2,3) or not np.isfinite(transform).all() or abs(np.linalg.det(transform[:,:2]))<1e-12:
        raise ValueError('A nonsingular finite 2x3 pixel-to-world matrix is required')
    result=[]
    for candidate in candidates:
        p=dict(candidate);points=[transform@np.array([*candidate[k],1]) for k in ('hinge_px','closed_tip_px')];matches=[]
        for wall in model['walls']:
            if not wall_fit(points[0],points[1],wall,distance_tolerance=tolerance)['matches']:continue
            a=np.array(wall['a']);v=np.array(wall['b'])-a;length=np.linalg.norm(v)
            if length==0:continue
            u=v/length;offsets=[float((q-a)@u) for q in points];distances=[abs(float((q-a)@np.array([-u[1],u[0]]))) for q in points]
            if max(distances)>tolerance or min(offsets)<0 or max(offsets)>length:continue
            width=max(offsets)-min(offsets)
            if width<.35 or width>2.:continue
            matches.append({'wall_id':wall['id'],'offset':round(min(offsets),4),'width':round(width,4),'distance_m':round(max(distances),4),'details':{'style':'hinged'}})
        matches.sort(key=lambda m:m['distance_m']);p['wall_matches']=matches
        p['status']='needs_review' if len(matches)==1 else ('ambiguous_wall' if matches else 'unmatched_wall')
        p['existing_opening_ids']=[h['id'] for h in model.get('openings',[]) if any(h['wall_id']==m['wall_id'] and min(h['offset']+h['width'],m['offset']+m['width'])>max(h['offset'],m['offset']) for m in matches)]
        result.append(p)
    return result
