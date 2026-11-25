# diagrams.py - the vector figures of the guide
from reportlab.lib import colors
from pdflib import BLUE, BODY_W, GREY, GRID, INK, LBLUE, PALE, Diagram

AMBER = colors.HexColor("#E7B04A")
GREEN = colors.HexColor("#4C9F70")
RED = colors.HexColor("#C0505C")
SAND = colors.HexColor("#FFF5DC")
MINT = colors.HexColor("#E8F6EE")
ROSE = colors.HexColor("#FDEBED")
LILAC = colors.HexColor("#F0EBFB")


class Architecture(Diagram):
    def __init__(self):
        Diagram.__init__(self, BODY_W, 282)

    def draw(self):
        c = self.canv
        W = self.width
        # host container
        c.setFillColor(colors.HexColor("#F7F8FE"))
        c.setStrokeColor(GRID)
        c.roundRect(0, 152, W, 128, 6, fill=1, stroke=1)
        self.text(8, 266, "PC \u2014 tools/sidconv  (C, un solo file pi\u00f9 cpu6502.h)", 8.5, "Sans-Bold", BLUE)
        names = [
            ("File .sid", "PSID / RSID\ncodice 6502\n+ dati", SAND),
            ("1  Emulatore 6502", "init(), play()\nregistra le scritture\nai registri SID", PALE),
            ("2  Modello SID", "frequenza, onda,\ninviluppo ADSR\nper ogni voce", PALE),
            ("3  Mappatura", "layout dei canali,\nAUDF / AUDC,\nAUDCTL", PALE),
            ("4  Compressione", "un flusso LZ\nper registro\n+ verifica", PALE),
        ]
        bw, gap = 84, 12
        xs = []
        for i, (t, b, f) in enumerate(names):
            x = 4 + i * (bw + gap)
            xs.append(x)
            self.box(x, 164, bw, 84, fill=f, lines=[], bold=True)
            self.text(x + bw / 2, 233, t, 7.6, "Sans-Bold", BLUE, "c")
            for k, line in enumerate(b.split("\n")):
                self.text(x + bw / 2, 215 - k * 10.5, line, 7, "Sans", INK, "c")
            if i:
                self.arrow(xs[i - 1] + bw, 206, x, 206)
        # elbow from the last stage down to song.bin
        c.setStrokeColor(BLUE)
        c.setLineWidth(1.3)
        xe = xs[-1] + bw / 2
        c.line(xe, 164, xe, 143)
        c.line(xe, 143, 56, 143)
        self.arrow(56, 143, 56, 108)
        self.text(xe - 4, 146, "song.bin", 7.5, "Mono", BLUE, "r")
        # atari container
        c.setFillColor(colors.HexColor("#F7F8FE"))
        c.setStrokeColor(GRID)
        c.roundRect(0, 0, W, 134, 6, fill=1, stroke=1)
        self.text(8, 122, "Atari 400/800/XL/XE \u2014 sid2pokey.com", 8.5, "Sans-Bold", BLUE)
        self.box(8, 64, 96, 42, fill=SAND, lines=["song.bin", "(RODATA)", "stream LZ"], size=7.6)
        self.box(130, 64, 160, 42, fill=PALE, lines=["Player 6502 (sp-common.asm)", "VBI + DLI: decodifica l'LZ,",
                                                        "scrive i registri"], size=7.4)
        self.box(396, 64, 80, 42, fill=MINT, lines=["POKEY 1  $D200", "POKEY 2  $D210"], size=7)
        self.arrow(104, 85, 130, 85)
        self.arrow(290, 85, 396, 85, color=GREEN)
        self.text(343, 90, "AUDF / AUDC", 6.6, "Mono", GREEN, "c")
        self.box(130, 8, 160, 42, fill=PALE, lines=["Schermata (sid2pokey.c)", "titolo, autore,", "VU meter, tempo"], size=7.4)
        self.box(316, 8, 120, 42, fill=SAND, lines=["font C64", "(font.bin, in RAM)"], size=7.2)
        self.arrow(316, 29, 290, 29, color=GREY, width=1, head=4)
        c.setDash(2, 2)
        self.arrow(210, 64, 210, 50, color=GREY, width=1, head=4)
        c.setDash()
        self.text(216, 55, "outbuf: i volumi decodificati", 6.4, "Mono", GREY)


class FrameTimeline(Diagram):
    """one video frame (PAL, 312 lines) from a VBI to the next, for 1..4 records per frame"""
    # (K, [(target line offset, actual line offset)]) in lines after the VBI, PAL
    DATA = {1: [], 2: [(156, 159)], 3: [(104, 103), (208, 207)], 4: [(78, 79), (156, 159), (234, 231)]}

    def __init__(self):
        Diagram.__init__(self, BODY_W, 168)

    def draw(self):
        T = 312.0
        x0, wbar = 64, 400
        sc = wbar / T
        # regions: VBI at p=0, vertical blank p in [0,64), overscan [64,72), display [72,312)
        top = 130
        for row, K in enumerate((1, 2, 3, 4)):
            y = top - row * 33
            c = self.canv
            self.text(x0 - 8, y + 8, "%dx" % K, 9, "Sans-Bold", BLUE, "r")
            c.setFillColor(colors.HexColor("#D9DCF5"))
            c.rect(x0, y, 64 * sc, 18, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#EEF0FD"))
            c.rect(x0 + 64 * sc, y, 8 * sc, 18, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#C9D8FF"))
            c.rect(x0 + 72 * sc, y, (T - 72) * sc, 18, fill=1, stroke=0)
            c.setStrokeColor(BLUE)
            c.setLineWidth(0.8)
            c.rect(x0, y, wbar, 18, fill=0, stroke=1)
            # VBI
            self.canv.setFillColor(RED)
            self.canv.rect(x0 - 1, y - 3, 3, 24, fill=1, stroke=0)
            self.text(x0 + 4, y + 5.5, "VBI", 7, "Sans-Bold", RED)
            self.canv.setFillColor(RED)
            self.canv.rect(x0 + wbar - 2, y - 3, 3, 24, fill=1, stroke=0)
            for (tg, ac) in self.DATA[K]:
                xt = x0 + tg * sc
                xa = x0 + ac * sc
                c.setStrokeColor(GREY)
                c.setLineWidth(0.7)
                c.setDash(1, 1.5)
                c.line(xt, y - 2, xt, y + 20)
                c.setDash()
                c.setFillColor(BLUE)
                c.rect(xa - 1.4, y - 3, 2.8, 24, fill=1, stroke=0)
                self.text(xa + 3, y + 5.5, "DLI", 7, "Sans-Bold", BLUE)
            rec = "record 1: VBI" + ("".join("  +  record %d: DLI" % (j + 2) for j in range(K - 1)))
            self.text(x0 + wbar + 6, y + 6, "", 6)
        # scale
        ys = top - 4 * 33 + 22
        c = self.canv
        self.text(x0, ys - 6, "linea 248 (VBI)", 6.8, "Sans", GREY)
        self.text(x0 + 64 * sc, ys - 6, "linea 0", 6.8, "Sans", GREY, "c")
        self.text(x0 + 72 * sc + 4, ys - 6, "inizio dell'immagine (linea 8)", 6.8, "Sans", GREY)
        self.text(x0 + wbar, ys - 6, "VBI successivo", 6.8, "Sans", GREY, "r")


class StreamLayout(Diagram):
    def __init__(self):
        Diagram.__init__(self, BODY_W, 214)

    def draw(self):
        c = self.canv
        W = self.width
        y, h = 162, 30
        segs = [
            ("campi\nfissi", 26, SAND),
            ("titolo\nautore\ncopyr.", 40, MINT),
            ("tabella\nregistri", 46, LILAC),
            ("flusso\nAUDF1", 52, PALE),
            ("flusso\nAUDC1", 46, PALE),
            ("flusso\nAUDF2", 58, PALE),
            ("...", 24, PALE),
            ("flusso\nAUDC4", 44, PALE),
        ]
        sc = (W - 4) / sum(s_[1] for s_ in segs)
        x = 2
        pos = []
        for name, wd, col in segs:
            wp = wd * sc
            self.box(x, y, wp, h, fill=col, lines=name.split("\n"), size=6.6, r=1.5)
            pos.append((x, wp))
            x += wp
        self.text(2, y + h + 10, "song.bin", 8.5, "Mono", BLUE)
        self.text(W - 2, y + h + 10, "(i registri costanti non hanno un flusso)", 7, "Sans-Italic", GREY, "r")
        # the table points to a stream
        tx, tw = pos[2]
        sx, sw = pos[4]
        c.setStrokeColor(GREEN)
        c.setLineWidth(1)
        c.setDash(2, 2)
        c.line(tx + tw / 2, y, tx + tw / 2, y - 12)
        c.line(tx + tw / 2, y - 12, sx + sw / 2, y - 12)
        c.setDash()
        self.arrow(sx + sw / 2, y - 12, sx + sw / 2, y - 1, color=GREEN, width=1, head=4)
        self.text((tx + tw / 2 + sx + sw / 2) / 2, y - 22, "offset del flusso (dall'inizio del file)", 6.8,
                  "Sans-Italic", GREEN, "c")
        # the first 13 bytes
        self.text(2, 124, "i primi 13 byte", 7.4, "Sans-Bold", BLUE)
        d = [("0", "AUDCTL"), ("1", "Hz"), ("2-3", "quadri"), ("4", "K"), ("5", "AUDCTL 2"), ("6", "POKEY"),
             ("7-12", "registri dei VU")]
        x = 2
        for off, nm in d:
            wd = 78 if off == "7-12" else (52 if off in ("2-3", "5") else 46)
            self.box(x, 98, wd, 22, fill=SAND, lines=[nm], size=6.8, r=1.5)
            self.text(x + wd / 2, 88, off, 6.6, "Mono", GREY, "c")
            x += wd + 3
        # one entry of the table
        self.text(2, 70, "una voce della tabella dei registri (3 byte)", 7.4, "Sans-Bold", BLUE)
        self.box(2, 44, 60, 22, fill=LILAC, lines=["tipo"], size=6.8, r=1.5)
        self.box(65, 44, 110, 22, fill=LILAC, lines=["valore  |  offset (basso)"], size=6.6, r=1.5)
        self.box(178, 44, 90, 22, fill=LILAC, lines=["0  |  offset (alto)"], size=6.6, r=1.5)
        self.text(2, 32, "tipo 0 = costante (il valore \u00e8 nel secondo byte); tipo 1 = flusso LZ "
                  "(secondo e terzo byte = offset a 16 bit)", 6.8, "Sans", GREY)


class LzTokens(Diagram):
    def __init__(self):
        Diagram.__init__(self, BODY_W, 148)

    def bits(self, x, y, labels, cw=22, h=15, fills=None, size=7):
        for i, lb in enumerate(labels):
            f = (fills[i] if fills else PALE)
            self.box(x + i * cw, y, cw, h, fill=f, lines=[lb], size=size, r=0)

    def draw(self):
        c = self.canv
        self.text(0, 134, "gruppo = 1 byte di flag + fino a 8 token", 8.3, "Sans-Bold", BLUE)
        self.text(0, 118, "flag (bit 7 per primo)", 7.2, "Sans", GREY)
        self.bits(0, 100, ["7", "6", "5", "4", "3", "2", "1", "0"])
        self.bits(0, 85, ["1", "0", "1", "1", "0", "1", "0", "0"], fills=[MINT, ROSE, MINT, MINT, ROSE, MINT, ROSE, ROSE])
        self.text(190, 90, "1 = letterale (1 byte)    0 = match (2 byte)", 7.4, "Sans", INK)
        # tokens
        self.text(0, 70, "token (nell'ordine dei flag)", 7.2, "Sans", GREY)
        x = 0
        order = [("L", 1), ("M", 2), ("L", 1), ("L", 1), ("M", 2), ("L", 1), ("M", 2), ("M", 2)]
        for i, (kind, nb) in enumerate(order):
            wd = 34 * nb
            col = MINT if kind == "L" else ROSE
            self.box(x, 48, wd - 2, 16, fill=col, lines=["valore" if kind == "L" else "offset | lung."],
                     size=6.4, r=1)
            self.text(x + (wd - 2) / 2, 40, str(i + 1), 6.2, "Mono", GREY, "c")
            x += wd
        # match bytes
        self.text(0, 30, "match: 2 byte", 7.6, "Sans-Bold", BLUE)
        self.text(0, 22, "byte 1", 7, "Mono", GREY)
        self.bits(46, 18, ["o7", "o6", "o5", "o4", "o3", "o2", "o1", "o0"], fills=[ROSE] * 8)
        self.text(236, 22, "byte 2", 7, "Mono", GREY)
        self.bits(282, 18, ["o8", "l6", "l5", "l4", "l3", "l2", "l1", "l0"], fills=[ROSE] + [LILAC] * 7)
        self.text(0, 6, "offset = o8..o0 (1..512, 0 vale 512): quanti valori indietro nella storia di QUEL registro;"
                  "  lunghezza = l6..l0 + 3 (da 3 a 130).", 6.8, "Sans", GREY)


class MemoryMaps(Diagram):
    def __init__(self):
        Diagram.__init__(self, BODY_W, 262)

    def column(self, x, w, title, regions):
        self.text(x + w / 2, 250, title, 8.6, "Sans-Bold", BLUE, "c")
        y = 244
        for name, h, fill, sub in regions:
            y -= h
            self.box(x, y, w, h, fill=fill, lines=[name] + ([sub] if sub else []), size=6.9, r=1)
        return y

    def draw(self):
        w = (self.width - 24) / 2
        a = [
            ("$C000-$FFFF   ROM del sistema (I/O $D000-$D7FF)", 26, colors.HexColor("#E2E4EF"), ""),
            ("$BC20-$BFFF   schermo e display list (OS)", 22, SAND, ""),
            ("font: 1 KB sul confine di 1 KB", 20, MINT, "(nei 2 KB riservati, __RESERVED_MEMORY__)"),
            ("2 KB riservati in cima alla RAM", 14, colors.HexColor("#F3F4FA"), ""),
            ("stack software e heap di cc65", 18, colors.HexColor("#F3F4FA"), ""),
            ("BSS: buffer circolari 16 × 512 byte (8,4 KB)", 28, LILAC, "variabili del player e della schermata"),
            ("RODATA: song.bin + font.bin", 28, PALE, "stream LZ, font C64 (1 KB)"),
            ("CODE: player, schermata, libreria cc65", 36, PALE, ""),
            ("$0000-$1FFF   OS, pagina zero, stack, DOS", 26, colors.HexColor("#E2E4EF"), "il programma parte a $2000"),
        ]
        b = [
            ("$FFFA-$FFFF   vettori (NMI: hook per i DLI)", 18, ROSE, "in RAM, scritti da cc65"),
            ("$E400-$FFF9   RAM sotto la ROM", 22, colors.HexColor("#F3F4FA"), "wrapper degli interrupt"),
            ("$E000-$E3FF   CHARGEN in RAM = il font", 28, MINT, "copiato dalla ROM da cc65: si modifica sul posto"),
            ("$D800-$DFFF   RAM nascosta", 16, colors.HexColor("#F3F4FA"), ""),
            ("$D000-$D7FF   I/O (ANTIC, POKEY, PIA...)", 22, colors.HexColor("#E2E4EF"), ""),
            ("schermo e display list (sotto il programma)", 18, SAND, "spostati da cc65"),
            ("BSS: buffer circolari 16 × 512 byte (8,4 KB)", 28, LILAC, "variabili del player e della schermata"),
            ("RODATA: song.bin + font.bin", 28, PALE, "stream LZ, font C64 (1 KB)"),
            ("CODE: player, schermata, libreria cc65", 36, PALE, ""),
            ("$0000-$1FFF   OS, pagina zero, stack", 26, colors.HexColor("#E2E4EF"), "ROM dell'OS spenta durante il programma"),
        ]
        self.column(0, w, "400 / 800  (target atari)", a)
        self.column(w + 24, w, "XL / XE  (target atarixl)", b)


class Layouts(Diagram):
    def __init__(self):
        Diagram.__init__(self, BODY_W, 150)

    def draw(self):
        c = self.canv
        half = self.width / 2
        for k, (title, boxes) in enumerate((
            ("3 canali a 8 bit  (AUDCTL $00 o $01)",
             [("CH1", "voce 1", PALE), ("CH2", "voce 2", PALE), ("CH3", "voce 3", PALE), ("CH4", "libero", colors.HexColor("#E2E4EF"))]),
            ("voce 1 sulla coppia a 16 bit  (AUDCTL $50 o $51)",
             [("CH1+CH2", "voce 1  16 bit\n1,79 MHz", MINT), None, ("CH3", "voce 2", PALE), ("CH4", "voce 3", PALE)]))):
            x0 = k * half + 4
            self.text(x0, 134, title, 7.4, "Sans-Bold", BLUE)
            x = x0
            bw = 52
            for b in boxes:
                if b is None:
                    continue
                name, desc, fill = b
                wd = bw * 2 + 3 if name == "CH1+CH2" else bw
                self.box(x, 62, wd, 52, fill=fill, lines=[name] + desc.split("\n"), size=7.2, r=2)
                x += wd + 3
            self.text(x0, 50, "AUDF = divisore, AUDC = distorsione + volume", 6.6, "Sans", GREY)
        self.text(4, 32, "Ogni voce SID va su un canale (o su una coppia): la scelta si fa per ciascun SID sul brano intero,",
                  7, "Sans", INK)
        self.text(4, 21, "calcolando l'errore di intonazione medio di ogni disposizione (8 candidate, tabella 4.6).",
                  7, "Sans", INK)


class GlyphGrid(Diagram):
    """8x8 glyphs: items = [(label, [8 bytes])]"""
    def __init__(self, items, px=3.6, per_row=8, title=None):
        self.items = items
        self.px = px
        self.per_row = per_row
        self.cellw = 8 * px + 22
        rows = (len(items) + per_row - 1) // per_row
        self.cellh = 8 * px + 17
        Diagram.__init__(self, BODY_W, rows * self.cellh + (12 if title else 2))
        self.title = title

    def draw(self):
        c = self.canv
        top = self.height - (12 if self.title else 0)
        if self.title:
            self.text(0, self.height - 8, self.title, 7.8, "Sans-Bold", BLUE)
        for i, (label, rows) in enumerate(self.items):
            r, cc = divmod(i, self.per_row)
            x = cc * self.cellw + 2
            y = top - (r + 1) * self.cellh + 14
            c.setFillColor(colors.HexColor("#1F2A82"))
            c.rect(x - 1, y - 1, 8 * self.px + 2, 8 * self.px + 2, fill=1, stroke=0)
            for ry, b in enumerate(rows):
                for bx in range(8):
                    if b & (0x80 >> bx):
                        c.setFillColor(LBLUE)
                        c.rect(x + bx * self.px, y + (7 - ry) * self.px, self.px, self.px, fill=1, stroke=0)
            self.text(x + 4 * self.px, y - 9.5, label, 6.4, "Mono", GREY, "c")
