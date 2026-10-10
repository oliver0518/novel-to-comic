# Tools · 可复用工具集

novel-to-comic 的所有可复用脚本都在这里。它们从真实连载工程（半年实战）中提炼出来，每个文件都自带文档字符串。

---

## bubble_lib.py · 气泡绘制公共库（方案A）

**定位**：纯函数库——不含任何集目录、底图路径，也永不写成品文件。

### 核心函数

| 函数 | 用途 |
|------|------|
| `bubble(d, cx, cy, bw, bh, lines, size, tail)` | 对白泡：手绘圆泡 + 小尾巴指向说话人 |
| `mental_bubble(d, ...)` | 心里话泡：云状边 |
| `burst_bubble(d, ...)` | 厉声呐喊：粗黑锯齿爆框 |
| `shaky_bubble(d, ...)` | 吃惊/发颤：双层不规则轮廓 |
| `whisper_bubble(d, ...)` | 小声/远处：细线小泡 |
| `narration(d, x, y, lines, size, vertical, style)` | 旁白·解说·时间跳跃：米白底黑框（支持竖排、`box`/`tag`/`rough` 三种风格）|
| `loc_box(d, x, y, text, size)` | 地点框：左上角，整页只放一次 |
| `float_word(d, x, y, text, size)` | 浮字·拟声·招式：金字 + 深色重描边 |
| `remove_watermark(im)` | 去右下"AI生成"水印 v3（双源混合补丁）|
| `white_gutters(im)` | 分隔条统一白条化（新规：禁黑条）|
| `shrink_band(im, y0, y1, target=48)` | 超宽分隔带收窄到标准 48px |

### 调用示例

```python
from PIL import Image, ImageDraw
from bubble_lib import (
    bubble, mental_bubble, narration, loc_box, float_word,
    remove_watermark, white_gutters,
)

im = Image.open("P01_xxx.png").convert("RGB")
d = ImageDraw.Draw(im)

# 1. 去水印
remove_watermark(im)

# 2. 叠地点框（页左上角）
loc_box(d, 80, 80, "神手谷·药庐", size=34)

# 3. 叠对白泡（中心，气泡大小 600×150，文字 size=36，尾巴指向左下说话人）
bubble(d, 540, 300, 600, 150, ["接下来", "看我来"], size=36, tail=(300, 450))

# 4. 叠心里话（云状边）
mental_bubble(d, 540, 600, 500, 130, ["原来……", "还有这种灵气"], size=32, tail=(300, 750))

# 5. 叠旁白框
narration(d, 100, 100, ["次日清晨"], size=28, style="box")

# 6. 叠浮字（拟声词）
float_word(d, 500, 1500, "火弹！", size=92)

# 7. 统一白条化
white_gutters(im)

im.save("成品.png")
```

### 样式样张

```bash
python3 bubble_lib.py
# 生成 tools/_bubble_samples/ 下的 9 张单样式图
# 生成 tools/_bubble_samples_overview.png 总览
```

---

## qa_check.py · 7 项自动质检门禁

**用途**：交付前一条命令跑完 7 项机械检查，替代人工逐页目检。

### 用法

```bash
python3 tools/qa_check.py <集目录>             # 检查 P*.png 成品
python3 tools/qa_check.py <集目录> --json      # 输出 JSON
python3 tools/qa_check.py <集目录> -v          # 附每页统计明细
```

### 退出码

- `0` = 全部通过
- `1` = 有 ERROR（必修）
- `2` = 仅 WARN（人工确认）

### 7 项检查

| # | 检查 | ERROR | WARN |
|---|------|-------|------|
| 1 | 命名与尺寸规范 | 命名不合规 / 同集尺寸不一致 | 尺寸非 9:16 |
| 2 | 黑条/空白带检查 | 黑条残留（禁黑条新规）| >120px 超宽白带 |
| 3 | 页边白边 | —— | 左右白列 / 底部白行 >6px |
| 4 | 水印残留 | —— | 右下角亮笔画像素 >120 |
| 5 | 相邻页撞图 | —— | 相关系数 >0.93 |
| 6 | 气泡体检 | 空泡 / 糊死 | —— |
| 7 | 画风离群 | —— | 同集内 >1.5σ |

---

## check_refs.py · 引用断链体检

**用途**：目录结构改过之后，文档里的路径引用极易失效；失效的挂图路径会直接导致出图用错参考图。

### 用法

```bash
python3 tools/check_refs.py                   # 扫描全仓库
python3 tools/check_refs.py <子目录>           # 只扫指定
python3 tools/check_refs.py -v                # 列出每处引用的来源与行号
python3 tools/check_refs.py --ext .py         # 只扫指定扩展名
```

### 退出码

- `0` = 全部引用有效
- `1` = 存在失效引用

### 判定规则

- 载体文件：`.md` / `.mdc` / `.py` / `.txt`（跳过 `.git`、`__pycache__`、`_分件_*` 等）
- 被检引用：形如 `某顶层目录/.../文件名.扩展名` 的仓库相对路径
- URL（http/https）先整段剔除
- 顶层目录白名单 = 仓库内实际存在的顶层目录
- 历史日志（`memory/YYYY-MM-DD.md`）跳过；前瞻引用走白名单

### 前瞻引用白名单

编辑 `tools/check_refs_forward.txt`，每行一个"仓库相对路径"——该文件确实被文档引用，但计划中、尚未创建。

---

## 已知坑位

| 坑 | 规避 |
|----|------|
| 模块级叠泡代码被 import 重跑覆盖成品 | PIL 公共库只 import 不写成品；`bubble_lib.py` 严禁模块级代码 |
| Edit 偶发"报成功但未落盘" | 每次编辑后用 Grep 复核文件实际内容 |
| Bash `grep "a\|b"` 交替模式**静默返回空** | 多模式检索一律用 Grep 工具 |
| 校验器会连你自己的记忆/文档一起查 | 写"已失效路径"当例子时别写成完整路径字面量 |
| 检查器一有失败就无法当门禁 | 给"计划中尚未创建"的引用留白名单机制 |

---

## 依赖安装

```bash
pip install -r requirements.txt
# Pillow / numpy / scipy
```

中文字体优先级：
1. `/System/Library/Fonts/STHeiti Medium.ttc`（macOS 默认）
2. `/System/Library/Fonts/PingFang.ttc`
3. `/System/Library/Fonts/Hiragino Sans GB.ttc`

跨平台可改 `bubble_lib._FONT_CANDIDATES` 加入新字体路径。