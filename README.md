# 户型图 → 三维空间基座

用 Python、Blender 和 Three.js 将户型描摹数据转成可编辑三维空间。包含两个完整示例及 GitHub Pages 交互预览。

## 在线查看（无需登录）

- [首页](https://peijin0405.github.io/spatial-home-02/)
- [示例一：原始户型与参考款沙发](https://peijin0405.github.io/spatial-home-02/demos/floorplan-01/)
- [示例二：约14.2×8.2米的新户型](https://peijin0405.github.io/spatial-home-02/demos/floorplan-02/)

## 项目结构

- `examples/floorplan-01/`：第一个户型的源码、原图、空间数据、参考沙发图片、模型与渲染图。
- `examples/floorplan-02/`：第二个户型的源码、原图、空间数据、模型与渲染图。
- `demos/`：两个示例的静态在线版本。
- 根目录网页：已发布的分享版。

## 本地编辑

```sh
git clone https://github.com/peijin0405/spatial-home-02.git
cd spatial-home-02/examples/floorplan-01
python3 server.py
```

示例一使用 http://127.0.0.1:8769，示例二使用 http://127.0.0.1:8770。运行服务时请留在对应示例目录。

本地服务器支持结构锁定、家具房间边界及墙体相交检查、版本冲突检测与历史保存。在线静态版只保存至访客浏览器，不共享修改，也不执行后端碰撞验收。

## Blender 建模与渲染

用与 bpy 5.3.0 兼容的 Python 环境（本项目验证过 Python 3.13）：

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd examples/floorplan-01
python geometry.py
python build_blender.py
python test_model.py
```

`output` 已提供 `.blend`、`.glb` 和 PNG；脚本还可重新生成深度、法线、物体索引多层 EXR。EXR 需按目标生图接口约定转换后使用，未接入生图 API。

## Agent 接口

在示例目录执行：

```sh
python agent.py inspect
python agent.py material --id wall --color '#ded7c8'
```

`move` 操作支持 `--id`、`--x`、`--y`、`--rotation`。修改已保存空间后，重新运行建模脚本才能更新 Blender 文件。`create_model.py` 是示例一最初的描摹生成记录，执行会覆盖当前数据，不用于日常编辑。

## 技术与边界

流程：人工读图/描摹 → 米制坐标 JSON → 墙体开口与家具几何 → Three.js 交互 / Blender 多机位渲染。

这不是全自动户型识别系统。原图尺寸、墙厚、层高、门窗高度及未见结构存在估算；各示例的来源与假设保存在 `space.json`。模型仅用于设计预览，不作为施工图。参考款沙发依据正面照片和外尺寸近似建模，侧背面与材料外观未经厂家确认。

`vendor` 中的 Three.js 与 OrbitControls 保留上游许可声明；示例图片为用户提供素材，不额外授予其商业使用许可。

## 门窗细化生成

`spatial/opening_details.py` 是两个户型共用的门窗细化模块。现有 `geometry.py`、本地保存接口与 Blender 建模脚本会自动调用它，根据洞口的米制坐标生成框、门扇/窗扇、轨道、玻璃、把手与合页。墙体轮廓和洞口尺寸保持原样；网页剖切会同步裁切新增部件。

每个 `openings` 条目可增加配置：

```json
{"details": {"style": "sliding"}}
```

| style | 行为 |
| --- | --- |
| `auto`（默认） | window 类型、非零窗台或宽度大于 1.6 米使用双轨推拉；其余使用平开实体门 |
| `hinged` | 实体门扇、门框、把手、合页 |
| `glass_door` | 带边框的玻璃门扇、把手、合页 |
| `sliding` | 两扇玻璃推拉门/窗、框与上下双轨 |
| `none` | 保留通道，不增加部件 |

示例二的书房开口与厨房通道显式设置为 `none`。部件属于设计预览方案：门扇默认关闭，无开合动画；窗框宽 45 mm、普通窗玻璃厚 6 mm，非产品测量数据。标准部件不支持宽小于 0.3 米或高小于 0.4 米的洞口，会报告错误；这种洞口可设为 `none`。玻璃在网页与通用 glTF 中采用透明材质，Blender 脚本另设置透射材质。

从仓库根目录重新生成：

```sh
python3 examples/floorplan-01/geometry.py
python3 examples/floorplan-02/geometry.py
python3 scripts/export_detailed_gltf.py examples/floorplan-01
python3 scripts/export_detailed_gltf.py examples/floorplan-02
cp examples/floorplan-01/geometry.json demos/floorplan-01/geometry.json
cp examples/floorplan-02/geometry.json demos/floorplan-02/geometry.json
cp examples/floorplan-02/geometry.json geometry.json
cp examples/floorplan-02/output/space-detailed.gltf output/space-detailed.gltf
```

`output/space-detailed.gltf` 自包含几何、材质及非凸地板，可导入 Blender；无需安装 Blender 即可生成。网页下载入口已改为此文件。它是生成时的快照，网页家具调整不会自动改写下载文件。已有 `.blend`、`.glb` 与旧效果图保留为历史快照；要更新 `.blend` 和渲染图，请重新执行前文 Blender 建模命令。当前修改已检查 Blender 脚本语法，尚未在 Blender 中运行验证。

验证命令：

```sh
python3 -m unittest discover -s tests -v
python3 examples/floorplan-01/test_model.py
python3 examples/floorplan-02/test_model.py
```

## 平开门符号检测（实验性、需复核）

新增 `spatial/door_detection.py`，识别“门扇直线 + 开启圆弧 + 两端墙体”的几何关系，支持实线和虚线圆弧。候选来自 Hough 门扇线段和墙体间隙；使用圆弧覆盖率、径向对比、墙端距离、洞口净空及扇形内部杂线比例过滤家具与文字。旋转的门扇可由 Hough 路径检测；墙缝补充路径限于图像水平/垂直方向。默认检测 90° 开启，可在 Python Config.sweeps 中扩展，但其他开启角度尚未验证。

该模块是通用几何基线，不是保证覆盖所有户型的训练模型。不支持从推拉门、折叠门或无圆弧的开口推断平开门；严重遮挡、透视照片、细墙线与家具侵入开启扇区可能漏检。`score` 是几何证据评分，不是概率；全部结果标记为需人工复核，不自动增删墙体或洞口。复核前不能用来断言原图的所有门均已识别。

安装独立依赖并运行（与 Blender 环境分离）：

```sh
python3 -m venv .venv-vision
.venv-vision/bin/python -m pip install -r requirements-vision.txt
.venv-vision/bin/python scripts/detect_doors.py examples/floorplan-02/source.png \
  --min-radius 50 --max-radius 140 --ignore-colored-annotations \
  --output artifacts/door-recognition/floorplan-02
.venv-vision/bin/python -m unittest discover -s tests -v
```

半径范围是原始图像的像素单位，应依据分辨率/标注比例调整，不是为某张图硬编码坐标。`--ignore-colored-annotations` 可去除蓝色尺寸线等高饱和度标注；有彩色门墙线的图请勿开启。大图内部缩至最长边 1600 像素，结果会映射回输入像素坐标。输出：

- `doors.json`：铰链点、门扇端点、推断闭合端点、半径、带符号开启角、评分、证据和复核状态。
- `doors-overlay.png`：红点为铰链，绿线为开启门扇，蓝线为推断闭合位置。图像坐标 X 向右、Y 向下，正旋转为顺时针。

可同时提供 `--space space.json --calibration calibration.json`。标定文件是明确的 2×3 像素到米制坐标仿射矩阵（两行三列 JSON 数组），满足 `[world_x,world_y] = M × [pixel_x,pixel_y,1]`。模块仅在端点靠近墙线、宽度合理、投影位于墙段内时提出 `wall_id / offset / width`，并报告重叠的现有洞口。无匹配或多墙匹配会显式报告，不强行贴到最近墙；尚未实现把人工确认结果自动写回模型。

当前验证：合成实线/虚线、旋转（含 33°）、缩放，以及空白、矩形、圆形干扰；户型图二人工标记的三处可见平开门均匹配。该单图结果不能视为跨图集准确率，落地前仍需多来源标注集、独立留出测试与误检/漏检评估。

## 生成前的门洞绑定校验

`spatial/door_audit.py` 使用纯 Python，几何生成、直接调用 `boxes()`、服务器保存、glTF 导出及 Blender 生成前都会执行校验。门的绑定方向来自 **铰链 → 闭合端点**，不能用开启门扇方向替代。

需复核的图像证据保存在门洞 `source_evidence`：

```json
{
  "source_image": "source.png",
  "hinge_px": [487, 490],
  "leaf_tip_px": [415, 490],
  "closed_tip_px": [487, 418],
  "review_status": "confirmed"
}
```

模型 `calibration.pixel_to_world` 必须提供有限、可逆的 2×3 仿射标定矩阵。校验检查来源图片、原始门扇/圆弧半径、闭合方向与墙轴夹角（≤8°）、端点距墙线（≤0.15 m）、墙段范围，以及模型洞口的偏移/宽度偏差（各≤0.10 m）。这些默认值用于当前描摹精度，不代表施工验收公差。墙段方向反转不影响平行判断。

- `blocked`：有证据但绑错墙、缺失墙段、多墙歧义、尺寸不一致、证据未确认，或模型中的检测候选未处理。抛出 `DoorBindingError`，禁止生成/导出；保留旧导出文件，另写失败报告，不能把旧文件当成本轮成功结果。
- `requires_review`：旧门洞缺少原图证据。允许生成明确标记的草稿，不宣称已通过图像一致性验证。
- `validated`：当前模型中的门洞证据及候选对账均通过。此状态只覆盖已录入的证据，不能证明原图没有漏检门。

`door_candidates` 可保存检测候选。复核后添加 `review: {"status":"accepted","opening_id":"..."}`，其三个关键点必须与对应门洞证据一致；误检需写 `review: {"status":"rejected","reason":"..."}`。未决候选、接受后未建模以及证据冲突都会阻止生成。算法不会自动删除无对应检测的旧门，也不会自动补墙或选择最近墙。

```sh
python3 scripts/audit_doors.py examples/floorplan-02/space.json
```

审计命令不改模型，退出码 0 为通过，1 为缺少证据待复核，2 为冲突。正常生成会写 `door-audit.json`，网页显示对应状态并提供报告链接，glTF 的 `extras.door_audit` 保存同一审计信息。更新静态预览时还需把示例目录的 `door-audit.json` 复制到对应 `demos`，户型二报告同时复制至根目录。

户型二西侧次卧的 `bed_a_door` 已从下方横墙移至右侧 `bed_a_entry_wall`，并和东卧室门一同保存人工核对后的图像依据。其他旧门洞尚未逐个录入图像依据，因此两个示例仍标为待复核草稿。新增测试主动制造错墙、偏移、宽度、缺墙、多墙匹配、无效标定及候选冲突，验证它们会被拒绝；还验证失败导出不会覆盖上一个文件。

## 轻量自动机位搜索

`spatial/camera_planner.py` 为纯 Python、无新增依赖的候选机位搜索。Agent 先把自然语言映射为“允许站位的房间 ID + 要展示的家具 ID”，再调用规划器；它本身不解析自然语言。客厅可以用 `sofa table` 作为主体，客餐厅组合可以用 `sofa dining` 作为主体。这是家具代理目标，不是对整个房间可见面积的测量。

流程：在房间多边形内确定性采样 → 检查站立净空 → 对每个目标发射多条遮挡射线 → 搜索注视点和 FOV → 检查主体完整入框、面积与留白 → 构图评分 → 返回最多三个位置不同的机位。使用墙体开洞后的几何、门扇和家具检测碰撞；不透明物体遮挡视线，透明玻璃遮挡行走但近似允许看穿。不会隐藏墙体、打开门或移动家具来凑画面。

默认参数：眼高 1.6 m，站立净空 0.20 m，约 0.6 m 网格且最多 180 个位置，垂直 FOV 为 50/60/70°，俯角不超过 18°，横滚为 0。每个目标的采样点可见率至少 75%，主体包围盒四周至少留画幅 8% 的边距；主体联合矩形占画幅 6%～65%，单目标面积至少 1.2%。角度和位置经过搜索，而不是强行把镜头设在房间中心。

几何构图评分（非审美概率）：30% 最弱目标可见率、22% 主体占比（偏好约28%）、18% 画面中心/留白、10% 多目标大小平衡、12% 已知沙发正面朝向、8% 较小广角偏好。默认最低评分 0.70。阈值可通过 Python `CameraConfig` 调整，应根据产品审美标注集验证。

```sh
python3 scripts/plan_camera.py examples/floorplan-01 --room living \
  --targets sofa table --output artifacts/door-recognition/auto-camera-01.json
python3 scripts/plan_camera.py examples/floorplan-02 --room living \
  --targets sofa dining --output artifacts/door-recognition/auto-camera-02.json
python3 scripts/plan_camera.py examples/floorplan-02 --room balcony \
  --targets sofa dining --output artifacts/door-recognition/auto-camera-02-balcony.json
```

结果有三个状态：`ok`（退出0）、`no_feasible_view`（退出2，没有通过硬性约束的机位）、`requires_review`（退出3，存在可用机位但构图分数不足）。后两种状态不能被调用方当作成功截图。失败只说明当前离散搜索未找到合格视角，不证明连续空间中绝对无解。样例二西侧阳台不是客厅阳台，不能为了满足描述而自动换一个房间。

所有查看器提供 `window.spatialApp.captureCameraPlan(plan, index=0, width=1600)`。它检查场景快照和计划状态，按计划画幅捕获图片，返回 PNG data URL、相机参数、视图/投影矩阵，随后恢复交互相机与剖切状态。场景中的墙、门或家具变动后必须重新计算，不能复用旧计划。示例一页面中可通过以下代码使用本地生成的文件：

```js
const plan = await fetch('/artifacts/door-recognition/auto-camera-01.json').then(r => r.json());
const shot = window.spatialApp.captureCameraPlan(plan);
const link = document.createElement('a');
link.href = shot.image;
link.download = 'auto-camera.png';
link.click();
```

算法不需要训练、外部模型服务或 GPU 搜索；GPU 只用于最后的 Three.js 截图。当前两个案例的规划耗时在本机约一秒以内（非性能承诺）。实测户型一能返回合格候选，户型二客餐厅组合分数不足而返回需复核，西侧阳台组合返回未找到可用机位。

边界：稀疏射线和家具包围盒不能替代逐像素可见性；不检查从入口走到机位的路径；不评价曝光、反射或真实材质；几何评分不能保证所有场景都美观。交付前应低分辨率渲染候选并做图像检查。当前 Agent 示例已人工检查截图，代码尚未实现渲染像素二次评分或视觉模型审美排序。
