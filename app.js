import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
const $=id=>document.getElementById(id),status=t=>$('status').textContent=t;
let model=await fetch('space.json').then(r=>r.json()),parts=await fetch('geometry.json').then(r=>r.json());
const original=structuredClone(model);const storageKey='spatial-home-02-v1';try{const draft=JSON.parse(localStorage.getItem(storageKey)||'null');if(draft){model.furniture=draft.furniture;model.materials=draft.materials;}}catch{}
const host=$('viewport'),scene=new THREE.Scene();scene.background=new THREE.Color('#e5e9e1');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.prepend(renderer.domElement);
const camera=new THREE.PerspectiveCamera(65,1,.05,150);camera.up.set(0,0,1);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xffffff,0x758d7a,2.5));const sun=new THREE.DirectionalLight(0xffffff,3);sun.position.set(-3,-4,16);scene.add(sun);
const root=new THREE.Group();scene.add(root);let cut=false,selected;
function meshBox(p,s,color,r=0,radius=0,metallic=0){
 const rad=Math.min(radius,...s.map(v=>v/2));const geo=new THREE.BoxGeometry(...s,rad?8:1,rad?8:1,rad?8:1);
 if(rad){const pos=geo.attributes.position;const v=new THREE.Vector3(),q=new THREE.Vector3();for(let i=0;i<pos.count;i++){v.fromBufferAttribute(pos,i);q.set(...s.map((d,j)=>Math.max(-d/2+rad,Math.min(d/2-rad,v.getComponent(j)))));v.sub(q).normalize().multiplyScalar(rad).add(q);pos.setXYZ(i,v.x,v.y,v.z);}geo.computeVertexNormals();}
 const o=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color,roughness:metallic?.3:.9,metalness:metallic}));o.position.set(...p);o.rotation.z=r;root.add(o);return o;}

function build(){while(root.children.length){const o=root.children.pop();o.geometry?.dispose();o.material?.dispose();o.parent=null;}
 const shape=new THREE.Shape(model.outline.map(p=>new THREE.Vector2(...p)));const floor=new THREE.Mesh(new THREE.ShapeGeometry(shape),new THREE.MeshStandardMaterial({color:model.materials.floor,side:THREE.DoubleSide}));floor.position.z=-.015;root.add(floor);
 for(const b of parts.filter(b=>b.kind==='wall')){let p=[...b.position],s=[...b.size];if(cut){let lo=p[2]-s[2]/2,hi=Math.min(.65,p[2]+s[2]/2);if(lo>=hi)continue;s[2]=hi-lo;p[2]=(hi+lo)/2;}meshBox(p,s,model.materials.wall,b.rotation);}
 for(const f of model.furniture){
  const r=THREE.MathUtils.degToRad(f.rotation);
  const components=f.components||[{center:[0,0,.5],size:[1,1,1]}];
  for(const c of components){const [dx,dy,dz]=c.center.map((v,i)=>v*f.size[i]);
   const p=[f.position[0]+dx*Math.cos(r)-dy*Math.sin(r),f.position[1]+dx*Math.sin(r)+dy*Math.cos(r),f.position[2]+dz];
   const o=meshBox(p,c.size.map((v,i)=>v*f.size[i]),c.color||f.color,r,c.radius||0,c.metallic||0);o.userData.id=f.id;
  }
 }
 $('rev').textContent=`v${model.revision}`;
}
function fields(){selected=model.furniture.find(f=>f.id===$('object').value);$('x').value=selected.position[0];$('y').value=selected.position[1];$('rotation').value=selected.rotation;$('color').value=selected.color;$('depth').value=selected.size[0];$('width').value=selected.size[1];$('height').value=selected.size[2];}
for(const f of model.furniture)$('object').add(new Option(f.name,f.id));$('object').onchange=fields;fields();
for(const c of model.cameras)$('camera').add(new Option(c.name,c.id));
function setCamera(){const c=model.cameras.find(c=>c.id===$('camera').value);camera.position.set(...c.position);camera.fov=c.fov;camera.updateProjectionMatrix();controls.target.set(...c.target);controls.update();$('viewName').textContent=c.name;}
$('camera').onchange=setCamera;$('top').onclick=()=>{camera.position.set(7.1,4.1,20);controls.target.set(7.1,4.11,0);controls.update();$('viewName').textContent='俯视 · 结构核对';};
$('cut').onclick=()=>{cut=!cut;build();$('cut').textContent=cut?'恢复完整墙体':'剖切查看';};
$('apply').onclick=()=>{const x=Number($('x').value),y=Number($('y').value),r=Number($('rotation').value);if(![x,y,r].every(Number.isFinite)){status('请输入有效数值');return;}const size=['depth','width','height'].map(id=>Number($(id).value));if(!size.every(v=>Number.isFinite(v)&&v>=.1&&v<=10)){status('尺寸须介于 0.1 和 10 米之间');return;}selected.size=size;selected.position[0]=x;selected.position[1]=y;selected.rotation=r;selected.color=$('color').value;build();status('已更新预览，尚未保存。分享预览版未进行碰撞验收，请结合俯视图核对。');};
for(const [id,k] of [['wallColor','wall'],['floorColor','floor']]){$(id).value=model.materials[k];$(id).oninput=()=>{model.materials[k]=$(id).value;build();status('材质已更新预览，结构保持不变。');};}
function download(data,name,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
$('export').onclick=()=>download(JSON.stringify(model,null,2),'space-draft.json','application/json');
$('save').onclick=()=>{try{localStorage.setItem(storageKey,JSON.stringify({furniture:model.furniture,materials:model.materials}));status('已保存到当前浏览器。不会改变其他访客的方案；此分享版不做空间碰撞验收。');}catch(e){status('浏览器保存失败，请导出 JSON 备份。');}};
$('reset').onclick=()=>{model=structuredClone(original);localStorage.removeItem(storageKey);build();fields();status('已恢复发布时的布局。');};
$('share').onclick=async()=>{try{await navigator.clipboard.writeText(location.origin+location.pathname);status('页面链接已复制；分享的是初始布局，不含本机修改。');}catch{status('请复制浏览器地址栏中的链接进行分享。');}};
$('shot').onclick=()=>{renderer.render(scene,camera);const a=document.createElement('a');a.href=renderer.domElement.toDataURL('image/png');a.download=`space-v${model.revision}-preview.png`;a.click();download(JSON.stringify({revision:model.revision,draft:true,cutaway:cut,camera:{position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov},space:model},null,2),'preview-manifest.json','application/json');};
$('rooms').innerHTML=model.rooms.map(r=>`<div class="stat"><span>${r.name}</span><span>${r.label_area_m2} m²</span></div>`).join('');
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();renderer.domElement.addEventListener('dblclick',e=>{const rect=renderer.domElement.getBoundingClientRect();mouse.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(root.children).find(h=>h.object.userData.id);if(hit){$('object').value=hit.object.userData.id;fields();}});
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);
build();setCamera();status('空间已加载。双击家具可选中；原始结构处于锁定状态。');renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
window.spatialApp={get model(){return model;},scene,camera,renderer};

$('enter').onclick=()=>{
 cut=false;build();$('cut').textContent='剖切查看';$('object').value='sofa';fields();
 camera.position.set(8.4,1.0,1.6);controls.target.set(10.25,3.15,.7);camera.fov=65;camera.updateProjectionMatrix();controls.update();
 $('viewName').textContent='客厅 · 1.60 米人眼视角';status('已进入客厅并选中虚拟沙发。修改位置、宽深高与角度后，点击应用，再保存版本。拖动可围绕沙发观察。');
};
