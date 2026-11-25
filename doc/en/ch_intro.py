# ch_intro.py - cover, how to read, chapters 1 (overview) and 2 (hardware)
import datetime
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import NextPageTemplate, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

import diagrams as D
from pdflib import (BLUE, BODY_W, INK, MARGIN_X, ST, bullets, callout, chapter, code, esc, figure, flow, m,
                    numbered, P, section, sub, table)


def git_short():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=D.__file__.rsplit("/", 2)[0],
                                       text=True).strip()
    except Exception:
        return "?"


def cover(S):
    ind = MARGIN_X
    S.append(Spacer(1, 38 * mm))
    S.append(Paragraph("SID → POKEY", ParagraphStyle("t1", fontName="Sans-Bold", fontSize=44, leading=48,
                                                          textColor=colors.white, leftIndent=ind)))
    S.append(Spacer(1, 4 * mm))
    S.append(Paragraph("Building a SID player for the Atari 8-bit",
                       ParagraphStyle("t2", fontName="Sans-Bold", fontSize=20, leading=25,
                                      textColor=colors.HexColor("#C9CEFF"), leftIndent=ind)))
    S.append(Spacer(1, 8 * mm))
    S.append(Paragraph("From the PSID file to the screen: the converter, the stream format, the 6502 player,<br/>"
                       "the interface with the C64 font and the VU meters, and a skeleton to start from.",
                       ParagraphStyle("t3", fontName="Sans", fontSize=11.2, leading=16, textColor=colors.white,
                                      leftIndent=ind, rightIndent=ind)))
    S.append(Spacer(1, 11 * mm))
    from pdflib import IMG
    import os
    from reportlab.platypus import Image, Table, TableStyle
    from PIL import Image as PI
    path = os.path.join(IMG, "ui_dual_xe.png")
    w, h = PI.open(path).size
    wp = 112 * mm
    im = Image(path, width=wp, height=wp * h / w)
    t = Table([[im]], colWidths=[wp + 6])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, BLUE), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    t.hAlign = "LEFT"
    S.append(Table([[None, t]], colWidths=[ind, wp + 10], style=TableStyle(
        [("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)])))
    S.append(Spacer(1, 30 * mm))
    meta = ParagraphStyle("meta", fontName="Sans", fontSize=8.6, leading=12.5, textColor=INK, leftIndent=ind,
                          rightIndent=ind)
    S.append(Paragraph("<b>Repository</b>  github.com/gianlucarenzi/sid2pokey  —  commit %s, plus the skeleton "
                       "and this documentation<br/><b>Document version</b>  %s<br/>"
                       "<b>Target</b>  Atari 400, 800, 600XL, 800XL, 130XE (PAL and NTSC), with one or two POKEYs<br/>"
                       "<b>Tools</b>  cc65 2.19, gcc, make, Python 3, atari800 7.x (VICE only for the C64 character "
                       "ROM and for the tests)" % (git_short(), datetime.date.today().isoformat()), meta))
    S.append(NextPageTemplate("body"))
    S.append(PageBreak())


def toc(S):
    S.append(Paragraph("Contents", ST["h1x"]))
    t = TableOfContents()
    t.levelStyles = [ST["toc1"], ST["toc2"]]
    t.dotsMinLevel = 0
    S.append(t)
    S.append(PageBreak())


def how_to_read(S):
    S.append(Paragraph("How to read this document", ST["h1"]))
    P(S, "This document explains how to build a player for SID files on an 8-bit Atari, and it does so by following "
         "the <b>sid2pokey</b> project: a PC converter (<font face=\"Mono\">tools/sidconv</font>), a compressed "
         "stream format, a 6502 assembly player that runs in interrupts and a C64-style screen. "
         "Every number and every table comes from a measurement or from the code; when something has not been "
         "verified, I say so.")
    P(S, "Chapters 1-3 give the context, chapters 4-7 describe the components one by one, chapter 8 "
         "contains the <b>skeleton</b>: the smallest possible player, with all the files, to build and run in order "
         "to understand the mechanism before moving on to the full one. Chapters 9 and 10 collect the verifications "
         "and the pitfalls that are easiest to fall into.")
    sub(S, "Boxes")
    callout(S, "NOTE", "Background information: it helps you understand, not act.")
    callout(S, "TIP", "An approach that has given good results.")
    callout(S, "WARNING", "A limit or a choice that has consequences: worth knowing before you start.")
    callout(S, "PITFALL", "A real mistake that is easy to make: the symptom, the cause and the fix.")
    callout(S, "VERIFIED", "Something that was tried on an emulator or compared against an independent reference, "
                           "with the result.")
    sub(S, "Conventions")
    table(S, [
        ["Notation", "Meaning"],
        ["$D200", "hexadecimal number (as in 6502 assembly)"],
        ["AUDF1 … AUDC4", "the eight POKEY audio registers, in this order (index 0-7)"],
        ["POKEY 1 / POKEY 2", "the chip at $D200 and the second chip of the stereo board, at $D210"],
        ["SID 1 / SID 2", "the first and the second SID chip of a two-SID tune"],
        ["record", "the POKEY register values for one instant of the music (one call of <font face=\"Mono\">play</font>)"],
        ["frame", "a video frame: 49.86 Hz on PAL, 59.92 Hz on NTSC; it contains from 1 to 4 records"],
        ["K", "number of records per frame (1 = normal, 2-4 = multispeed tunes)"],
        ["400/800, XL/XE", "the two build targets: <font face=\"Mono\">atari</font> and <font face=\"Mono\">atarixl</font>"],
    ], [38, 132], mono_cols=(0,))


def ch1(S):
    chapter(S, "Overview")
    section(S, "The problem: a SID file contains no audio")
    P(S, "A <b>SID</b> file (PSID format, or RSID for tunes that require a complete C64) contains a piece of "
         "<b>6502 code</b> and its data: the music is played by that code, which the C64 runs once per video "
         "frame (50 Hz on PAL), writing to the 25 registers of the SID chip, which synthesizes the sound. The file "
         "holds the load address, that of the <font face=\"Mono\">init</font> routine (it prepares a tune) and "
         "that of the <font face=\"Mono\">play</font> routine (to be called every frame), plus title, author and "
         "copyright. There is no waveform to play back.")
    P(S, "The Atari has a different chip, the <b>POKEY</b>: four 8-bit channels with a frequency divider, "
         "polynomial distortion and a 4-bit volume. It has no envelopes, no filters, no triangle or sawtooth "
         "waveforms. A SID player for the Atari must therefore <b>translate</b> what the SID does into what the "
         "POKEY can do, and do it within the time of one video frame on a 1.79 MHz CPU.")
    section(S, "Two approaches")
    P(S, "There are two ways to tackle the problem. The first is to bring the tune's code to the Atari and "
         "run it there; the second is to run it on the PC just once, record what it writes to the SID "
         "and bring to the Atari only the translated result.")
    table(S, [
        ["", "A. Run the SID code on the Atari", "B. Convert on the PC (this project)"],
        ["Idea", "The tune is loaded as it is; the writes to $D400 are redirected to an area of memory; "
                 "a routine at the VBI translates those values into AUDF/AUDC.",
         "A 6502 emulator on the PC runs <font face=\"Mono\">init</font> and <font face=\"Mono\">play</font>, "
         "records the SID registers at every call and translates them once and for all."],
        ["Work per tune", "Each tune must be relocated and its writes to $D400 patched by hand or with dedicated "
                          "tools (this is the sid2gumby approach).",
         "None: a single command converts any tune the emulator can run."],
        ["Memory on the Atari", "The original code (up to tens of KB) plus the translator and the frequency tables.",
         "Only the compressed stream: about 1.5 KB per minute for a typical tune."],
        ["Translation quality", "Limited by the CPU time available in one frame; the ADSR has to be "
                                "approximated in a few instructions.",
         "Unconstrained: the translation costs time only on the PC (exact ADSR, channel choice by minimum error)."],
        ["Interactivity", "The tune can react to events (rare in SIDs).",
         "None: you play what was recorded. A tune is as long as you convert it."],
        ["Unsupported tunes", "Those that cannot be relocated.",
         "Those that play back voice samples ($D418), are driven by NMI, or require a whole C64."],
    ], [30, 70, 70], font=7.9)
    callout(S, "NOTE", "The repository also contains <font face=\"Mono\">sid2gumby/</font>, Ivo van "
                       "Poorten's project (GPL 3) from which this one was born: it is a good example of approach A. "
                       "sid2pokey follows approach B.")
    section(S, "The architecture", need=118)
    flow(S, D.Architecture(), "Figure 1.1 — The data flow: the heavy work is done on the PC, the Atari receives a "
                              "compressed stream and decodes it while playing.")
    numbered(S, [
        "<b>6502 emulator.</b> Loads the tune into 64 KB of memory, calls <font face=\"Mono\">init</font> and then "
        "<font face=\"Mono\">play</font> at the right rate, and intercepts the writes to the SID registers.",
        "<b>SID model.</b> For each voice it computes frequency, waveform and volume, with the ADSR envelope of the real chip.",
        "<b>POKEY mapping.</b> Chooses which channels to put the three voices on (eight candidate layouts, the one "
        "with the lowest pitch error wins) and computes dividers and distortion.",
        "<b>Compression.</b> Writes a stream containing one LZ stream for each POKEY register that changes, and reads "
        "it back with the same algorithm as the player to make sure it is identical.",
        "<b>6502 player.</b> A routine at the vertical blank (and, for multispeed tunes, at the display "
        "list interrupts) decodes the stream and writes the POKEY registers.",
        "<b>Screen.</b> A C program draws title, author and one VU meter per voice, reading the values the "
        "player has just decoded.",
    ])
    section(S, "What you get", need=90)
    table(S, [
        ["Feature", "Status"],
        ["One SID (3 voices) on one POKEY", "complete"],
        ["Two SIDs (PSID v3) on two POKEYs (stereo board), one SID per chip", "complete; the third SID is ignored with a warning"],
        ["Multispeed tunes (2x, 3x, 4x per frame)", "complete up to 4x; beyond that, resampled to 4"],
        ["Tunes with their own IRQ handler (<font face=\"Mono\">play</font> = 0)", "complete if the handler is an IRQ"],
        ["16-bit pair at 1.79 MHz for the bass notes", "automatic, for each chip"],
        ["SID ADSR envelope (rate counter + exponential)", "as in reSID, without the ADSR delay bug"],
        ["Stream compression", "about 6 times, compared with a delta format"],
        ["Undocumented 6502 opcodes, even the unstable ones", "all except the 12 JAMs, compared against VICE"],
        ["C64 screen with title, author, VU meters, time", "400/800 and XL/XE"],
        ["Filter, ring modulation, sync, pulse modulation", "not modeled"],
        ["Digital samples ($D418), NMI-driven tunes, BASIC", "not supported: the converter reports it"],
    ], [118, 52])
    section(S, "Requirements and quick start")
    table(S, [
        ["Tool", "What it is for", "Notes"],
        ["cc65 (cl65, ca65, ld65)", "builds the player and the screen", "tested with 2.19"],
        ["gcc, make", "build <font face=\"Mono\">sidconv</font> and <font face=\"Mono\">mkfont</font> for the PC", ""],
        ["Python 3", "skeleton (<font face=\"Mono\">dump2raw.py</font>), opcode tests", "standard library only"],
        ["atari800 7.x", "testing the player; the POKEY recorder", "needs the OS ROMs (400/800 and XL/XE)"],
        ["A SID collection (HVSC)", "the tunes to convert", ""],
        ["C64 character ROM", "the font of the screen", "VICE: <font face=\"Mono\">chargen-901225-01.bin</font>; optional"],
        ["VICE x64sc", "only to regenerate the reference for the opcode test", "optional"],
    ], [42, 78, 50], font=7.9)
    P(S, "From the project folder, to convert a tune and watch it play on an emulated XL/XE with two POKEYs:")
    code(S, "make -B song.bin SID=~/Music/C64Music/MUSICIANS/H/Hubbard_Rob/Commando.sid DURATION=60\n"
            "make            # atarixl target (XL/XE): produces sid2pokey.com\n"
            "make build      # launches atari800 with -stereo\n"
            "\n"
            "make MACH=atari # the same for a 400/800 (48 KB)", title="Quick start")
    callout(S, "WARNING", "<font face=\"Mono\">make</font> does not reconvert <font face=\"Mono\">song.bin</font> when "
                          "only <font face=\"Mono\">SONG</font>, <font face=\"Mono\">DURATION</font> or "
                          "<font face=\"Mono\">VIDEO</font> change: it depends only on the SID file. Use "
                          "<font face=\"Mono\">make -B song.bin ...</font> to force it.")
    callout(S, "WARNING", "The C64 character ROM belongs to Commodore: the font is built locally "
                          "(<font face=\"Mono\">font.bin</font>) and is not part of the repository. Without the ROM "
                          "the build continues with the Atari font (chapter 7).")


def ch2(S):
    chapter(S, "The hardware: SID and POKEY")
    section(S, "The SID chip")
    P(S, "The SID (6581/8580) has three independent voices, a filter and a master volume. Each voice has a "
         "24-bit phase accumulator: at every clock cycle the 16-bit value of the frequency registers is added to it, "
         "and the frequency produced is")
    P(S, "<b>f = Fn × clock / 2<super>24</super></b>,  with clock = 985,248 Hz (PAL) or 1,022,727 Hz (NTSC).")
    P(S, "The waveform is chosen with four bits of the control register (triangle, sawtooth, pulse, "
         "noise, also combined). Each voice has an 8-bit ADSR envelope; the noise is a shift register "
         "that advances at the rate of the accumulator.")
    table(S, [
        ["Register", "Voice 1", "Voice 2", "Voice 3", "Contents"],
        ["frequency (lo, hi)", "$D400-01", "$D407-08", "$D40E-0F", "Fn, 16 bits"],
        ["pulse width", "$D402-03", "$D409-0A", "$D410-11", "12 bits"],
        ["control", "$D404", "$D40B", "$D412", "bit 7 noise, 6 pulse, 5 sawtooth, 4 triangle, 3 test, 0 gate"],
        ["attack / decay", "$D405", "$D40C", "$D413", "AD: attack (high), decay (low)"],
        ["sustain / release", "$D406", "$D40D", "$D414", "SR: sustain level (high), release (low)"],
        ["global", "$D415-18", "", "", "filter, resonance, mode and <b>volume</b> ($D418, bits 0-3)"],
    ], [34, 20, 20, 20, 76], mono_cols=(1, 2, 3))
    section(S, "The POKEY chip")
    P(S, "The POKEY has four channels. Each has an 8-bit divider (AUDFn) and a control register (AUDCn) with "
         "three distortion bits, a “volume only” bit and four volume bits. The AUDCTL register ($D208) "
         "selects the clock of the channels and lets you <b>join two channels into a 16-bit divider</b>.")
    table(S, [
        ["Clock base", "Frequency (PAL)", "Divider", "Output frequency", "Useful range"],
        ["64 kHz (CPU/28)", "63,337 Hz", "N + 1, N ≤ 255", "f = clk / (2 (N+1))", "124 Hz to 31 kHz"],
        ["15 kHz (CPU/114)", "15,556 Hz", "N + 1, N ≤ 255", "f = clk / (2 (N+1))", "30 Hz to 7.8 kHz"],
        ["1.79 MHz, 16-bit", "1,773,447 Hz", "N + 7, N ≤ 65535", "f = clk / (2 (N+7))", "13.5 Hz to 126 kHz"],
    ], [34, 30, 33, 41, 32])
    P(S, "Two constraints drive all the later choices: at 64 kHz the low notes (below about 124 Hz) "
         "cannot be reached, and at 15 kHz the high notes have a resolution of a semitone or worse. The 16-bit pair at "
         "1.79 MHz solves both problems, but uses up two channels.")
    table(S, [
        ["AUDCTL", "Effect"],
        ["bit 0", "all channels on the 15 kHz clock instead of 64 kHz"],
        ["bit 1 / bit 2", "high-pass filter on channel 1 (clocked by channel 3) / on channel 2 (by channel 4)"],
        ["bit 3", "channel 4 linked to 3: 16-bit divider, output on 4"],
        ["bit 4", "channel 2 linked to 1: 16-bit divider, output on 2 (AUDF1 = low part, AUDF2 = high part)"],
        ["bit 5 / bit 6", "channel 3 / channel 1 on the CPU clock (1.79 MHz)"],
        ["bit 7", "9-bit polynomial instead of 17-bit"],
    ], [28, 142], mono_cols=(0,), caption="Table 2.1 — The AUDCTL register. The project uses bits 0, 4 and 6: $00, $01, $50 and $51.")
    table(S, [
        ["AUDCn bits 7-5", "Distortion", "Use in the project"],
        ["000", "5- and 17-bit polynomials", ""],
        ["100", "17-bit polynomial (noise)", "SID noise waveform: $8x"],
        ["101", "pure square wave", "all the other waveforms: $Ax"],
        ["110", "4-bit polynomial", "not used: it changes the pitch (period 15)"],
    ], [34, 66, 70], mono_cols=(0,), caption="Table 2.2 — Distortion (selection). Bit 4 is “volume only”, bits 3-0 are the volume.")
    section(S, "Comparison and what must be approximated")
    table(S, [
        ["", "SID", "POKEY", "How the converter handles it"],
        ["Voices / channels", "3 voices", "4 channels (or 2 at 16 bits)", "8 candidate layouts per chip"],
        ["Waveforms", "triangle, sawtooth, pulse, noise", "square or noise", "noise → $8x, the rest → $Ax"],
        ["Volume", "8-bit ADSR × 4-bit volume", "4 bits per channel", "level × volume / 255, rounded"],
        ["Pitch", "24-bit accumulator", "8- or 16-bit divider", "nearest divider; octaves folded if needed"],
        ["Filter, ring, sync, PWM", "yes", "no", "ignored"],
        ["Digital samples", "via volume ($D418)", "volume-only mode only", "not supported"],
    ], [28, 44, 40, 58], font=7.9)
    section(S, "Timing constants")
    table(S, [
        ["Quantity", "PAL", "NTSC", "Notes"],
        ["Atari CPU/POKEY clock", "1,773,447 Hz", "1,789,773 Hz", ""],
        ["lines per frame", "312", "262", "114 cycles per line"],
        ["Atari frame rate", "49.861 Hz", "59.923 Hz", "clock / (lines × 114)"],
        ["SID clock", "985,248 Hz", "1,022,727 Hz", ""],
        ["<font face=\"Mono\">play</font> rate on the C64", "50.125 Hz", "59.826 Hz", "clock / (312 × 63), clock / (263 × 65)"],
    ], [58, 32, 32, 48])
    callout(S, "WARNING", "A tune written for PAL (50.125 Hz) played on an NTSC Atari (59.92 Hz) runs 20% too "
                          "fast. The converter resamples to real time (option <font face=\"Mono\">-p</font>) "
                          "and the program warns if the stream and the machine do not have the same frequency.")
    section(S, "The second POKEY")
    P(S, "Stereo boards for the Atari add a second POKEY at <b>$D210-$D21F</b> (the same registers as the first chip, 16 bytes higher: "
         "AUDF1 at $D210, AUDCTL at $D218). Without the board those addresses are a <b>mirror</b> of the first chip: a "
         "write at $D210 ends up in AUDF1 of POKEY 1. For this reason the player never writes to the second POKEY "
         "without having checked that it is present (chapter 6).")
    figure(S, "ui_dual_xe.png", "Figure 2.1 — A two-SID tune on the emulated XE with two POKEYs: two groups of "
                                "three VU meters, one per chip.", width_mm=96)
