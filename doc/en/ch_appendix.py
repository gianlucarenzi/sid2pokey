# ch_appendix.py - appendices
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, section, sub, table)
import pdflib
from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak


def appendix(S, title, need_mm=None):
    """New page, or only if less than need_mm are left (so short appendices share a page)."""
    if need_mm is None:
        S.append(pdflib.PageBreak())
    else:
        S.append(CondPageBreak(need_mm * mm))
    S.append(pdflib.Heading(title, pdflib.ST["h1"]))


def build(S):
    pdflib.NUM.ch += 0
    # appendices are numbered A, B, ...
    appendix(S, "Appendix A — Addresses used")
    P(S, "The operating system and hardware locations that the code touches.")
    table(S, [
        ["Name", "Address", "Use"],
        ["VDSLST", "$0200", "the OS DLI vector (the player points it to the handler, for K &gt; 1)"],
        ["SDLSTL", "$0230", "shadow of the display list pointer: it is scanned to set the DLI bits"],
        ["ATRACT", "$004D", "attract mode counter, cleared at every frame"],
        ["SAVMSC", "$0058", "pointer to screen memory"],
        ["RTCLOK", "$0012-$0014", "frame clock; the low byte ($14) marks “one frame”"],
        ["MEMTOP", "$02E5", "last free RAM address (400/800: base of the font block)"],
        ["COLOR1, COLOR2, COLOR4", "$02C5, $02C6, $02C8", "color shadows: text, background, border"],
        ["CRSINH", "$02F0", "1 = cursor hidden"],
        ["CHBAS", "$02F4", "character set page (shadow)"],
        ["CH", "$02FC", "last key pressed, $FF = none"],
        ["AUDF1 … AUDC4", "$D200-$D207", "the four channels of POKEY 1"],
        ["AUDCTL", "$D208", "audio control of POKEY 1"],
        ["RANDOM, SKCTL, SKSTAT", "$D20A, $D20F", "random number; keyboard control (write) / status (read, bit 2 = key down)"],
        ["POKEY 2", "$D210-$D217, $D218", "the same registers of the second POKEY (AUDCTL at $D218); RANDOM at $D21A, SKCTL at $D21F"],
        ["PALNT", "$D014", "GTIA: $01 on PAL, $0F on NTSC"],
        ["NMIEN, NMIST", "$D40E, $D40F", "NMI enable (bit 7 DLI, bit 6 VBI); status (bit 7 = it was a DLI)"],
        ["SETVBV, XITVBV", "$E45C, $E462", "installs a VBI vector; exit from a VBI (on the XL/XE: the symbols of atari.inc)"],
        ["NMI vector", "$FFFA", "RAM on the XL/XE with the ROM off: the player puts nmi_dli there"],
    ], [38, 34, 98], mono_cols=(0, 1), font=7.8, keep=False, caption="Table A.1 — System addresses.")

    appendix(S, "Appendix B — Commands")
    sub(S, "Project Makefile")
    table(S, [
        ["Target", "Effect"],
        ["make", "builds <font face=\"Mono\">sid2pokey.com</font> for the chosen target (<font face=\"Mono\">MACH</font>)"],
        ["make build", "as above and launches atari800 with <font face=\"Mono\">-stereo</font>"],
        ["make song.bin", "converts <font face=\"Mono\">$(SID)</font> (if the SID is newer than the stream)"],
        ["make font.bin", "builds the C64 font from <font face=\"Mono\">$(CHARGEN)</font> (empty if the ROM is not there)"],
        ["make atr", "copies the program to <font face=\"Mono\">$(ATRFOLDER)/build</font> and creates the ATR image with <font face=\"Mono\">dir2atr</font> (MyPicoDos 4.06)"],
        ["make clean", "removes the generated files (including font.bin and the two PC programs)"],
    ], [38, 132], mono_cols=(0,), font=7.9)
    table(S, [
        ["Variable", "Default", "Meaning"],
        ["MACH", "atarixl", "<font face=\"Mono\">atarixl</font> (XL/XE) or <font face=\"Mono\">atari</font> (400/800)"],
        ["SID", "Commando.sid (Rob Hubbard)", "the file to convert, in $(HOME)/Music/C64Music/..."],
        ["SONG", "1", "the tune in the file"],
        ["DURATION", "60", "seconds to convert"],
        ["VIDEO", "pal", "<font face=\"Mono\">pal</font> or <font face=\"Mono\">ntsc</font>"],
        ["CHARGEN", "/usr/lib/vice/C64/chargen-901225-01.bin", "C64 character ROM"],
        ["STEREO", "-stereo", "atari800 option for the second POKEY (empty to remove it)"],
        ["EMULATOR", "atari800", "the emulator used by <font face=\"Mono\">make build</font>"],
        ["ROM", "~/ATARI/ATARIXL.ROM", "OS ROM for the emulator (with MACH=atari: ATARIOSB.ROM)"],
        ["ATRFOLDER", "~/ATARI/ATR", "working folder of <font face=\"Mono\">make atr</font>"],
    ], [28, 66, 76], mono_cols=(0,), font=7.8)
    code(S, "# convert and try, one SID, XL/XE (make always rebuilds the .com)\n"
            "make -B song.bin SID=tune.sid DURATION=90 && make && make build\n\n"
            "# a 400/800 (48 KB): stream under about 20 KB\n"
            "make -B song.bin SID=tune.sid DURATION=60 && make MACH=atari && make build MACH=atari\n\n"
            "# the tests and the skeleton\n"
            "sh tests/opcodes/run.sh     # 6502 core against the VICE reference (vice_ref.txt)\n"
            "cd skeleton && make SID=tune.sid", title="Recipes")

    appendix(S, "Appendix C — Repository map", 85)
    table(S, [
        ["Path", "Contents"],
        ["tools/sidconv.c", "the converter (PSID reader, C64 environment, SID model, POKEY mapping, LZ encoder)"],
        ["tools/cpu6502.h", "the 6502 core (PC only)"],
        ["tools/mkfont.c", "C64 character ROM → Atari font"],
        ["sp-common.asm", "the player: decoding, VBI, DLI, two POKEYs, stereo detection"],
        ["sp-data.asm, sp-font.asm", "embed <font face=\"Mono\">song.bin</font> and <font face=\"Mono\">font.bin</font>"],
        ["sid2pokey.c", "the screen: font, boxes, VU meters, keyboard, DLI preparation"],
        ["Makefile", "building everything"],
        ["tests/opcodes/", "the core test against VICE: generator, driver, reference, scripts"],
        ["skeleton/", "the minimal player, with dump converter and Makefile"],
        ["doc/", "this document: <font face=\"Mono\">build_pdf.py</font> regenerates it (listings read from the sources)"],
        ["sid2gumby/", "the original project (GPL 3): the “run the tune on the Atari” case"],
        ["README.md", "the project summary, with the measurements"],
    ], [42, 128], mono_cols=(0,), font=7.9)

    appendix(S, "Appendix D — Formulas", 125)
    table(S, [
        ["Quantity", "Formula"],
        ["frequency of a SID voice", "f = Fn × clock_SID / 2<super>24</super>"],
        ["8-bit POKEY divider", "N = clk / (2 f) − 1;  clk = CPU/28 (64 kHz) or CPU/114 (15 kHz)"],
        ["16-bit POKEY divider, 1.79 MHz", "N = CPU / (2 f) − 7"],
        ["noise", "like the wave, with f → 8 f"],
        ["pitch error", "1200 × log<sub>2</sub>(f_obtained / f_wanted) cents; + 1200 for each folded octave"],
        ["POKEY volume", "(level × volume_SID + 127) / 255, 0-15"],
        ["frame frequency", "CPU / (lines × 114)"],
        ["play frequency (CIA)", "clock_SID / (latch + 1)"],
        ["records per frame", "K = round(f_play / f_atari), 1-4"],
        ["play call for a record", "floor(((n + j/K) / f_atari) × f_play)"],
        ["position of a DLI", "(248 + j × lines / K) mod lines, j = 1 … K−1"],
        ["envelope, attack", "255 × period cycles (period 9…31251)"],
        ["envelope, decay", "one step every p ticks, p = 1, 2, 4, 8, 16, 30 below 255, 93, 54, 26, 14, 6"],
        ["source position of a match", "(pos − offset) mod 512"],
        ["size of the header", "109 + 3 × N bytes (N = 8 or 16)"],
        ["address of the font (400/800)", "(MEMTOP + 1 − $400) &amp; $FC00"],
    ], [58, 112], font=7.9)

    appendix(S, "Appendix E — Glossary", 125)
    table(S, [
        ["Term", "Meaning"],
        ["ADSR", "Attack, Decay, Sustain, Release: the SID volume envelope"],
        ["ANTIC", "the Atari video chip: it reads the display list and the character set"],
        ["AUDF / AUDC / AUDCTL", "divider, control and general control of the POKEY"],
        ["CIA", "the C64 timer chip; its timer A sets the pace of tunes not tied to the frame"],
        ["DLI", "Display List Interrupt: an NMI at a chosen scanline, requested by a bit of the display list"],
        ["HIRAM", "bit 1 of C64 port $01: when it is 1 the KERNAL is visible"],
        ["HVSC", "High Voltage SID Collection: the archive of SID tunes"],
        ["init / play", "the two routines of a SID tune: init prepares a tune; play is called every frame"],
        ["KERNAL", "the C64 operating system (here a minimal fake ROM)"],
        ["multispeed", "a tune with several play calls per frame (2x, 3x, 4x)"],
        ["NMI", "non-maskable interrupt: the Atari VBI and DLI use it"],
        ["PSID / RSID", "the SID file formats; RSID requires a real C64"],
        ["record", "the values of all the POKEY registers for one instant (one play call)"],
        ["VBI", "Vertical Blank Interrupt: once per frame, at the start of the vertical blank interval"],
        ["VU meter", "level indicator: here one bar per voice"],
    ], [42, 128], font=7.9)

    appendix(S, "Appendix F — References and licenses", 100)
    bullets(S, [
        "<b>cc65</b>: compiler, assembler and linker for the 6502; the documentation of the <i>atari</i> and "
        "<i>atarixl</i> targets describes the reserved memory, ROM banking and the interrupts.",
        "<b>atari800</b>: the emulator used for all the tests; the POKEY recorder (<font face=\"Mono\">-pokeyrec</font>) "
        "was the basis of the verification.",
        "<b>VICE</b> (x64sc): the reference for the undocumented opcodes and the source of the C64 character ROM.",
        "<b>reSID</b>: the model from which the SID envelope generator used here derives (rate counter "
        "and exponential counter).",
        "<b>sid2gumby</b> (Ivo van Poorten, GPL 3): the project this one started from, in the "
        "<font face=\"Mono\">sid2gumby/</font> folder.",
        "<b>HVSC</b>: the collection of tunes on which the measurements were made.",
        "For the Atari hardware details the <i>Altirra Hardware Reference Manual</i>, the <i>Atari 400/800 "
        "Technical Reference Notes</i> and the <i>Operating System User's Manual</i> are useful.",
    ])
    callout(S, "WARNING", "The C64 character ROM belongs to Commodore. The repository does not contain it, nor the font "
                          "derived from it: <font face=\"Mono\">font.bin</font> is built locally from a copy "
                          "you already have (for example the one distributed with VICE). The screenshots in this document show "
                          "the result; they do not contain the ROM.")
