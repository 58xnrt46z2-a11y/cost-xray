# Cost-Xray（成本透视）

像 X 光一样穿透价格标签，看清一件商品的钱到底花去了哪里。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex-8B5CF6)](#安装)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)

Cost-Xray 是一个给 Claude Code / Codex 使用的 AI skill。输入**产品名 + 价格**，它会搜索供应链数据、企业财报、拆机报告、行业研报和竞品信息，拆解商品或服务的成本结构，并给出「值不值」判断。

适合用来分析：

- 消费电子：手机、耳机、电脑、相机、麦克风
- 奢侈品/时尚：包袋、服装、鞋履、配饰
- 化妆品/护肤品：面霜、精华、口红、香水
- 餐饮/食品饮料：餐厅菜品、外卖、包装食品
- 软件/SaaS、教育培训、医美、家居、新能源汽车等

## 它能输出什么

一次完整分析会尽量包含：

- **成本全景表**：物料、制造、研发、营销、渠道、税费、品牌溢价、售后、净利等维度
- **可信度标注**：每条数字标注来源和可信度，找不到硬数据时明确写「行业经验估算」
- **利润流向解读**：说明谁赚走了这笔钱，为什么能赚这么多
- **竞品对比**：同价位、同品牌上下级或品类标杆的横向比较
- **值不值判断**：值回票价 / 合理 / 偏贵 / 纯智商税
- **可发布文本**：适合小红书、公众号、商业观察文章的 500-800 字版本
- **HTML 报告**：深度模式可生成单文件 HTML 报告，浏览器直接打开
- **证据账本**：区分官方数据、第三方数据、行业估算和必要假设
- **自动 QA**：检查金额合计、百分比、来源标签、可信度和证据覆盖

示例输入：

```text
帮我透视一下 iPhone 17 Pro，¥8999
LV Speedy 30 ¥15,500 钱花在哪了
小米 YU7 标准版 ¥253,500 拆成本
这瓶面霜 ¥3200 值不值
```

触发词包括：`成本拆解`、`价格解剖`、`钱花在哪了`、`值不值`、`溢价拆解`、`智商税`、`拆成本`、`透视成本`、`为什么这么贵`、`成本结构`。

## 安装

### Codex

```bash
git clone https://github.com/58xnrt46z2-a11y/cost-xray.git ~/.codex/skills/cost-xray
```

然后重启 Codex。

### Claude Code

```bash
git clone https://github.com/58xnrt46z2-a11y/cost-xray.git ~/.claude/skills/cost-xray
```

然后重启 Claude Code。

### Python 依赖

如果你需要生成图表、HTML 报告或 PDF，请安装：

```bash
pip install matplotlib fpdf2
```

### 推荐：安装 AnySearch

Cost-Xray 可以使用内置搜索工具；如果你的环境里装了 AnySearch，它会优先用批量搜索和全文提取，提高深度分析速度。

```bash
git clone https://github.com/anysearch-ai/anysearch-skill.git ~/.codex/skills/anysearch
```

Claude Code 用户可以把路径换成：

```bash
git clone https://github.com/anysearch-ai/anysearch-skill.git ~/.claude/skills/anysearch
```

## 快速模式和深度模式

Cost-Xray 有两档深度：

| 模式 | 适合场景 | 输出 |
| --- | --- | --- |
| 快速判断 | 购物前想快速知道值不值 | 成本大头、品牌毛利估算、明确判断、替代方案 |
| 深度拆解 | 写文章、做研究、做竞品分析 | 多轮搜索、竞品对比、成本表、HTML 报告、自媒体文案 |

快速模式示例输出结构：

```markdown
## 快速成本判断：DJI Mic Mini 2 ¥350

**成本大头**：物料、研发摊销、渠道加价。
**品牌方赚多少**：结合公开毛利和行业基线估算。
**值不值？** 值回票价。
**更划算的替代**：列出 1-2 个替代方案。
```

深度模式会尽量生成更完整的成本 JSON，并调用 `scripts/generate_html_report.py` 生成单文件 HTML。

## 工作流程

```text
用户输入：透视 iPhone 17 Pro ¥8999
  ↓
解析产品、品牌、型号、价格、疑问
  ↓
识别品类并加载 references/industry-baselines.md
  ↓
搜索拆机/BOM、财报、供应链、渠道、竞品
  ↓
用硬数据锚定成本，用行业基线填补缺口
  ↓
生成成本拆解、可信度标注和「值不值」判断
  ↓
深度模式输出 HTML 报告和社交媒体文案
```

深度模式会把研究过程落到一组可追踪的文件中：

```text
cost-xray-<product-slug>/
  data/input.json
  data/cost_data.json
  evidence/evidence-ledger.md
  evidence/sources.md
  output/report.md
  output/report.html
  output/social-copy.md
  output/validation.json
```

完整流程会先建立证据账本，再生成报告，最后运行自动验证。验证中的 `FAIL` 必须修复；无法消除的 `WARN` 必须在交付时披露。

## 支持的品类

所有品类都有内置的行业成本基线数据库，搜索到的硬数据会动态修正基线值。

| 品类 | 示例产品 |
| --- | --- |
| 消费电子 | 手机、耳机、电脑、相机、麦克风 |
| 奢侈品/时尚 | 包袋、服装、鞋履、配饰 |
| 化妆品/护肤品 | 面霜、精华、口红、香水 |
| 餐饮/食品饮料 | 餐厅菜品、外卖、包装食品 |
| 软件/SaaS | 订阅服务、App、云服务 |
| 教育/培训 | 线上课程、培训班、私教 |
| 医疗美容 | 热玛吉、水光针、牙齿矫正 |
| 家居/家具 | 沙发、床垫、定制柜 |
| 新能源汽车 | 纯电、混动、增程 |


## 数据可信度

Cost-Xray 的原则是：宁可写「暂无公开数据」，也不编造数字。

| 可信度 | 含义 | 典型来源 |
| --- | --- | --- |
| 5/5 | 官方硬数据 | 上市公司财报、品牌官方披露 |
| 4/5 | 可信第三方 | iFixit 拆机、知名券商研报、供应链报告 |
| 3/5 | 行业经验区间 | 行业白皮书、从业者访谈、公开报价 |
| 2/5 | 基线估算 | 品类通用成本结构 |
| 1/5 | 弱估算 | 数据不足时的保守推断 |

## 仓库结构

```text
SKILL.md                         Skill 入口和工作流说明
README.md                        项目介绍、安装和使用说明
examples/                        示例输入和预期输出
references/industry-baselines.md 行业成本基线数据库
references/analysis-framework.md 品类分析框架
references/report-template.md    深度报告结构
references/category-playbook.md  分品类拆解路径
references/evidence-rules.md     证据分级与引用规则
references/production-workflow.md 深度报告生产流程
references/qa-checklist.md       交付前检查清单
scripts/cost_calculator.py       成本估算辅助脚本
scripts/generate_html_report.py  HTML 报告生成器
scripts/generate_md_report.py    Markdown 报告生成器
scripts/md_to_pdf.py             PDF 转换辅助脚本
scripts/evidence_ledger.py       证据账本生成器
scripts/validate_cost_report.py  数据与证据覆盖验证器
```

## 本地生成报告

如果你已经有成本数据 JSON，可以直接生成 HTML：

```bash
python scripts/generate_html_report.py cost_data.json output.html
```

或生成 Markdown：

```bash
python scripts/generate_md_report.py cost_data.json output.md
```

生成证据账本并运行验证：

```bash
python scripts/evidence_ledger.py cost_data.json evidence-ledger.md
python scripts/validate_cost_report.py cost_data.json evidence-ledger.md validation.json
```

## 示例

仓库里有一个验收案例：

- [`examples/dji-mic-mini2-output.md`](examples/dji-mic-mini2-output.md)

它展示了一个 350 元无线麦克风应该如何识别品类、搜索数据、拆分成本，并给出「值不值」判断。

## 适合谁

- 想判断一个产品是不是贵得合理的消费者
- 写小红书、公众号、商业观察内容的创作者
- 做竞品研究、价格分析、用户洞察的产品/运营/研究人员
- 想把「品牌溢价」讲清楚的商业分析爱好者

## 免责声明

Cost-Xray 会优先使用公开资料和可验证来源。很多商品的真实成本并不公开，因此报告中的部分数字可能是基于行业基线和公开线索的估算，不构成投资、消费或商业决策建议。

## License

MIT License. See [LICENSE](LICENSE).
