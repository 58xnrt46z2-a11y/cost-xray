# Cost-Xray (成本透视)

像 X 光一样穿透价格标签，看清每一分钱被谁赚走了。

输入任意商品/服务的名称和价格，Cost-Xray 自动搜索供应链数据、财报、拆机报告，生成一份 McKinsey 风格的 HTML 分析报告——包含成本全景表、图表（条形图+堆叠条图）、逐项深度解读、竞品对比、以及"值不值"的明确判断。

## 安装

```bash
# 克隆到 Claude Code 全局 skills 目录
git clone https://github.com/YOUR_USERNAME/cost-xray.git ~/.claude/skills/cost-xray
```

也可放在任意项目的 `.claude/skills/` 目录下作为项目级 skill。

## 依赖

- **Python 3.6+**，需安装以下包：
  ```bash
  pip install matplotlib fpdf2
  ```
- **AnySearch skill**（推荐，用于批量并行搜索 + 全文提取）：
  ```bash
  git clone https://github.com/anysearch-ai/anysearch-skill.git ~/.claude/skills/anysearch
  ```
  可选：在 AnySearch 目录下配置 `.env` 文件填写 API Key 以提高搜索限额。无 Key 也可匿名使用。

Cost-Xray 在 AnySearch 不可用时会自动回退到内置 WebSearch。

## 用法

在 Claude Code 中直接说：

```
帮我透视一下 iPhone 17 Pro，¥8999
拆解 LV Speedy 30 的成本结构，¥15500
这瓶 La Mer 面霜 ¥3200，值不值？
小米 YU7 标准版 ¥253,500，成本多少？
```

触发词包括：`成本拆解` `价格解剖` `钱花在哪了` `值不值` `溢价拆解` `智商税` `拆成本` `透视成本` 等。

## 支持的品类

- 消费电子（手机、耳机、电脑等）
- 奢侈品/时尚（包袋、服装、配饰等）
- 化妆品/护肤品
- 餐饮/食品饮料
- 软件/SaaS
- 教育/培训服务
- 医疗美容服务
- 家居/家具
- 新能源汽车（通过自定义维度支持）

## 输出示例

![成本拆解条图](examples/dji-mic-mini2-output.md)

三份完整报告示例：
- 消费电子：[大疆 DJI Mic Mini ¥350](examples/dji-mic-mini2-output.md)
- 奢侈品：[LV Speedy 30 ¥15,500](#)
- 新能源汽车：[小米 YU7 ¥253,500](#)

报告为单文件自包含 HTML（内联 CSS + base64 图表），可直接在浏览器中打开，也可嵌入文章。

## 文件结构

```
cost-xray/
├── SKILL.md                    # Skill 定义（8 步分析流程）
├── README.md                   # 本文件
├── references/
│   ├── industry-baselines.md   # 8 大品类成本基线数据库
│   ├── analysis-framework.md   # 分品类深度分析框架
│   └── report-template.md      # 报告模板
├── scripts/
│   ├── cost_calculator.py      # 成本估算计算引擎
│   ├── generate_charts.py      # McKinsey 风格图表生成器
│   ├── generate_html_report.py # HTML 报告生成器
│   ├── generate_md_report.py   # Markdown 报告生成器（备用）
│   └── md_to_pdf.py            # Markdown→PDF 转换器（备用）
└── examples/
    └── dji-mic-mini2-output.md # 验收用例
```

## 数据来源与可信度

Cost-Xray 严格标注每条数据的来源和可信度（●1-5）：

- ●●●●● = 官方财报/拆机报告等硬数据
- ●●●●  = 可信第三方数据（行业研报、权威媒体分析）
- ●●●   = 行业通用区间
- ●●    = 仅行业经验估算
- ●     = 纯推测

## 许可

MIT License
