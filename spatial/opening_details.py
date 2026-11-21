"""Detail existing openings only. Metres; leaves closed; assumed profiles."""
import math

def opening_parts(model):
    result=[]
    walls={w['id']:w for w in model['walls']}
    for h in model['openings']:
        settings=h.get('details',{});style=settings.get('style','auto')
        if style=='none':continue
        if style=='auto':style='sliding' if h.get('type')=='window' or h['sill']>0 or h['width']>1.6 else 'hinged'
        if style not in ('sliding','hinged','glass_door'):raise ValueError('Unknown opening detail style: '+style)
        if h['width']<.3 or h['height']<.4:raise ValueError('Opening too small for standard profiles: '+h['id'])
        w=walls[h['wall_id']];a=w['a'];r=math.atan2(w['b'][1]-a[1],w['b'][0]-a[0]);W=h['width'];H=h['height'];z=h['sill'];F=.045
        def part(name,x,y,v,s,color='#716b60',opacity=1):
            u=h['offset']+x
            result.append(dict(id=h['id']+':'+name,opening_id=h['id'],kind='opening_detail',position=[a[0]+u*math.cos(r)-y*math.sin(r),a[1]+u*math.sin(r)+y*math.cos(r),z+v],size=s,rotation=r,color=color,opacity=opacity,component=name))
        for x,n in [(F/2,'frame_left'),(W-F/2,'frame_right')]:part(n,x,0,H/2,[F,w['thickness']+.02,H])
        part('frame_head',W/2,0,H-F/2,[W-2*F,w['thickness']+.02,F])
        sliding=style=='sliding'
        if sliding:
            part('frame_sill',W/2,0,F/2,[W-2*F,w['thickness']+.02,F])
            for lane in [-.025,.025]:
                for v,n in [(F+.005,'bottom'),(H-F-.005,'top')]:part(f'track_{n}_{lane}',W/2,lane,v,[W-2*F,.012,.01],'#a1a4a0')
            sash_width=(W-2*F)/2;sh=H-2*F-.02;sf=.028
            for i in range(2):
                x=F+sash_width*(i+.5);y=(-.025 if i==0 else .025)
                for dx,n in [(-sash_width/2+sf/2,'left'),(sash_width/2-sf/2,'right')]:part(f'sash_{i}_{n}',x+dx,y,H/2,[sf,.035,sh])
                for v,n in [(H/2-sh/2+sf/2,'bottom'),(H/2+sh/2-sf/2,'top')]:part(f'sash_{i}_{n}',x,y,v,[sash_width-2*sf,.035,sf])
                part(f'glass_{i}',x,y,H/2,[sash_width-2*sf,.006,sh-2*sf],'#bddce4',.22)
                if h['sill']==0:part(f'handle_{i}',x+(-1 if i else 1)*(sash_width/2-.055),y+.04,1.05,[.018,.035,.20],'#4c4e4b')
        else:
            # Flush closed leaf fits between the existing jambs; no speculative swing.
            sw=W-2*F-.008;sh=H-F-.015
            glass=style=='glass_door'
            if glass:
                sf=.035
                for x,n in [(W/2-sw/2+sf/2,'left'),(W/2+sw/2-sf/2,'right')]:part('leaf_'+n,x,0,.01+sh/2,[sf,.04,sh])
                for v,n in [(.01+sf/2,'bottom'),(.01+sh-sf/2,'top')]:part('leaf_'+n,W/2,0,v,[sw-2*sf,.04,sf])
                part('leaf_glass',W/2,0,.01+sh/2,[sw-2*sf,.008,sh-2*sf],'#bddce4',.22)
            else:part('leaf',W/2,0,.01+sh/2,[sw,.04,sh],'#c8b59a')
            handle_z=min(1.02,H*.5)
            for side in [-1,1]:
                part('handle_plate_'+str(side),W-F-.09,side*.027,handle_z,[.035,.012,.17],'#5b5d58')
                part('handle_'+str(side),W-F-.135,side*.05,handle_z+.02,[.12,.022,.022],'#5b5d58')
            for v in [H*.12,H*.86]:part('hinge_'+str(v),F+.008,-.027,v,[.018,.018,.09],'#9b9e96')
    return result
