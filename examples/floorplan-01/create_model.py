import json, pathlib, shutil
P=pathlib.Path(__file__).parent
S=10.485/(484-160)
def xy(p):return [round((p[0]-160)*S,4),round((422-p[1])*S,4)]
def poly(ps):return [xy(p) for p in ps]
m={'schema_version':1,'revision':1,'status':'draft_requires_review','units':'metres','coordinates':'right-handed: X east, Y north, Z up','source':'source.png','calibration':{'metres_per_pixel':S,'basis':'top dimension chain 2746+1564+3965+1605+1605 mm; raster span x160..484','status':'inferred_needs_verification'},'assumptions':{'ceiling_height':2.8,'external_wall_thickness':0.24,'internal_wall_thickness':0.16,'door_height':2.1,'window_sill':0.85,'window_height':1.45,'status':'all_unconfirmed'},'warnings':['这是低分辨率图片人工描摹底稿，不是测绘模型。','房间面积为原图标注，未用作模型面积验收。','厨房南侧开口形式、储B门位置及南侧窗型需核实。','家具为占位模型；原图储A无家具，保持空置。'],'outline':poly([(160,143),(296,143),(296,54),(484,54),(484,422),(355,422),(355,360),(348,360),(348,386),(240,386),(240,407),(193,407),(193,386),(160,386)]),'rooms':[],'walls':[],'openings':[],'furniture':[],'cameras':[],'materials':{'wall':'#e7e4dd','floor':'#c9b695','furniture':'#8faaa7'}}
rooms=[('bed_a','卧室 A',12.5,[(160,143),(329,143),(329,222),(160,222)]),('store_a','储 A',17.5,[(160,222),(276,222),(276,386),(160,386)]),('bed_b','卧室 B',8.5,[(276,260),(359,260),(359,360),(348,360),(348,386),(276,386)]),('bath','卫生间',3.6,[(329,140),(379,140),(379,222),(329,222)]),('store_b','储 B',2,[(299,105),(359,105),(359,146),(329,146),(329,140),(299,140)]),('kitchen','厨房',5.9,[(299,54),(429,54),(429,110),(359,110),(359,105),(299,105)]),('living','客厅',40.4,[(429,54),(484,54),(484,422),(355,422),(355,360),(359,360),(359,260),(276,260),(276,222),(379,222),(379,140),(359,140),(359,110),(429,110)])]
for id,name,area,pts in rooms:m['rooms'].append({'id':id,'name':name,'label_area_m2':area,'polygon':poly(pts),'status':'traced'})
def wall(id,a,b,ex=False,holes=[]):
 p,q=xy(a),xy(b);length=sum((q[i]-p[i])**2 for i in range(2))**.5
 m['walls'].append({'id':id,'a':p,'b':q,'thickness':.24 if ex else .16,'height':2.8,'locked':True,'status':'traced_unconfirmed'})
 for name,kind,start,end in holes:
  # scalar offset in raster pixel distance from a
  m['openings'].append({'id':name,'wall_id':id,'type':kind,'offset':round(start*S,4),'width':round((end-start)*S,4),'sill':.85 if kind=='window' else 0,'height':1.45 if kind=='window' else 2.1,'status':'inferred_unconfirmed' if 'kitchen' in name or 'store_b' in name else 'traced_unconfirmed'})
wall('north',(296,54),(484,54),True,[('entry','door',145,181)])
wall('east',(484,54),(484,422),True)
wall('south_living',(355,422),(484,422),True,[('living_window','window',5,123)])
wall('west_living',(355,360),(355,422),True)
wall('bed_b_step',(348,360),(355,360),True)
wall('bed_b_east_lower',(348,360),(348,386),True)
wall('south_b',(276,386),(348,386),True)
wall('south_store',(160,386),(276,386),True,[('store_a_window','window',33,80)])
wall('west',(160,143),(160,386),True)
wall('north_a',(160,143),(299,143),True,[('bed_a_window','window',8,69)])
wall('west_kitchen',(299,54),(299,143),True)
wall('kitchen_east',(429,54),(429,110))
wall('kitchen_south',(359,110),(429,110),False,[('kitchen_access','door',3,34)])
wall('store_b_north',(299,105),(359,105),False,[('store_b_access','door',8,33)])
wall('store_b_east',(359,105),(359,140))
wall('store_b_south',(299,143),(329,143))
wall('bath_north',(329,140),(379,140))
wall('bath_west',(329,140),(329,222))
wall('bath_east',(379,140),(379,222))
wall('bath_south',(329,222),(379,222),False,[('bath_door','door',20,44)])
wall('bed_a_south',(160,222),(329,222),False,[('store_a_door','door',90,116),('bed_a_door','door',136,165)])
wall('store_a_east',(276,222),(276,386))
wall('bed_b_north',(276,260),(359,260),False,[('bed_b_door','door',7,34)])
wall('bed_b_east',(359,260),(359,360))
for id,name,p,size,rot,room in [('bed_a','卧室 A · 床',(208,185),(1.65,2,.52),0,'bed_a'),('bed_b','卧室 B · 床',(329,300),(1.35,1.95,.52),0,'bed_b'),('sofa','客厅 · 沙发',(465,286),(.85,2.5,.8),0,'living'),('table','客厅 · 茶几',(428,286),(.72,1.2,.42),0,'living'),('cabinet','厨房 · 操作台',(358,67),(3.3,.65,.9),0,'kitchen')]:
 m['furniture'].append({'id':id,'name':name,'position':xy(p)+[0],'size':list(size),'rotation':rot,'room_id':room,'status':'design_placeholder','color':'#8faaa7'})
for id,name,p,t in [('overview','整体鸟瞰',[-7,-9,15],[5,6,0]),('living_1','客厅 · 南向北',[7,1.2,1.6],[9,8,1.4]),('living_2','客厅 · 北向南',[9,9.7,1.6],[8,3,1.4]),('bedroom','卧室 A',[4.8,6.8,1.6],[1.4,7.5,1])]:m['cameras'].append({'id':id,'name':name,'position':p,'target':t,'fov':65})
(P/'space.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
# source.png is supplied next to this script.
