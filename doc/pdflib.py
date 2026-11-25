# pdflib.py - layout helpers for the sid2pokey guide (reportlab).
#
# Text is Paragraph markup: <b>, <i>, <font face="Mono">, <super>; escape & < > with
# esc().  Listings are read from the files of the repository, so that they cannot
# drift from the code.
import os
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image,
                                KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
IMG = os.path.join(HERE, "img")

# ---------------------------------------------------------------- fonts
_FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", _FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", _FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Italic", _FD + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Sans-BoldItalic", _FD + "DejaVuSans-BoldOblique.ttf"))
pdfmetrics.registerFont(TTFont("Mono", _FD + "DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", _FD + "DejaVuSansMono-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Italic", _FD + "DejaVuSansMono-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Mono-BoldItalic", _FD + "DejaVuSansMono-BoldOblique.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Italic",
                              boldItalic="Sans-BoldItalic")
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono-Italic",
                              boldItalic="Mono-BoldItalic")

# ---------------------------------------------------------------- colours
INK = colors.HexColor("#1D2040")
BLUE = colors.HexColor("#2B3190")        # the dark blue of the C64 screen
LBLUE = colors.HexColor("#8E95F2")       # its light blue
PALE = colors.HexColor("#EEF0FD")
GRID = colors.HexColor("#C5C9EE")
CODEBG = colors.HexColor("#F3F4FA")
GREY = colors.HexColor("#6B7090")

CALLOUT = {
    "NOTA":        (colors.HexColor("#2B6CB0"), colors.HexColor("#EAF2FC")),
    "CONSIGLIO":   (colors.HexColor("#2F855A"), colors.HexColor("#E8F6EE")),
    "ATTENZIONE":  (colors.HexColor("#B7791F"), colors.HexColor("#FFF5DC")),
    "TRAPPOLA":    (colors.HexColor("#B02A37"), colors.HexColor("#FDEBED")),
    "VERIFICATO":  (colors.HexColor("#5B3FA5"), colors.HexColor("#F0EBFB")),
}

PAGE_W, PAGE_H = A4
MARGIN_X = 20 * mm
BODY_W = PAGE_W - 2 * MARGIN_X

# ---------------------------------------------------------------- styles
ST = {}
ST["body"] = ParagraphStyle("body", fontName="Sans", fontSize=9.4, leading=13.6, textColor=INK,
                            spaceAfter=5)
ST["small"] = ParagraphStyle("small", parent=ST["body"], fontSize=8.2, leading=11.4)
ST["bullet"] = ParagraphStyle("bullet", parent=ST["body"], leftIndent=13, bulletIndent=3,
                              spaceAfter=2.5)
ST["cell"] = ParagraphStyle("cell", fontName="Sans", fontSize=8.1, leading=10.6, textColor=INK)
ST["cellb"] = ParagraphStyle("cellb", parent=ST["cell"], fontName="Sans-Bold", textColor=colors.white)
ST["caption"] = ParagraphStyle("caption", fontName="Sans-Italic", fontSize=8, leading=10.5,
                               textColor=GREY, alignment=TA_CENTER, spaceBefore=3, spaceAfter=9)
ST["h1"] = ParagraphStyle("h1", fontName="Sans-Bold", fontSize=22, leading=26, textColor=BLUE,
                          spaceAfter=10, spaceBefore=0)
ST["h1x"] = ParagraphStyle("h1x", fontName="Sans-Bold", fontSize=22, leading=26, textColor=BLUE,
                           spaceAfter=10, spaceBefore=0)
ST["h2"] = ParagraphStyle("h2", fontName="Sans-Bold", fontSize=14, leading=18, textColor=BLUE,
                          spaceBefore=14, spaceAfter=5, keepWithNext=1)
ST["h3"] = ParagraphStyle("h3", fontName="Sans-Bold", fontSize=10.6, leading=14, textColor=INK,
                          spaceBefore=9, spaceAfter=3, keepWithNext=1)
ST["code"] = ParagraphStyle("code", fontName="Mono", fontSize=7.3, leading=9.2, textColor=INK,
                            backColor=CODEBG, borderColor=GRID, borderWidth=0.5, borderPadding=(4, 5, 4, 5),
                            leftIndent=5, rightIndent=5, spaceBefore=4, spaceAfter=9)
ST["toc1"] = ParagraphStyle("toc1", fontName="Sans-Bold", fontSize=10, leading=15, textColor=INK,
                            leftIndent=0, spaceBefore=4)
ST["toc2"] = ParagraphStyle("toc2", fontName="Sans", fontSize=9, leading=12.5, textColor=INK,
                            leftIndent=14)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def m(s):
    """inline monospace"""
    return '<font face="Mono" size="8.3">%s</font>' % esc(s)


# ---------------------------------------------------------------- document
class Doc(BaseDocTemplate):
    def __init__(self, path, title, footer_text, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=A4, title=title,
                                 author="sid2pokey", subject="SID player for the Atari 8-bit",
                                 leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                                 topMargin=24 * mm, bottomMargin=20 * mm, **kw)
        self.footer_text = footer_text
        self.chapter = ""
        self._key = 0
        body = Frame(self.leftMargin, self.bottomMargin, BODY_W, PAGE_H - 44 * mm, id="body",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover = Frame(0, 0, PAGE_W, PAGE_H, id="cover", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover], onPage=self._cover_bg),
            PageTemplate(id="body", frames=[body], onPage=self._chrome, onPageEnd=self._header),
        ])

    # background of the cover
    def _cover_bg(self, c, d):
        c.saveState()
        c.setFillColor(BLUE)
        c.rect(0, PAGE_H * 0.46, PAGE_W, PAGE_H * 0.54, fill=1, stroke=0)
        c.setFillColor(LBLUE)
        c.rect(0, PAGE_H * 0.46 - 5 * mm, PAGE_W, 5 * mm, fill=1, stroke=0)
        c.restoreState()

    def _chrome(self, c, d):
        c.saveState()
        c.setStrokeColor(GRID)
        c.setLineWidth(0.6)
        c.line(MARGIN_X, PAGE_H - 17 * mm, PAGE_W - MARGIN_X, PAGE_H - 17 * mm)
        c.line(MARGIN_X, 15 * mm, PAGE_W - MARGIN_X, 15 * mm)
        c.setFont("Sans", 7.6)
        c.setFillColor(GREY)
        c.drawString(MARGIN_X, 10.5 * mm, self.footer_text)
        c.setFont("Sans-Bold", 8.5)
        c.setFillColor(BLUE)
        c.drawRightString(PAGE_W - MARGIN_X, 10.5 * mm, str(d.page))
        c.restoreState()

    def _header(self, c, d):
        c.saveState()
        c.setFont("Sans-Bold", 8.5)
        c.setFillColor(BLUE)
        c.drawString(MARGIN_X, PAGE_H - 13.5 * mm, "SID → POKEY")
        c.setFont("Sans", 8.5)
        c.setFillColor(GREY)
        c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 13.5 * mm, self.chapter)
        c.restoreState()

    def beforeDocument(self):
        self._key = 0          # the keys of the table of contents must be the same in every pass
        self.chapter = ""

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph):
            name = fl.style.name
            if name in ("h1", "h2"):
                text = re.sub(r"<[^>]+>", "", fl.getPlainText())
                level = 0 if name == "h1" else 1
                self._key += 1
                key = "h%d" % self._key
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level, 0)
                self.notify("TOCEntry", (level, text, self.page, key))
                if level == 0:
                    self.chapter = text


class Heading(Paragraph):
    """a heading that the table of contents links to"""
    def __init__(self, text, style):
        Paragraph.__init__(self, text, style)


# ---------------------------------------------------------------- building blocks
class Numbering:
    def __init__(self):
        self.ch = 0
        self.sec = 0


NUM = Numbering()


def chapter(S, title):
    NUM.ch += 1
    NUM.sec = 0
    S.append(PageBreak())
    S.append(Heading("%d. %s" % (NUM.ch, title), ST["h1"]))


def section(S, title, need=42):
    """need: millimetres that must be free at the bottom of the page, else a new page"""
    NUM.sec += 1
    S.append(CondPageBreak(need * mm))
    S.append(Heading("%d.%d  %s" % (NUM.ch, NUM.sec, title), ST["h2"]))


def sub(S, title):
    S.append(Paragraph(title, ST["h3"]))


def P(S, text, style="body"):
    S.append(Paragraph(text, ST[style]))


def bullets(S, items, style="bullet"):
    for it in items:
        S.append(Paragraph(it, ST[style], bulletText="•"))
    S.append(Spacer(1, 3))


def numbered(S, items):
    for i, it in enumerate(items, 1):
        S.append(Paragraph(it, ST["bullet"], bulletText="%d." % i))
    S.append(Spacer(1, 3))


def callout(S, kind, text, title=None):
    fg, bg = CALLOUT[kind]
    label = Paragraph('<font name="Sans-Bold" size="8" color="%s">%s%s</font>' % (
        fg.hexval().replace("0x", "#"), kind, (" — " + title) if title else ""),
        ParagraphStyle("cl", fontName="Sans-Bold", fontSize=8, leading=10, spaceAfter=2))
    body = Paragraph(text, ParagraphStyle("cb", parent=ST["body"], fontSize=8.8, leading=12.4,
                                          spaceAfter=0))
    t = Table([[[label, body]]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3.2, fg),
        ("BOX", (0, 0), (-1, -1), 0.4, fg),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    S.append(KeepTogether([Spacer(1, 3), t, Spacer(1, 8)]))


def table(S, data, widths, header=True, align=None, zebra=True, mono_cols=(), font=None, caption=None,
          keep=True):
    """data: list of rows of strings (Paragraph markup). widths in mm (sum <= 170)."""
    rows = []
    cs = ST["cell"] if font is None else ParagraphStyle("c", parent=ST["cell"], fontSize=font,
                                                         leading=font * 1.3)
    hs = ST["cellb"] if font is None else ParagraphStyle("hc", parent=ST["cellb"], fontSize=font,
                                                          leading=font * 1.3)
    for r, row in enumerate(data):
        cells = []
        for c, cell in enumerate(row):
            if isinstance(cell, str):
                txt = cell
                if c in mono_cols and not (header and r == 0):
                    txt = '<font face="Mono" size="%s">%s</font>' % ((font or 8.1) - 0.3, txt)
                st = hs if (header and r == 0) else cs
                if align and align[c] != "L" and not (header and r == 0):
                    st = ParagraphStyle("a", parent=st, alignment={"C": 1, "R": 2}[align[c]])
                cells.append(Paragraph(txt, st))
            else:
                cells.append(cell)
        rows.append(cells)
    t = Table(rows, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BLUE), ("LINEBELOW", (0, 0), (-1, 0), 0.8, BLUE)]
    if zebra:
        for r in range(1 if header else 0, len(rows)):
            if (r % 2) == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), PALE))
    t.setStyle(TableStyle(style))
    blk = [t]
    if caption:
        blk.append(Paragraph(caption, ST["caption"]))
    else:
        blk.append(Spacer(1, 8))
    if keep and len(rows) <= 14:
        S.append(KeepTogether(blk))
    else:
        S.extend(blk)


def figure(S, name, caption, width_mm=150, border=True):
    path = os.path.join(IMG, name)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    wp = width_mm * mm
    im = Image(path, width=wp, height=wp * h / w)
    if border:
        t = Table([[im]], colWidths=[wp + 4])
        t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, GRID),
                               ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                               ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        im = t
    S.append(KeepTogether([im, Paragraph(caption, ST["caption"])]))


def flow(S, fl, caption):
    S.append(KeepTogether([fl, Paragraph(caption, ST["caption"])]))


def code(S, text, title=None, size=None):
    lines = text.rstrip("\n").split("\n")
    for ln in lines:
        if len(ln.expandtabs(4)) > 108:
            print("WARNING: listing line longer than 108 characters:", ln[:60])
    st = ST["code"] if size is None else ParagraphStyle("c2", parent=ST["code"], fontSize=size,
                                                         leading=size * 1.26)
    items = []
    if title:
        items.append(CondPageBreak(32 * mm))        # a title is never alone at the bottom of a page
        items.append(Paragraph('<font name="Sans-Bold" size="8" color="#2B3190">%s</font>' % esc(title),
                               ParagraphStyle("ct", fontName="Sans-Bold", fontSize=8, spaceBefore=6,
                                              spaceAfter=2)))
    items.append(Preformatted("\n".join(l.expandtabs(4) for l in lines), st))
    S.extend(items)


def excerpt(path, start, end=None, include_end=True, max_lines=None):
    """lines of a file of the repository from the first line containing `start` to the first
    following line containing `end`"""
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        lines = f.read().split("\n")
    i = next(k for k, l in enumerate(lines) if start in l)
    j = len(lines)
    if end is not None:
        j = next(k for k in range(i + 1, len(lines)) if end in lines[k]) + (1 if include_end else 0)
    out = lines[i:j]
    if max_lines:
        out = out[:max_lines]
    return "\n".join(out)


def read_text(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- vector diagrams
class Diagram(Flowable):
    def __init__(self, width, height):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def wrap(self, aw, ah):
        return self.width, self.height

    # drawing helpers (origin at the bottom left)
    def box(self, x, y, w, h, text="", fill=PALE, stroke=BLUE, size=8, bold=False, color=INK, r=3,
            lines=None):
        c = self.canv
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.9)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1)
        c.setFillColor(color)
        rows = lines if lines is not None else text.split("\n")
        c.setFont("Sans-Bold" if bold else "Sans", size)
        n = len(rows)
        lead = size * 1.25
        y0 = y + h / 2 + (n - 1) * lead / 2 - size * 0.33
        for i, t in enumerate(rows):
            c.drawCentredString(x + w / 2, y0 - i * lead, t)

    def arrow(self, x1, y1, x2, y2, color=BLUE, width=1.3, head=5):
        import math
        c = self.canv
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(width)
        c.line(x1, y1, x2, y2)
        a = math.atan2(y2 - y1, x2 - x1)
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2 - head * math.cos(a - 0.4), y2 - head * math.sin(a - 0.4))
        p.lineTo(x2 - head * math.cos(a + 0.4), y2 - head * math.sin(a + 0.4))
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    def text(self, x, y, s, size=8, font="Sans", color=INK, anchor="l"):
        c = self.canv
        c.setFont(font, size)
        c.setFillColor(color)
        {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[anchor](x, y, s)
