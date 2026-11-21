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
