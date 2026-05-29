# 🩻 Cost-Xray（成本透视）

*像 X 光一样穿透价格标签，看清每一分钱被谁赚走了。*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Claude%20Code-8B5CF6)](https://claude.ai/code)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)

---

## 这是什么

你花 ¥15,500 买了一只 LV Speedy 30，但它的物料成本只有 ¥628。剩下的钱去哪了？

Cost-Xray 是一个 Claude Code 全局 skill。给它**产品名 + 价格**，它会自动搜索供应链数据、企业财报、拆机报告和行业研报，拆解出 10+ 个成本维度，生成一份 McKinsey 风格的 HTML 报告——**把品牌方不愿意告诉你的定价黑箱，摆到桌面上**。

每份报告包含：

- 📊 **成本全景表**：每个维度的金额、占比、数据来源和可信度
- 📈 **可视化图表**：横向条图 + 100% 堆叠条图（扁平、无 3D、无渐变）
- 🔍 **逐项深度解读**：每一分钱给了谁，为什么给这么多
- 🆚 **竞品对比**：同价位产品横向比较
- ⚖️ **"值不值"判定**：给明确结论，不模棱两可

<p align="center"><em>报告示例预览（单文件 HTML，浏览器直接打开）</em></p>

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/58xnrt46z2-a11y/cost-xray.git ~/.claude/skills/cost-xray
```

### 2. 安装 Python 依赖

```bash
pip install matplotlib fpdf2
```

### 3. （推荐）安装 AnySearch

Cost-Xray 优先使用 AnySearch 做批量并行搜索和全文提取。不装也能用，会自动回退到内置搜索。

```bash
git clone https://github.com/anysearch-ai/anysearch-skill.git ~/.claude/skills/anysearch
```

> AnySearch 不配 API Key 也能匿名使用，只是速率限制较低。去 [anysearch.com](https://anysearch.com/console/api-keys) 免费注册获取 Key，写入 `~/.claude/skills/anysearch/.env` 即可。

### 4. 开始使用

重启 Claude Code，然后直接说：

```
帮我透视一下 iPhone 17 Pro，¥8999
LV Speedy 30 ¥15,500 钱花在哪了
小米 YU7 标准版 ¥253,500 拆成本
这瓶面霜 ¥3200 值不值
```

> **触发词**：`成本拆解` `价格解剖` `钱花在哪了` `值不值` `溢价拆解` `智商税` `拆成本` `透视成本` `为什么这么贵` `成本结构`

---

## 工作流程

```
你说 "透视 iPhone 17 Pro ¥8999"
    ↓
① 输入解析 → 识别品类：消费电子
    ↓
② 基线匹配 → 加载消费电子成本区间（BOM 20-35%、渠道 20-35%...）
    ↓
③ 并行搜索 → AnySearch 同时搜：拆机报告 + 苹果财报 + 供应链信息
    ↓
④ 初步估算 → 硬数据锚定 + 基线填补，生成成本拆解 JSON
    ↓
⑤ 深度模式 → 6-8 路平行搜索 + 关键页面全文提取
    ↓
⑥ 竞品对比 → 三星/华为旗舰横向对比
    ↓
⑦ 生成报告 → 单文件 HTML（内联 CSS + base64 图表）
    ↓
⑧ 输出文件 → 浏览器打开即可查看
```

---

## 支持的品类

所有品类都有内置的行业成本基线数据库，搜索到的硬数据会动态修正基线值。

| 品类 | 示例产品 |
|------|---------|
| 💻 消费电子 | 手机、耳机、电脑、相机、麦克风 |
| 👜 奢侈品/时尚 | 包袋、服装、鞋履、配饰 |
| 💄 化妆品/护肤品 | 面霜、精华、口红、香水 |
| 🍔 餐饮/食品饮料 | 餐厅菜品、外卖、包装食品 |
| 💾 软件/SaaS | 订阅服务、App、云服务 |
| 📚 教育/培训 | 线上课程、培训班、私教 |
| 💉 医疗美容 | 热玛吉、水光针、牙齿矫正 |
| 🛋️ 家居/家具 | 沙发、床垫、定制柜 |
| 🚗 新能源汽车 | 纯电、混动、增程 |

---

## 数据可信度

每条成本数据都标注了来源和可信度，宁写"暂无公开数据"也不编造数字。

| 星级 | 含义 | 典型来源 |
|------|------|---------|
| ●●●●● | 官方硬数据 | 上市公司财报、品牌官方成本披露 |
| ●●●● | 可信第三方 | iFixit 拆机 BOM 清单、知名券商研报 |
| ●●● | 行业经验区间 | 行业白皮书、从业者访谈 |
| ●● | 基线估算 | 品类通用成本结构 |



## 许可

MIT License — 随便用，提个 Issue 或 PR 更好。
