"""Small python-docx toolkit: GOST-like academic formatting and table-based editable diagrams."""
import re
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
BLACK = RGBColor(0, 0, 0)
TEXT_W = 16.5      # portrait text width, cm
TEXT_W_LAND = 25.2  # landscape text width, cm


def _fonts(rpr_parent_font, el):
    """Force Times New Roman for all scripts and drop theme font overrides."""
    rpr = el.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in list(rf.attrib):
        del rf.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)


def setup(doc):
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin, s.right_margin = Cm(3), Cm(1.5)
    s.top_margin, s.bottom_margin = Cm(2), Cm(2)
    s.footer_distance = Cm(1.0)
    st = doc.styles
    n = st["Normal"]
    n.font.name, n.font.size, n.font.color.rgb = FONT, Pt(14), BLACK
    _fonts(None, n.element)
    lang = OxmlElement("w:lang"); lang.set(qn("w:val"), "ru-RU"); lang.set(qn("w:eastAsia"), "ru-RU")
    n.element.get_or_add_rPr().append(lang)
    pf = n.paragraph_format
    pf.line_spacing, pf.space_before, pf.space_after = 1.5, Pt(0), Pt(0)
    pf.first_line_indent = Cm(1.25)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.widow_control = True
    for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Title", 16)):
        h = st[name]
        rpr = h.element.get_or_add_rPr()
        for tag in ("w:color", "w:rFonts", "w:sz", "w:szCs", "w:i", "w:iCs"):
            for e in rpr.findall(qn(tag)):
                rpr.remove(e)
        h.font.name, h.font.size, h.font.bold, h.font.italic = FONT, Pt(size), True, False
        h.font.color.rgb = BLACK
        _fonts(None, h.element)
        ppr = h.element.get_or_add_pPr()
        for e in ppr.findall(qn("w:pBdr")):
            ppr.remove(e)
        hp = h.paragraph_format
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hp.first_line_indent = Cm(1.25)
        hp.left_indent = Cm(0)
        hp.space_before = Pt(18 if name == "Heading 1" else 12)
        hp.space_after = Pt(12 if name == "Heading 1" else 6)
        hp.line_spacing = 1.15
        hp.keep_with_next = True
    # page numbers, centred in the footer; title page has none
    s.different_first_page_header_footer = True
    p = s.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    r = p.add_run()
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); r._r.append(f)
        else:
            t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = txt
            r._r.append(t)
    r.font.size = Pt(12)


def runs(p, text, size=None, bold=None):
    """Add text with **bold** markup."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part:
            continue
        r = p.add_run(part)
        r.font.color.rgb = BLACK
        if size:
            r.font.size = Pt(size)
        if bold or i % 2 == 1:
            r.bold = True
    return p


def para(doc, text, align=None, indent=True, bold=False, size=None, keep=False, space_after=0):
    p = doc.add_paragraph()
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if not indent:
        p.paragraph_format.first_line_indent = Cm(0)
    if keep:
        p.paragraph_format.keep_with_next = True
    if space_after:
        p.paragraph_format.space_after = Pt(space_after)
    runs(p, text, size=size, bold=bold)
    return p


def bullets(doc, items, last="."):
    """GOST-style dash list: «– item;» … «– item.»"""
    for i, it in enumerate(items):
        end = last if i == len(items) - 1 else ";"
        t = it.rstrip(";.")
        para(doc, "– " + t + end)


def caption_table(doc, text):
    p = para(doc, text, align="left", indent=False, keep=True)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(3)
    return p


def caption_figure(doc, text):
    p = para(doc, text, align="center", indent=False)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.0
    return p


# ------------------------------------------------------------------ tables
def _set_cell_borders(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); tcPr.append(b)
    for edge in ("top", "left", "bottom", "right"):
        if edge in kw:
            el = b.find(qn("w:" + edge))
            if el is None:
                el = OxmlElement("w:" + edge); b.append(el)
            val = kw[edge]
            if val:
                el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(val))
                el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
            else:
                el.set(qn("w:val"), "nil")
    # schema order inside tcBorders: top, left(start), bottom, right(end)
    order = {qn("w:top"): 0, qn("w:left"): 1, qn("w:bottom"): 2, qn("w:right"): 3}
    kids = sorted(b, key=lambda e: order.get(e.tag, 9))
    for k in kids:
        b.remove(k)
    for k in kids:
        b.append(k)


def _tbl_pr(table, borders, cell_mar):
    tblPr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    bd = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        if borders:
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6"); e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
        bd.append(e)
    tblPr.append(bd)
    mar = OxmlElement("w:tblCellMar")
    for edge, v in (("top", cell_mar[0]), ("left", cell_mar[1]), ("bottom", cell_mar[0]),
                    ("right", cell_mar[1])):
        e = OxmlElement("w:" + edge); e.set(qn("w:w"), str(int(v * 567))); e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblPr.append(mar)


def cell_text(cell, text, size=12, bold=False, align="left", valign="center"):
    cell.text = ""
    lines = text.split("\n")
    p = cell.paragraphs[0]
    for i, line in enumerate(lines):
        if i:
            p = cell.add_paragraph()
        pf = p.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.line_spacing = 1.0
        pf.space_before = pf.space_after = Pt(0)
        p.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
                       "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
        runs(p, line, size=size, bold=bold)
    cell.vertical_alignment = {"center": WD_CELL_VERTICAL_ALIGNMENT.CENTER,
                               "top": WD_CELL_VERTICAL_ALIGNMENT.TOP}[valign]


def _no_split(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    if header:
        trPr.append(OxmlElement("w:tblHeader"))


def data_table(doc, header, rows, widths, size=12, align=None, center_cols=(), bold_first_col=False):
    """Bordered table; header repeated on page breaks; rows never split."""
    t = doc.add_table(rows=1 + len(rows), cols=len(widths))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _tbl_pr(t, True, (0.05, 0.12))
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for r, data in enumerate([header] + rows):
        row = t.rows[r]
        _no_split(row, header=(r == 0))
        for c, w in enumerate(widths):
            cell = row.cells[c]
            cell.width = Cm(w)
            txt = data[c] if c < len(data) else ""
            if r == 0:
                cell_text(cell, txt, size=size, bold=True, align="center")
                sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "FFFFFF")
                cell._tc.get_or_add_tcPr().append(sh)
            else:
                al = "center" if c in center_cols else "left"
                cell_text(cell, txt, size=size, align=al, valign="center",
                          bold=bold_first_col and c == 0)
    after = doc.add_paragraph()
    after.paragraph_format.line_spacing = 1.0
    after.paragraph_format.space_after = Pt(4)
    return t


def boxed(doc, text, size=14):
    """Single framed paragraph used for the emphasised conclusion."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    _tbl_pr(t, False, (0.2, 0.3))
    c = t.rows[0].cells[0]
    c.width = Cm(TEXT_W - 0.4)
    cell_text(c, text, size=size, align="justify")
    for p in c.paragraphs:
        p.paragraph_format.line_spacing = 1.3
    _set_cell_borders(c, top=18, left=18, bottom=18, right=18)
    doc.add_paragraph().paragraph_format.line_spacing = 1.0


# ---------------------------------------------------------- diagram engine
class Diagram:
    """Editable diagram built from a borderless Word table on an N-column grid.

    Items per row:
      ("box", c0, c1, text[, opts])  merged cells c0..c1 framed ("thick", "bold", "size")
      ("text", c0, c1, text[, opts]) merged cells, no frame
      ("v", b)                        vertical line on grid boundary b
      ("h", b0, b1)                   horizontal line from boundary b0 to b1 (top of row)
      ("arrow", b[, glyph])           arrow glyph centred on boundary b
    Row kinds: "box" (auto height), "line" (thin), "arrow".
    """

    def __init__(self, n, width_cm=TEXT_W, size=11):
        self.n, self.w, self.size, self.rows = n, width_cm, size, []

    def row(self, kind, *items):
        self.rows.append((kind, items))
        return self

    def render(self, doc):
        n, cw = self.n, self.w / self.n
        t = doc.add_table(rows=len(self.rows), cols=n)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        _tbl_pr(t, False, (0.0, 0.04))
        for i in range(n):
            t.columns[i].width = Cm(cw)
        for r, (kind, items) in enumerate(self.rows):
            row = t.rows[r]
            _no_split(row)
            for c in range(n):
                row.cells[c].width = Cm(cw)
                cell_text(row.cells[c], "", size=4)
            if kind == "line":
                row.height, row.height_rule = Cm(0.32), WD_ROW_HEIGHT_RULE.EXACTLY
            elif kind == "arrow":
                row.height, row.height_rule = Cm(0.42), WD_ROW_HEIGHT_RULE.EXACTLY
            else:
                row.height, row.height_rule = Cm(0.9), WD_ROW_HEIGHT_RULE.AT_LEAST
            # borders that do not depend on merges
            for it in items:
                if it[0] == "v":
                    b = it[1]
                    if b < n:
                        _set_cell_borders(t.cell(r, b), left=12)
                    else:
                        _set_cell_borders(t.cell(r, n - 1), right=12)
                elif it[0] == "h":
                    for c in range(it[1], it[2]):
                        _set_cell_borders(t.cell(r, c), top=12)
            # merged items, right to left so indices stay valid
            for it in sorted([i for i in items if i[0] in ("box", "text", "arrow")],
                             key=lambda i: -i[1]):
                if it[0] == "arrow":
                    b = it[1]
                    cell = t.cell(r, b - 1).merge(t.cell(r, b))
                    cell_text(cell, it[2] if len(it) > 2 else "▼", size=9, align="center")
                    for p in cell.paragraphs:
                        p.paragraph_format.line_spacing = Pt(9)
                    continue
                c0, c1, text = it[1], it[2], it[3]
                opts = it[4] if len(it) > 4 else {}
                cell = t.cell(r, c0).merge(t.cell(r, c1)) if c1 > c0 else t.cell(r, c0)
                cell_text(cell, text, size=opts.get("size", self.size),
                          bold=opts.get("bold", False), align=opts.get("align", "center"))
                if it[0] == "box":
                    wdt = 18 if opts.get("thick") else 8
                    _set_cell_borders(cell, top=wdt, left=wdt, bottom=wdt, right=wdt)
                    mar = OxmlElement("w:tcMar")
                    for edge in ("top", "bottom", "left", "right"):
                        e = OxmlElement("w:" + edge)
                        e.set(qn("w:w"), "57" if edge in ("top", "bottom") else "85")
                        e.set(qn("w:type"), "dxa"); mar.append(e)
                    cell._tc.get_or_add_tcPr().append(mar)
        sp = doc.add_paragraph()
        sp.paragraph_format.line_spacing = 1.0
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.keep_with_next = True
        return t


def landscape_section(doc):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.LANDSCAPE
    s.page_width, s.page_height = Cm(29.7), Cm(21)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)
    s.different_first_page_header_footer = False
    return s


def portrait_section(doc):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)
    s.different_first_page_header_footer = False
    return s


def page_break(doc):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.add_run().add_break(WD_BREAK.PAGE)


def toc_line(doc, text, page, level):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0 if level == 1 else 0.75)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.line_spacing = 1.25
    pf.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    runs(p, f"{text}\t{page}")
