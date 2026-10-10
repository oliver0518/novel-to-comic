# 提示词骨架模板（v3 六段锁）

> 这是出图提示词的**统一骨架**。每次出图都按这个结构写，不要自由发挥。

---

## 六段锁结构

```
[CHARACTER LOCK]
...

[ANATOMY LOCK]
...

[PROPORTION LOCK]
...

[LAYOUT]
...

[PROP+NO-TEXT LOCK]
...

[SCENE]
...
```

---

## 完整模板

```python
prompt = f"""[CHARACTER LOCK]
<角色名>脸部最高优先级严格照搬参考图2：
脸型、眉、眼、鼻、唇全部照搬。
禁止美化、禁止换脸、禁止共用配角脸。
ENTIRE FIGURE — face, hairstyle, clothing, body proportions —
MUST exactly copy reference image 2.
禁止横过额头的丝带/头巾。

[ANATOMY LOCK]
EXACTLY TWO legs. EXACTLY TWO arms.
<双臂各自用途：right hand grips saber raised,
              left hand clutches wounded shoulder>
禁止藏手入体。禁止断肢。

[PROPORTION LOCK]
Head proportionate to body. 禁止头身错位。
<角色A> only one head taller than <角色B>.
<角色B> only one head taller than <角色C>.

[LAYOUT]
9:16 竖版漫画分格，海贼王 1189 式不规则格，
2 层为主、3 层最多。禁 4 层+密叠。
构图主体居中或偏左，避开 y240–1680 顶栏安全区。
封面构图：NO large empty black areas,
          ground extends to the bottom edge.

[PROP+NO-TEXT LOCK]
所有道具一律素面禁文字：
- <道具 1>
- <道具 2>
- <道具 3>
禁止任何文字、气泡、旁白、拟声词、印章、Logo、Watermark。

[SCENE]
<具体场景描述>
<光线：左上方自然光 / 室内烛火 / 户外月光>
<天气：晴 / 阴 / 雨 / 雪>
<色板关键词：主色 #xxxxxx, 辅色 #yyyyyy>
<氛围关键词：紧张 / 温馨 / 诡异 / 庄严>
"""
```

---

## 各段详细说明

### [CHARACTER LOCK]

**作用**：锁脸、锁身形、锁服装。

**必含**：
- "最高优先级严格照搬参考图2"
- 脸型/眉/眼/鼻/唇四项具体列出
- "禁止美化、禁止换脸"
- "ENTIRE FIGURE"
- "禁止横过额头的丝带/头巾"

**不写会出现**：
- 撞脸（配角像主角）
- 服装/身形与定妆不一致
- 额头带子（系统性缺陷）

### [ANATOMY LOCK]

**作用**：锁人体结构。

**必含**：
- "EXACTLY TWO legs. EXACTLY TWO arms."
- **双臂各自用途**（关键！只写 "no extra arm" 不够）

**不写会出现**：
- 断肢
- 藏手入体（模型会把难画的手藏进身体）
- 三脚（偶尔出现）

### [PROPORTION LOCK]

**作用**：锁人物身高比例。

**必含**：
- "Head proportionate to body"
- 人物之间的高度差（"only one head taller than X"）

**不写会出现**：
- 头身错位
- 矮个画成高个
- 配角撞脸主角（身高一致 + 服装类似 → 撞脸）

### [LAYOUT]

**作用**：锁分镜与构图。

**必含**：
- "9:16 竖版"
- "海贼王 1189 式不规则格"
- "2 层为主、3 层最多。禁 4 层+密叠"
- 安全区（避开 y240–1680）
- 封面构图纪律（NO large empty black areas）

**不写会出现**：
- 4 层+密叠（看起来不像漫画）
- 主体撞顶栏安全区
- 封面有大块黑/白空背景

### [PROP+NO-TEXT LOCK]

**作用**：锁道具 + 禁文字。

**必含**：
- 道具清单（每件都列出）
- "禁止任何文字、气泡、旁白、拟声词、印章、Logo、Watermark"

**不写会出现**：
- 道具带字（AI 经常给法器加字）
- AI 画的气泡/旁白（错字率高）
- AI 画的 Logo（永远不对）

### [SCENE]

**作用**：锁场景内容。

**必含**：
- 具体场景描述
- 光线方向
- 天气
- 色板关键词（hex 或 RGB）
- 氛围关键词

**不写会出现**：
- 色调漂移（与场景定妆不一致）
- 光影方向乱
- 氛围不达标

---

## 实战示例（C03 火弹术 P03）

```python
prompt = """[CHARACTER LOCK]
韩立脸部最高优先级严格照搬参考图2：
脸型、眉、眼、鼻、唇全部照搬。
禁止美化、禁止换脸、禁止共用配角脸。
ENTIRE FIGURE — face, hairstyle, clothing, body proportions —
MUST exactly copy reference image 2 (角色定妆照/韩立/16_韩立_四年后.png)。
禁止横过额头的丝带/头巾。

[ANATOMY LOCK]
EXACTLY TWO legs. EXACTLY TWO arms.
right hand extended forward releasing fireball,
left hand by his side.
禁止藏手入体。禁止断肢。

[PROPORTION LOCK]
Head proportionate to body. 禁止头身错位。
韩立 only one head taller than 帮众甲.

[LAYOUT]
9:16 竖版漫画分格，海贼王 1189 式不规则格，
2 层为主、3 层最多。禁 4 层+密叠。
构图主体居中（韩立中近景），避开 y240–1680 顶栏安全区。
NO large empty black areas,
ground extends to the bottom edge.

[PROP+NO-TEXT LOCK]
所有道具一律素面禁文字：
- 火弹术特效（橙红色光团）
- 砍刀（素面无铭文）
- 皮甲（素面无纹章）
禁止任何文字、气泡、旁白、拟声词、印章、Logo、Watermark。

[SCENE]
墨居·练功房，韩立单手前推推出火弹。
光线：左上方自然光，下午。
天气：晴。
色板：韩立青绿门徽袍 #5b8a72、橙红火弹 #d97f3a、墨居深棕 #3a2818。
氛围：紧张、首战。"""
```

---

## 不同题材的禁项差异

### 修真 / 玄幻

```
- 法器一律素面禁文字
- 境界特效禁画乱（不要满屏金光）
- 神兽禁画成西方龙
```

### 古风 / 武侠

```
- 现代用品禁出现
- 服饰符合朝代（不能混搭）
- 武器材质对应（铁/钢/玉）
```

### 校园 / 都市

```
- 学生发型禁画成职业人
- 校服细节准确（领带/徽章位置）
- 现代物品允许出现（手机/电脑）
```

### 奇幻 / 西幻

```
- 装备风格统一
- 种族特征不串（精灵耳朵/矮人胡子）
- 魔法体系对应（符文/法术）
```

---

## 生图工具适配

### OpenAI ImageGen / GPT-4o

```python
response = client.generate(
    prompt=prompt,
    size="1080x1920",
    quality="high",
    input_fidelity="high",
    image1=<往期成品页>,
    image2=<角色定妆照>,
)
```

### Midjourney（风格接近但锁脸差）

```python
response = client.imagine(
    prompt=prompt + " --ar 9:16 --cref <URL> --cw 100",
)
```

### Stable Diffusion（开源可控）

```python
response = pipeline(
    prompt=prompt,
    negative_prompt="...（反向提示词）",
    width=1080, height=1920,
    ip_adapter_face_id=<角色定妆照>,
)
```

---

## 已知坑位

| 坑 | 规避 |
|----|------|
| ENTIRE FIGURE 不写 → 服装跑偏 | 必含 "ENTIRE FIGURE — face, hairstyle, clothing, body proportions" |
| "no extra arm" 不够 → 藏手入体 | 写死双臂各自用途 |
| 提示词太长 → 关键句被淹没 | 六段锁结构，第一句最重要 |
| 三图同传超请求体上限 | 只挂 image1 + image2 |
| 640px 压缩图锁脸失败 | PIL 缩到 1200px 高质量 JPG 存 /tmp |
| 提示词写成"接下来" | 用具体动作/场景描述 |