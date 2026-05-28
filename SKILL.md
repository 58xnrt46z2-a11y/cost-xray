---
name: cost-xray
description: Cost-Xray 成本透视——像X光一样穿透价格标签，看清每一分钱被谁赚走了。输入产品+价格，输出McKinsey风格HTML报告（含图表+竞品对比+值不值判断）。触发词："成本拆解""价格解剖""钱花在哪了""值不值""成本分析""溢价拆解""智商税""买的啥""买入价""拆成本""价格构成""为什么这么贵""成本结构""拆解一下""透视成本"
argument-hint: [产品名称+购买价格]
---

# Cost-Xray（成本透视）

像X光一样穿透价格标签，看清每一分钱的去向。

拆解用户购买的任何商品或服务的真实成本，生成一份尖锐、有硬数据支撑的分析报告。

## 核心原则

- **硬数据优先**：每条数字必须有来源锚点（财报、拆机报告、行业研报、供应链数据），找不到的明确标注"暂无公开数据，以行业经验估算"
- **尖锐但不失准确**：直指溢价核心，但不编造数据。宁写"这部分钱品牌方不会告诉你"也不瞎填一个数字
- **透明标注可信度**：每项成本标注 ⭐1-5 可信度（⭐⭐⭐⭐⭐ = 有官方财报/拆机报告支撑；⭐ = 纯行业经验猜测）
- **默认深度分析**：每次输出 10+ 成本维度，含竞品对比和"值不值"判断

## 搜索引擎

本 skill 使用 **AnySearch** 作为优先搜索引擎（支持批量并行搜索 + 全文内容提取 + 垂直领域搜索）。

### AnySearch 配置

```bash
# CLI 命令（读取 anysearch skill 的 runtime.conf 获取实际命令）
ANYSEARCH="python <anysearch_skill_dir>/scripts/anysearch_cli.py"
```

> 实际使用时，`<anysearch_skill_dir>` 替换为 AnySearch skill 的安装路径（通常为 `~/.claude/skills/anysearch`）。

### 命令速查

```bash
# 单次搜索（可指定内容类型、时效性、结果数）
$ANYSEARCH search "查询词" --max_results 5 --freshness year --content_types web,news,academic

# 批量并行搜索（核心用法——一次调用同时搜多个方向）
$ANYSEARCH batch_search --queries '[
  {"query":"q1","max_results":5,"freshness":"year"},
  {"query":"q2","max_results":5},
  {"query":"q3","max_results":5,"content_types":"news,academic"}
]'

# 全文内容提取（用于深度阅读搜索结果中的关键页面）
$ANYSEARCH extract "https://目标网址"

# 垂直领域列表（金融/学术/医疗/代码等专项搜索）
$ANYSEARCH list_domains
```

**何时用 WebSearch vs AnySearch**：优先 AnySearch。AnySearch 不可用时回退到内置 WebSearch。

---

## 工作流程

### 第 1 步：输入解析

从用户消息中提取关键信息：
- 产品全称、品牌、型号
- 购买价格（必填，若用户未提供则追问）
- 品类（自动识别）
- 购买渠道（如有，影响渠道加价估算）
- 用户的具体疑问（如"为什么这么贵""是不是智商税"）

支持两种输入模式：
- **自由文本**："我刚花了 350 买了个大疆 Mic Mini 2 无线麦克风，帮我拆一下成本"
- **结构化**："产品：iPhone 17 Pro / 价格：8999 / 品类：手机 / 渠道：官网"

### 第 2 步：品类识别与基线匹配

识别产品所属品类，从 `references/industry-baselines.md` 加载对应品类的成本基线区间。

如果品类跨越多个分类（如"智能手表"既是消费电子又是时尚配饰），合并两个基线给出加权区间。

### 第 3 步：第一轮并行搜索（快速定位）

使用 AnySearch `batch_search` 一次性并行搜索 3-5 个方向：

```bash
$ANYSEARCH batch_search --queries '[
  {"query":"[产品名] 拆机 BOM 成本 物料清单 拆解", "max_results":5, "freshness":"year"},
  {"query":"[品牌/行业] 毛利率 净利率 财报 2024 2025", "max_results":5, "freshness":"year", "content_types":"web,news,academic"},
  {"query":"[产品名] 代工厂 供应商 出货价 渠道利润 供应链", "max_results":5, "freshness":"year"}
]'
```

对服务类产品，调整 query 为：人工成本行情、场地租金行情、行业利润率等。

**搜索结果处理**：对 batch_search 返回的高价值链接，用 `$ANYSEARCH extract "URL"` 提取全文（财务数据、拆机报告、行业分析）。提取的 Markdown 内容直接作为数据来源。

### 第 4 步：初步估算

基于搜索结果 + 行业基线，识别三档数据点：

- **硬数据**（搜索到的具体数字，如官方毛利率、拆机BOM清单）→ 直接采用，可信度 ⭐⭐⭐⭐+
- **半硬数据**（行业报告中的区间，如"消费电子渠道加价通常 20-35%"）→ 取中值，可信度 ⭐⭐⭐
- **基线估算**（仅行业经验，无搜索结果支撑）→ 用品类基线区间，可信度 ⭐⭐

调用 `scripts/cost_calculator.py`，传入价格、品类、搜索结果摘要，生成初始成本拆解 JSON。

### 第 5 步：深度模式判断

以下条件触发深度模式（使用 AnySearch 做更大规模并行搜索 + 全文提取）：
- 首轮搜索结果不足（少于 3 个硬数据点）
- 用户明确要求"深度分析"、"全面搜索"、"详细搜一下"
- 产品单价超过 1000 元且首轮数据可信度偏低

深度模式——第二轮 AnySearch `batch_search`（6-8 路并行）：

```bash
$ANYSEARCH batch_search --queries '[
  {"query":"[品牌] 代工厂 供应链 采购价 供应商关系", "max_results":5},
  {"query":"[竞品1] vs [竞品2] 拆机 成本对比 BOM", "max_results":5, "freshness":"year"},
  {"query":"[品类] [品牌] 中国 海外 价格差异 关税 定价策略", "max_results":5},
  {"query":"[产品] 历史价格 降价 涨价 走势 2023 2024 2025", "max_results":5},
  {"query":"[产品/品类] 消费者 值不值 测评 性价比 知乎 小红书", "max_results":5, "content_types":"web,news"},
  {"query":"[行业/品类] 行业研报 成本结构 利润率 券商 2024", "max_results":5, "content_types":"academic,web"},
  {"query":"[品牌] 供应商 财报 供应链 毛利率拆解", "max_results":5, "content_types":"academic,web,news"},
  {"query":"[产品] 材料 原料 物料清单 BOM teardown components", "max_results":5, "freshness":"year"}
]'
```

深度模式——对关键页面做全文提取：
```bash
$ANYSEARCH extract "https://高价值URL1"
$ANYSEARCH extract "https://高价值URL2"
```

提取的全文内容直接作为硬数据锚点使用。

### 第 6 步：竞品对比

使用 AnySearch `batch_search` 一次性搜索 2-3 款竞品的成本信息：

```bash
$ANYSEARCH batch_search --queries '[
  {"query":"[竞品1] 成本 拆机 BOM 毛利率 价格", "max_results":5},
  {"query":"[竞品2] 成本 拆机 BOM 毛利率 价格", "max_results":5},
  {"query":"[产品] vs [竞品1] vs [竞品2] 对比 性价比 评测", "max_results":5}
]'
```

提取关键竞品页面全文后，构建竞品对比表：
- 竞品价格和核心参数
- 竞品的已知成本结构（如有拆机报告）
- 单位功能/性能的"性价比"对比

### 第 7 步：生成 HTML 报告

调用 `scripts/generate_html_report.py`，输入 JSON 成本数据、逐项解读、竞品对比表、"值不值"判定、替代方案，生成单文件自包含 HTML。

报告风格（McKinsey 极简商务风）：
- 白底，低饱和蓝灰+橙色高亮，不超过 4 种颜色
- 无衬线字体，标题左对齐加粗，严格网格对齐
- 图表（横向条图 + 100% 堆叠条图）以 base64 嵌入，扁平无 3D 无渐变
- 关键数值直接标注在图表上
- 页面底部小字来源标注和免责声明

报告必须包含以下结构（参考 `references/report-template.md`）：
1. 标题 + 一句话暴击
2. 成本全景表（金额、占比、可信度评级）
3. 可视化图表（条图 + 堆叠条图）
4. 逐项深度解读（每项 150-300 字，含金额和可信度）
5. 利润流向图（等宽字体可视化）
6. 竞品对比表
7. "值不值？"判定（分"值回票价""合理""偏贵""纯智商税"四档）+ 更优替代方案
8. 脚注：品类基线说明 + 免责声明

```bash
python scripts/generate_html_report.py <cost_data.json> <output.html>
```

### 第 8 步：展示并保存报告

返回 HTML 文件路径给用户。可直接在浏览器打开查看，也可用于嵌入文章或分享。

## 语言风格规范

整份报告必须使用以下语调：

- **开场一句扎心**："你花了 ¥XXX 买这个东西，但它的物料成本可能连 ¥XX 都不到。剩下的钱去哪了？"
- **每项成本不只列数字**，要配上通俗解读："物料成本 ¥XX，占比 X%——这部分钱是给富士康/立讯精密这些代工厂的。它们赚的是辛苦钱，利润率通常只有 3-5%。"
- **高溢价项要犀利点出**："品牌溢价这一项，¥XXX，占了总价的 X%。这不是研发投入，不是物料成本，就是 DJI 这三个字母值这么多钱。你得承认，它的品牌确实值这个溢价——但这不意味着溢价全合理。"
- **对数据空缺诚实但不软弱**："制造人工的精确占比大疆没有公开披露，我们参考了歌尔股份（DJI 麦克风代工厂之一）的财报毛利率，估算在 X%-Y% 之间。"
- **"值不值"判断要有态度**：不模糊、不和稀泥，给出明确判断和理由。
- **不堆砌术语**：用"渠道加价"而不是"分销层级溢价"；用"代工厂利润"而不是"OEM 毛利留存"。

## 参考资料

- `references/industry-baselines.md` — 行业成本基线数据库，按品类组织
- `references/analysis-framework.md` — 不同品类的深度分析框架和特殊维度
- `references/report-template.md` — Markdown 报告的完整模板

## 脚本

- `scripts/cost_calculator.py` — 成本估算计算引擎，输入价格+品类+搜索结果→输出 JSON
- `scripts/generate_charts.py` — McKinsey 风图表生成器（横向条图 + 100% 堆叠条图），base64 嵌入
- `scripts/generate_html_report.py` — 主报告生成器，全量 JSON→单文件 HTML（内联 CSS + base64 图表）
- `scripts/generate_md_report.py` — （保留）Markdown 报告生成器
- `scripts/md_to_pdf.py` — （保留）Markdown→PDF

## 示例

- `examples/dji-mic-mini2-output.md` — DJI Mic Mini 2 (¥350) 的预期输出示例
