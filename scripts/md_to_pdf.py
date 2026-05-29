#!/usr/bin/env python3
"""
Markdown → PDF 报告生成器（v2）

改进：
- 段落级渲染，文字排版规整
- 自动解析成本表格，生成柱状图+饼图
- 图表嵌入 PDF 对应位置
- 表格、引用块、列表的正确排版

用法：
    python md_to_pdf.py <input.md> <output.pdf>
"""

import sys
import os
import re
import json
import tempfile
import unicodedata
from fpdf import FPDF

# 图表生成依赖
try:
    from generate_charts import generate_bar_chart, generate_pie_chart, setup_cjk as _chart_cjk
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

# ============================================================
# 字体配置
# ============================================================
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyh.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def find_cjk():
    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            return fp
    return None


def strip_emoji(text):
    """移除 PDF 字体无法渲染的 emoji 和特殊符号。
    只保留：ASCII 可打印字符、CJK 统一汉字及标点、常用拉丁扩展、全角字符、通用标点。
    """
    cleaned = []
    for ch in text:
        cp = ord(ch)
        if (
            (0x0020 <= cp <= 0x007E)  # ASCII 可打印
            or (0x00A0 <= cp <= 0x024F)  # Latin 扩展
            or (0x2000 <= cp <= 0x206F)  # 通用标点（em-dash 等）
            or (0x2100 <= cp <= 0x214F)  # 字母符号（TM 等）
            or (0x2200 <= cp <= 0x22FF)  # 数学运算符
            or (0x3000 <= cp <= 0x303F)  # CJK 标点
            or (0x3400 <= cp <= 0x4DBF)  # CJK 扩展 A
            or (0x4E00 <= cp <= 0x9FFF)  # CJK 统一汉字
            or (0xF900 <= cp <= 0xFAFF)  # CJK 兼容汉字
            or (0xFF00 <= cp <= 0xFFEF)  # 全角字符
        ):
            cleaned.append(ch)
    return "".join(cleaned)


# ============================================================
# Markdown 块解析器
# ============================================================

def parse_blocks(lines):
    """将 markdown 行列表解析为逻辑块列表。
    每个块: {"type": ..., "content": ...}
    """
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        text = line.rstrip()

        # H1
        if text.startswith("# ") and not text.startswith("## "):
            blocks.append({"type": "h1", "text": text[2:]})
            i += 1
            continue

        # H2
        if text.startswith("## "):
            blocks.append({"type": "h2", "text": text[3:]})
            i += 1
            continue

        # H3
        if text.startswith("### "):
            blocks.append({"type": "h3", "text": text[4:]})
            i += 1
            continue

        # HR
        if text.startswith("---") and len(text.strip("-")) == 0:
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Blockquote (> ...)
        if text.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].rstrip().startswith("> "):
                quote_lines.append(lines[i].rstrip()[2:])
                i += 1
            blocks.append({"type": "quote", "paragraphs": _group_paragraphs(quote_lines)})
            continue

        # Code block
        if text.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].rstrip().startswith("```"):
                code_lines.append(lines[i].rstrip())
                i += 1
            i += 1  # skip closing ```
            blocks.append({"type": "code", "lines": code_lines})
            continue

        # Table — detect header row
        if text.startswith("| ") and _is_table_header(text):
            table_lines = [text]
            i += 1
            # separator row
            if i < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[i].rstrip()):
                table_lines.append(lines[i].rstrip())
                i += 1
            # data rows
            while i < len(lines) and lines[i].rstrip().startswith("| "):
                table_lines.append(lines[i].rstrip())
                i += 1
            blocks.append({"type": "table", "lines": table_lines})
            continue

        # Unordered list
        if re.match(r"^- ", text):
            list_items = []
            while i < len(lines) and re.match(r"^- ", lines[i].rstrip()):
                list_items.append(lines[i].rstrip()[2:])
                i += 1
            blocks.append({"type": "ul", "items": list_items})
            continue

        # Bold-emphasis metadata line (italic paragraph)
        if text.startswith("*") and text.endswith("*") and not text.startswith("**"):
            blocks.append({"type": "meta", "text": text.strip("*")})
            i += 1
            continue

        # Regular paragraph — group consecutive text lines
        if text.strip():
            para_lines = []
            while i < len(lines) and lines[i].rstrip().strip() and not _is_special(lines[i].rstrip()):
                para_lines.append(lines[i].rstrip())
                i += 1
            blocks.append({"type": "para", "text": " ".join(para_lines)})
            continue

        # Blank line
        i += 1

    return blocks


def _is_special(text):
    """判断该行是否属于特殊块开头"""
    return (
        text.startswith("# ")
        or text.startswith("## ")
        or text.startswith("### ")
        or text.startswith("---")
        or text.startswith("> ")
        or text.startswith("```")
        or text.startswith("| ")
        or re.match(r"^- ", text)
        or (text.startswith("*") and text.endswith("*") and not text.startswith("**"))
    )


def _is_table_header(text):
    return "|" in text and not re.match(r"^\|[\s\-:|]+\|$", text)


def _group_paragraphs(quote_lines):
    """将连续的引用行归并为段落"""
    if not quote_lines:
        return []
    paras = []
    current = [quote_lines[0]]
    for line in quote_lines[1:]:
        if line.strip():
            current.append(line)
        else:
            if current:
                paras.append(" ".join(current))
                current = []
    if current:
        paras.append(" ".join(current))
    return paras


# ============================================================
# 表格解析
# ============================================================

def parse_table_lines(table_lines):
    """Parse a markdown table into list of rows (each row = list of cells)."""
    rows = []
    for tl in table_lines:
        # separator row
        if re.match(r"^\|[\s\-:|]+\|$", tl):
            continue
        cells = [c.strip() for c in tl.split("|")[1:-1]]
        # Strip markdown formatting from cells for display
        clean = [re.sub(r"\*\*(.+?)\*\*", r"\1", c) for c in cells]
        rows.append(clean)
    return rows


def extract_cost_from_table(rows):
    """从成本全景表中提取数值数据（用于图表生成）。
    返回: (dimensions, amounts, percentages)
    """
    dims, amounts, pcts = [], [], []
    for row in rows:
        if len(row) < 3:
            continue
        # header row detection
        if any(kw in row[0] for kw in ["维度", "成本"]):
            continue
        dim = row[0]
        amt_str = row[1] if len(row) > 1 else ""
        pct_str = row[2] if len(row) > 2 else ""

        amt_match = re.search(r"[\d.]+", str(amt_str).replace("¥", "").replace(",", ""))
        pct_match = re.search(r"([\d.]+)", str(pct_str))

        if amt_match and pct_match:
            dims.append(dim)
            amounts.append(float(amt_match.group()))
            pcts.append(float(pct_match.group()))
    return dims, amounts, pcts


# ============================================================
# PDF 渲染器
# ============================================================

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_auto_page_break(True, 20)
        font_path = find_cjk()
        if font_path:
            self.add_font("CJK", "", font_path)
            self.add_font("CJK", "B", font_path)  # fpdf2 will fake bold
        else:
            self.add_font("CJK", "", "Helvetica")
            self.add_font("CJK", "B", "Helvetica")
        self.font_name = "CJK"
        self._in_quote = False
        self._chart_paths = []

    # ---- helpers ----
    def write_para(self, text, size=10, bold=False, color=None):
        """写一个段落，自动换行"""
        style = "B" if bold else ""
        self.set_font(self.font_name, style, size)
        if color:
            self.set_text_color(*color)
        # 清理 markdown 标记 + emoji
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        clean = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", clean)
        clean = strip_emoji(clean)
        self.multi_cell(0, self._lh(size), clean, align="L")
        if color:
            self.set_text_color(0, 0, 0)
        self.ln(2)

    def _lh(self, size):
        return size * 0.45

    def section_title(self, text, level=2):
        sizes = {1: 18, 2: 13, 3: 11}
        s = sizes.get(level, 11)
        style = "B" if level <= 2 else ""
        self.set_font(self.font_name, style, s)
        self.ln(3 if level == 2 else 2)
        clean = strip_emoji(text)
        self.multi_cell(0, self._lh(s), clean, align="L")
        if level == 2:
            self.set_draw_color(200, 50, 50)
            self.set_line_width(0.4)
            self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
            self.ln(4)
        else:
            self.ln(2)

    def _clean(self, text):
        """清理 markdown 标记 + emoji"""
        c = re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))
        c = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", c)
        return strip_emoji(c)

    def render_table(self, rows, col_widths=None, header_bg=(44, 62, 80), font_size=8):
        """渲染表格，自动计算列宽"""
        if not rows:
            return
        ncols = len(rows[0])
        if col_widths is None:
            usable = self.w - self.l_margin - self.r_margin
            col_widths = [usable / ncols] * ncols

        self.ln(2)
        # Header
        self.set_fill_color(*header_bg)
        self.set_text_color(255, 255, 255)
        self.set_font(self.font_name, "", font_size)
        header_h = self._lh(font_size) + 3
        for j, cell in enumerate(rows[0]):
            x = self.get_x()
            self.set_fill_color(*header_bg)
            self.rect(x, self.get_y(), col_widths[j], header_h, "FD")
            self.set_xy(x + 1, self.get_y() + 1.5)
            clean = self._clean(cell)
            self.cell(col_widths[j] - 2, self._lh(font_size), clean)
        self.ln(header_h)

        # Data rows
        self.set_text_color(0, 0, 0)
        alternating = False
        for row in rows[1:]:
            alternating = not alternating
            row_h = self._lh(font_size) + 2
            if self.get_y() + row_h > self.h - self.b_margin:
                self.add_page()

            y_before = self.get_y()
            if alternating:
                self.set_fill_color(248, 248, 248)

            for j, cell in enumerate(row):
                x = self.l_margin + sum(col_widths[:j])
                self.set_xy(x, y_before)
                if alternating:
                    self.rect(x, y_before, col_widths[j], row_h, "FD")
                else:
                    self.rect(x, y_before, col_widths[j], row_h, "D")
                self.set_xy(x + 1, y_before + 1)
                clean = self._clean(cell)
                self.set_font(self.font_name, "", font_size)
                self.cell(col_widths[j] - 2, self._lh(font_size), clean)

            self.set_xy(self.l_margin, y_before + row_h)
        self.ln(4)

    def render_quote(self, paragraphs):
        """渲染引用块"""
        self.set_fill_color(252, 240, 240)
        self.set_text_color(100, 100, 100)
        self.set_font(self.font_name, "", 9)
        for para in paragraphs:
            self.set_x(self.l_margin + 4)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 8, self._lh(9), self._clean(para), align="L")
            self.ln(1)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def render_code(self, code_lines):
        """渲染代码块/ASCII 图"""
        self.set_fill_color(245, 245, 245)
        self.set_text_color(60, 60, 60)
        self.set_font(self.font_name, "", 8)
        for cl in code_lines:
            self.set_x(self.l_margin + 4)
            self.cell(0, self._lh(8), self._clean(cl[:120]))
            self.ln()
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def render_ul(self, items):
        """渲染无序列表"""
        self.set_font(self.font_name, "", 9)
        for item in items:
            self.set_x(self.l_margin + 2)
            bullet = chr(0x2022)
            self.cell(5, self._lh(9), bullet)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 10, self._lh(9), self._clean(item), align="L")
            self.ln(1)
        self.ln(2)

    def render_meta(self, text):
        """渲染数据来源斜体小字"""
        self.set_text_color(130, 130, 130)
        self.set_font(self.font_name, "", 8)
        self.multi_cell(0, self._lh(8), self._clean(text), align="L")
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def embed_chart(self, chart_path, caption=""):
        """嵌入图表图片"""
        if not os.path.exists(chart_path):
            return
        self.ln(3)
        if caption:
            self.set_font(self.font_name, "", 9)
            self.cell(0, self._lh(9), caption)
            self.ln(3)
        # 计算缩放：A4 可用宽度约 180mm
        usable_w = self.w - self.l_margin - self.r_margin
        # 从文件获取实际尺寸
        try:
            from PIL import Image
            img = Image.open(chart_path)
            iw, ih = img.size
            dpi = img.info.get("dpi", (150, 150))
            iw_mm = iw / dpi[0] * 25.4
            ih_mm = ih / dpi[1] * 25.4
        except Exception:
            iw_mm, ih_mm = 180, 100

        if iw_mm > usable_w:
            scale = usable_w / iw_mm
            iw_mm = usable_w
            ih_mm *= scale

        # 如果放不下，换页
        if self.get_y() + ih_mm > self.h - self.b_margin:
            self.add_page()
        self.image(chart_path, x=self.l_margin, w=iw_mm)
        self.ln(ih_mm + 5)


# ============================================================
# 主流程
# ============================================================

def md_to_pdf(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = parse_blocks(lines)

    pdf = ReportPDF()
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)
    pdf.add_page()

    # ---- 第一遍：收集所有表格行，用于图表生成 ----
    all_table_rows = []
    for blk in blocks:
        if blk["type"] == "table":
            rows = parse_table_lines(blk["lines"])
            all_table_rows.append(rows)

    # 找到第一个（成本全景）表，生成图表
    chart_dir = tempfile.mkdtemp(prefix="cost_charts_")
    chart_files = []
    if CHARTS_AVAILABLE and all_table_rows:
        dims, amounts, pcts = extract_cost_from_table(all_table_rows[0])
        if dims and amounts:
            breakdown = [
                {"dimension": d, "amount": a, "pct": p}
                for d, a, p in zip(dims, amounts, pcts)
            ]
            # 从标题中提取总价
            price = sum(amounts)
            for blk in blocks:
                if blk["type"] == "h1":
                    m = re.search(r"¥(\d+)", blk.get("text", ""))
                    if m:
                        price = float(m.group(1))
                        break

            bar_path = os.path.join(chart_dir, "bar.png")
            pie_path = os.path.join(chart_dir, "pie.png")
            try:
                _chart_cjk()
                generate_bar_chart(breakdown, price, bar_path)
                chart_files.append(("成本拆解条图", bar_path))
                generate_pie_chart(breakdown, price, pie_path)
                chart_files.append(("成本分布饼图", pie_path))
            except Exception as e:
                print(f"图表生成失败: {e}")

    # ---- 第二遍：渲染 PDF ----
    for blk in blocks:
        t = blk["type"]

        if t == "h1":
            pdf.section_title(blk["text"], level=1)
            continue

        if t == "h2":
            # 在"成本全景"标题后插入图表
            if "成本全景" in blk.get("text", ""):
                pdf.section_title(blk["text"])
                # 渲染紧跟的表格
                continue
            pdf.section_title(blk["text"])
            continue

        if t == "h3":
            pdf.section_title(blk["text"], level=3)
            continue

        if t == "hr":
            pdf.ln(2)
            continue

        if t == "para":
            pdf.write_para(blk["text"])
            continue

        if t == "table":
            rows = parse_table_lines(blk["lines"])
            if rows:
                # 成本全景表——插入图表在表后
                pdf.render_table(rows, font_size=7)
                # 如果是第一个表格（成本全景），后面插入图表
                if chart_files and blk is [b for b in blocks if b["type"] == "table"][0]:
                    for caption, cpath in chart_files:
                        pdf.embed_chart(cpath, caption)
                    chart_files = []  # 只插入一次
            continue

        if t == "quote":
            pdf.render_quote(blk["paragraphs"])
            continue

        if t == "code":
            pdf.render_code(blk["lines"])
            continue

        if t == "ul":
            pdf.render_ul(blk["items"])
            continue

        if t == "meta":
            pdf.render_meta(blk["text"])
            continue

    pdf.output(output_path)
    print(f"PDF 已生成: {output_path}")
    print(f"总页数: {pdf.page_no()}")

    # 清理临时图表
    for _, cpath in chart_files:
        try:
            os.remove(cpath)
        except Exception:
            pass
    try:
        os.rmdir(chart_dir)
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python md_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    md_to_pdf(sys.argv[1], sys.argv[2])
