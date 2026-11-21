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
