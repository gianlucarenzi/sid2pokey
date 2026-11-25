# ch_stream_player.py - chapters 5 (the stream) and 6 (the 6502 player)
import os

import diagrams as D
from pdflib import (HERE, bullets, callout, chapter, code, excerpt, figure, flow, m, numbered, P, section, sub,
                    table)

REGNAMES = ["AUDF1", "AUDC1", "AUDF2", "AUDC2", "AUDF3", "AUDC3", "AUDF4", "AUDC4"]


def build(S):
    ch5(S)
    ch6(S)


def example_header():
    d = open(os.path.join(HERE, "examples", "commando.bin"), "rb").read()
    return d


def ch5(S):
    chapter(S, "The song.bin stream")
    P(S, "The stream is the only thing that goes from the PC to the Atari. It must be small (memory is scarce), easy to "
         "decode in a few cycles, and verifiable. The choice made is a <b>separate LZ stream for each POKEY "
         "register</b>: the AUDF1 values form one sequence, the AUDC1 values another, and so on. Within a "
         "sequence repetitions are very frequent (a vibrato, an envelope, a note that repeats in every "
         "bar), whereas mixing the registers together would hide them.")
    section(S, "Overview")
    flow(S, D.StreamLayout(), "Figure 5.1 — The file: a header of fixed fields, the three strings, the register table, "
                              "then the streams (registers that never change have none).")
    bullets(S, [
        "Each stream holds <b>one value per record</b>: once the streams of all the registers have been decoded you have "
        "the complete POKEY state for that instant.",
        "A video frame holds <b>K</b> consecutive records (K from 1 to 4): the VBI plays the first, the DLIs the others.",
        "Constant registers (typically: the unused channel 4, AUDC1 = 0 with the 16-bit pair) live only in the "
        "table: the value is there, and they cost no stream.",
        "At the end of the stream all the decoders are reset and the tune starts again: the first decode "
        "rewrites every register, so the loop is exact.",
    ])
    section(S, "The header", need=45)
    table(S, [
        ["Offset", "Bytes", "Contents"],
        ["0", "1", "AUDCTL of POKEY 1"],
        ["1", "1", "video rate it was built for: 50 or 60"],
        ["2-3", "2", "number of frames (little endian)"],
        ["4", "1", "records per frame, K"],
        ["5", "1", "AUDCTL of POKEY 2 (0 if there is only one POKEY)"],
        ["6", "1", "number of POKEYs: 1 or 2"],
        ["7-12", "6", "for each of the 6 voices, the register (0-15) that holds its volume in the low 4 bits, or $FF"],
        ["13-44", "32", "title (ASCII, zero-padded)"],
        ["45-76", "32", "author"],
        ["77-108", "32", "copyright"],
        ["109 …", "3 × N", "register table: N = 8 with one POKEY, 16 with two; for each register: type (0 constant, "
                              "1 stream), then the value or the 16-bit offset of the stream from the start of the file"],
    ], [20, 14, 136], mono_cols=(0,), keep=False, caption="Table 5.1 — The song.bin header: 109 + 3 N bytes.")
    d = example_header()
    vu = []
    for r in d[7:13]:
        vu.append("—" if r == 0xFF else "POKEY%d.%s" % (r // 8 + 1, REGNAMES[r % 8]))
    entries = []
    offs = []
    for r in range(8):
        t, a, b = d[109 + 3 * r:109 + 3 * r + 3]
        offs.append((a | b << 8) if t else None)
    ends = [o for o in offs if o is not None] + [len(d)]
    ends = sorted(ends)
    rows = [["Register", "Type", "Value or offset", "Stream bytes"]]
    for r in range(8):
        t, a, b = d[109 + 3 * r:109 + 3 * r + 3]
        if t == 0:
            rows.append([REGNAMES[r], "constant", "$%02X" % a, "—"])
        else:
            off = a | b << 8
            nxt = min(e for e in ends if e > off)
            rows.append([REGNAMES[r], "LZ stream", str(off), str(nxt - off)])
    sub(S, "A real example: Commando, 60 seconds")
    P(S, "The first bytes of <font face=\"Mono\">song.bin</font> for Commando by Rob Hubbard (one SID, "
         "AUDCTL $%02X): %d frames, K = %d, %d POKEY; the VU meters read registers %s. The title is “%s”."
         % (d[0], d[2] | d[3] << 8, d[4], d[6], ", ".join(vu[:3]), d[13:45].rstrip(b"\0").decode()))
    table(S, rows, [34, 34, 46, 56], mono_cols=(0,), align="LLRR", caption=
          "Table 5.2 — The register table of the Commando stream (offsets in bytes from the start of the file); "
          "the whole stream is %d bytes long." % len(d))
    section(S, "The LZ streams", need=70)
    P(S, "Each stream is a sequence of <b>groups</b>: a flag byte and up to eight tokens. The flags are read from bit 7 "
         "towards bit 0: <b>1 = literal</b> (one byte, the value itself), <b>0 = match</b> (two bytes).")
    flow(S, D.LzTokens(), "Figure 5.2 — A group: the flag byte and the tokens it describes.")
    P(S, "A match copies <b>3 to 130</b> values from the history of the same register, starting <b>1 to 512 values "
         "back</b>. Matches may overlap: a match with offset 1 and length 100 repeats the last value a hundred times, "
         "and this is how constant stretches are encoded. Here is how the sequence "
         "<font face=\"Mono\">5 5 5 5 7</font> is encoded and decoded:")
    table(S, [
        ["Step", "Flag", "Token (bytes)", "Output", "History after the step"],
        ["1", "1", "$05", "5", "5"],
        ["2", "0", "$01 $00  → offset 1, length 0 + 3 = 3", "5 5 5", "5 5 5 5"],
        ["3", "1", "$07", "7", "5 5 5 5 7"],
    ], [14, 12, 74, 26, 44], mono_cols=(2,), caption=
          "Table 5.3 — The stream for that stretch is <font face=\"Mono\">A0 05 01 00 07</font>: the flag byte "
          "$A0 = 1 0 1 + five unused bits.")
    callout(S, "NOTE", "A match with offset 0 means 512 back: in the two bytes the offset has 9 bits, so 0 represents "
                        "512 and 1 represents 1. The decoder computes the source position as "
                        "<font face=\"Mono\">(pos − offset) mod 512</font>.")
    code(S, excerpt("tools/sidconv.c", "static size_t lz_encode(", "dp[i] = best;") + "\n\t\tclen[i] = (short)bl;\n\t\tcoff[i] = (short)bestoff;\n\t}\n\t...",
         title="tools/sidconv.c — lz_encode(): optimal parsing (for each position the minimum cost of the tail)",
         size=6.9)
    P(S, "The cost in the model is 9 bits for a literal (1 of flag + 8) and 17 for a match (1 + 16): the dynamic "
         "programming starts from the end of the stream and for each position chooses between the literal and the match "
         "that minimizes the total cost. The encoder runs in under a tenth of a second for one minute of music.")
    section(S, "Why this format")
    P(S, "Before settling on the format, alternatives were measured on 31 tunes (45 seconds each), with a cost model: "
         "the raw values of each register or the differences between consecutive records, with windows of 256, 512 and "
         "1024 values. The choice fell on raw values with a window of 512.")
    table(S, [
        ["Scheme", "Bytes (31 tunes)", "Relative to the mask format"],
        ["mask + changed values (uncompressed)", "238,181", "100%"],
        ["LZ per register, raw values, window 256", "47,185", "19%"],
        ["LZ per register, raw values, window <b>512</b>", "<b>37,666</b>", "<b>15%</b>"],
        ["LZ per register, raw values, window 1024", "40,420", "16%"],
        ["LZ per register, differences, window 256", "47,887", "20%"],
        ["LZ per register, differences, window 512", "38,500", "16%"],
        ["LZ per register, differences, window 1024", "41,005", "17%"],
    ], [86, 34, 50], align="LRR", caption="Table 5.4 — Cost-model estimates (not the encoder's actual output).")
    bullets(S, [
        "<b>Raw values beat differences</b>: the decoder does not have to accumulate anything, and it is simpler.",
        "<b>512 is the compromise</b>: with 9 bits of offset, 7 bits remain for the length (up to 130); with larger "
        "windows the length gets shorter and the long stretches are lost.",
        "<b>One stream per register</b> lets each one repeat on its own: the notes change, the volume envelope does "
        "not.",
    ])
    table(S, [
        ["Measurement", "Result"],
        ["31 tunes, 45 s: mask format → LZ (actual output, exact ADSR)", "238,336 → 39,766 bytes (about 6 times)"],
        ["per-tune compression (linear ADSR, earlier measurement)", "from 3.8 to 13.3 times; median 6.7"],
        ["87 tunes, 60 s: stream size", "median 1.7 KB, 95th percentile 3.3 KB, maximum 9.5 KB"],
        ["Commando, 60 s", "2207 bytes (0.7 bytes per frame)"],
        ["4x tune, 5 minutes", "16 KB (about 1.1 bytes per record)"],
        ["two-SID tune (Double), 90 s", "7.4 KB (1.6 bytes per frame, 2 records per frame)"],
    ], [92, 78], font=7.9, caption="Table 5.5 — The sizes you get.")
    callout(S, "WARNING", "Compression depends on the tune: <i>Slanted</i> by Julian Jaymz (a two-SID tune) produces about 4.7 "
                          "bytes per frame, four times a typical tune, and on a 400/800 it holds only about 80 seconds.")
    section(S, "The built-in check")
    P(S, "After writing the stream, the converter <b>decodes it again</b> with the same steps as the player "
         "(flag register with sentinel bit, ring buffers of 512 values, source position "
         "<font face=\"Mono\">(pos − offset) mod 512</font>) and compares it with the original records. If even one value "
         "differs the file is not written and the program stops with <font face=\"Mono\">internal error</font>. "
         "This has never happened on the 4370 test tunes.")


def ch6(S):
    chapter(S, "The 6502 player")
    P(S, "The player is the file <font face=\"Mono\">sp-common.asm</font> (about 500 lines of ca65): it decodes the "
         "stream and writes the POKEY registers from the interrupts. The screen (chapter 7) is a C program that "
         "uses it through three functions and a few variables.")
    section(S, "The interface")
    table(S, [
        ["Symbol", "Direction", "Meaning"],
        ["initPlayer()", "C → asm", "silences the POKEYs, reads the header, detects the second POKEY, prepares the decoders"],
        ["startPlayer()", "C → asm", "installs the VBI (and for K &gt; 1 the DLI handler); from here on the music plays by itself"],
        ["stopPlayer()", "C → asm", "restores the OS vectors, silences, AUDCTL = 0"],
        ["play_k", "asm → C", "records per frame (K)"],
        ["play_chips", "asm → C", "POKEYs the stream is written for: 1 or 2"],
        ["have_stereo", "asm → C", "$80 if the second POKEY responds at $D210, otherwise 0"],
        ["outbuf[16]", "asm → C", "the values of the last decoded record, per register: the VU meters read them here"],
        ["play_frames, play_left", "asm → C", "frames in the stream, frames still to play (for the elapsed time)"],
    ], [38, 26, 106], mono_cols=(0,), font=7.9, caption="Table 6.1 — The player's functions and variables.")
    section(S, "Memory")
    table(S, [
        ["Zero page", "Bytes", "Use"],
        ["sptr", "2", "pointer to the compressed stream of the register being decoded"],
        ["wp, rp", "2 + 2", "write and read pointers into the ring buffer (the low byte is always 0)"],
        ["tmp, tmp2, tmp3", "3", "temporaries"],
        ["ri, reg", "2", "index into the register list, register being processed"],
    ], [38, 20, 112], mono_cols=(0,), font=7.9)
    table(S, [
        ["Variables and buffers (BSS)", "Bytes", "Use"],
        ["ring", "8447", "16 ring buffers of 512 values + 255 bytes to align them to the page"],
        ["start_lo/hi, st_lo/hi", "64", "start and current pointer of the stream of each register (16 + 16 + 16 + 16)"],
        ["fl, cnt, srcl, srch, rhi", "80", "flag register, values left in the match, source position, buffer page"],
        ["outbuf, reglist", "33", "the 16 values of the record; list of the registers that have a stream (+ terminator)"],
        ["other", "16", "K, number of POKEYs, stereo flag, saved vectors, counters"],
    ], [50, 20, 100], mono_cols=(0,), font=7.9, align="LRL",
          caption="Table 6.2 — About 8.6 KB of RAM, almost all of it buffers. With a single POKEY half would be enough: "
                  "today there are always 16 buffers.")
    section(S, "Decoding", need=80)
    P(S, "For each record the player walks the list of registers that have a stream and decodes <b>one value</b> from each. "
         "The values end up in <font face=\"Mono\">outbuf</font> and in the register's ring buffer; at the end, all "
         "together, they go to the POKEY registers. Writing everything in one burst makes the channels and the "
         "two halves of a 16-bit pair change at the same instant.")
    code(S, excerpt("sp-common.asm", "; X = register.  Decode its next value", "jmp @copy"),
         title="sp-common.asm — decode: one value of a register (X = register)", size=6.9)
    callout(S, "NOTE", "The flag register uses a <b>sentinel bit</b>: after reading the flag byte, "
                        "<font face=\"Mono\">sec; rol a</font> puts the first flag in the carry and a 1 at the bottom. Each "
                        "following flag is read with <font face=\"Mono\">asl</font>; when the result is zero, "
                        "the byte is used up and another one is loaded. No counter is needed.")
    section(S, "The vertical blank and the tune loop")
    P(S, "The player runs in the <b>deferred vertical blank</b> (vector 7 of <font face=\"Mono\">SETVBV</font>): the "
         "operating system first does its own work (clock, colors, keyboard) and then calls our code, which "
         "ends with a jump to <font face=\"Mono\">XITVBV</font>. At the start of each frame the counter of the "
         "frames left is checked; at zero the decoders are reset and the tune starts again.")
    code(S, excerpt("sp-common.asm", "; Deferred VBI: first record of the frame.", "jmp XITVBV"),
         title="sp-common.asm — the VBI (vbim, for K > 1, also enables the DLIs)", size=6.9)
    section(S, "Multispeed tunes: the DLIs", need=95)
    P(S, "A 2x, 3x or 4x tune calls <font face=\"Mono\">play</font> several times per frame; the Atari has only one VBI "
         "per frame. The other records are played from <b>display list interrupts</b> (DLI), spread at equal distances "
         "along the frame. POKEY is not a solution: its timers use the dividers of the channels that are needed to "
         "play the sound.")
    flow(S, D.FrameTimeline(), "Figure 6.1 — A PAL frame (312 lines) from one VBI to the next, for K from 1 to 4: the VBI plays the "
                               "first record, the DLIs (blue) the others; the dashed lines are the ideal positions.")
    P(S, "The C program searches the system's display list (as it is: text mode, 24 rows) for the instructions whose "
         "last scanline is closest to the points that divide the frame into K equal parts starting from the VBI, and "
         "sets the DLI bit on them. At the end it restores them.")
    table(S, [
        ["Standard", "K", "DLI", "Ideal point (line)", "Chosen instruction", "Scanline", "Error"],
        ["PAL", "2", "1", "92", "text row 7", "95", "3"],
        ["PAL", "3", "1", "40", "text row 0", "39", "1"],
        ["PAL", "3", "2", "144", "text row 13", "143", "1"],
        ["PAL", "4", "1", "14", "blank", "15", "1"],
        ["PAL", "4", "2", "92", "text row 7", "95", "3"],
        ["PAL", "4", "3", "170", "text row 16", "167", "3"],
        ["NTSC", "2", "1", "117", "text row 10", "119", "2"],
        ["NTSC", "3", "1", "73", "text row 4", "71", "2"],
        ["NTSC", "3", "2", "160", "text row 15", "159", "1"],
        ["NTSC", "4", "1", "51", "text row 1", "47", "4"],
        ["NTSC", "4", "2", "117", "text row 10", "119", "2"],
        ["NTSC", "4", "3", "182", "text row 18", "183", "1"],
    ], [20, 10, 12, 32, 42, 26, 28], align="LCCRLRR", font=7.8, keep=True,
          caption="Table 6.3 — Where the DLIs fall in the standard display list. The maximum error is 4 scanlines "
                  "(about 0.25 ms at 50 Hz): it cannot be heard.")
    code(S, excerpt("sid2pokey.c", "static void patchDisplayList(", "dli_ins[dli_n++] = ins_p[best];") + "\n\t}\n}",
         title="sid2pokey.c — patchDisplayList(): chooses the instructions that get the DLI", size=6.8)
    callout(S, "PITFALL", "<b>The DLIs must start only after the first VBI.</b> The records of a frame are always played in the "
                          "order VBI, DLI, DLI, …: if the first DLIs fire before the first VBI, the stream is still read "
                          "in order but out of phase, and the end of the stream no longer falls at the end of a frame: the "
                          "player reads bytes that are not data. For this reason NMIEN is not written in "
                          "<font face=\"Mono\">startPlayer</font>: the VBI (<font face=\"Mono\">vbim</font>) does it at every "
                          "frame. Moreover <font face=\"Mono\">SETVBV</font> puts NMIEN back to $40 and would turn off the "
                          "DLIs just enabled.")
    sub(S, "The direct NMI on the XL/XE")
    P(S, "On the XL/XE target cc65 keeps the OS ROM switched off and switches it back on, with a wrapper, for every "
         "interrupt. A DLI would go through it and the ROM would stay on for the whole handler: ANTIC would read the font "
         "from the ROM instead of the one in RAM for tens of scanlines (chapter 7, “The screen pitfalls”). The player "
         "therefore replaces the NMI vector in RAM "
         "($FFFA) with a handler of its own, which recognizes the DLI from bit 7 of NMIST and serves it without touching "
         "the ROM; the VBI goes to the original vector.")
    code(S, excerpt("sp-common.asm", "nmi_dli:", "@other:") + "\n\tjmp (old_nmi)",
         title="sp-common.asm — nmi_dli: the DLI served directly from the NMI vector (atarixl only)", size=6.9)
    section(S, "Two POKEYs", need=90)
    P(S, "With two POKEYs there are 16 registers: the first eight go to $D200, the others to $D210. The "
         "<font face=\"Mono\">putreg</font> function routes them and writes the second POKEY only if "
         "<font face=\"Mono\">have_stereo</font> has confirmed it.")
    callout(S, "PITFALL", "Without the stereo board, $D210-$D21F are a <b>mirror</b> of the first POKEY: writing register 8 "
                          "(AUDF1 of POKEY 2) overwrites AUDF1 of POKEY 1 and, writing AUDCTL 2 at $D218, also the "
                          "AUDCTL of the first. On a normal Atari a two-SID tune would play incorrectly, not just "
                          "with one chip missing.")
    P(S, "The detection relies on the RANDOM register ($D20A, $D21A). The player sets POKEY 2 running "
         "(<font face=\"Mono\">SKCTL = 3</font>) and <i>then</i> puts POKEY 1 in the initialization state "
         "(<font face=\"Mono\">SKCTL = 0</font>, the polynomial counters are stopped and RANDOM reads $FF), then reads "
         "RANDOM2 256 times:")
    table(S, [
        ["Situation", "What it reads at $D21A", "Outcome"],
        ["real stereo board", "values that change (POKEY 2 is running)", "second POKEY present"],
        ["Atari without a board", "always $FF: it is the mirror of POKEY 1, in initialization", "absent: only SID 1 is played"],
        ["atari800 with <font face=\"Mono\">-stereo</font>", "always $00: the emulator plays the second POKEY but does not implement its RANDOM",
         "present (constant other than $FF)"],
    ], [42, 82, 46], font=7.9, caption="Table 6.4 — The three cases the detection distinguishes.")
    code(S, excerpt("sp-common.asm", "detect_stereo:", "silence:", include_end=False).rstrip(),
         title="sp-common.asm — detect_stereo and putreg", size=6.9)
    callout(S, "WARNING", "The “constant other than $FF” case is a heuristic designed for atari800: I could not test it "
                          "on real hardware. On a real board RANDOM varies and the detection is the orthodox one.")
    section(S, "The two cc65 targets", need=80)
    table(S, [
        ["", "400/800 (<font face=\"Mono\">-t atari</font>)", "XL/XE (<font face=\"Mono\">-t atarixl</font>)"],
        ["OS ROM while the program runs", "always on", "off; switched back on by the wrappers for interrupts and OS calls"],
        ["SETVBV", "<font face=\"Mono\">$E45C</font> directly", "a wrapper (from <font face=\"Mono\">atari.inc</font>): never call $E45C"],
        ["The font", "in RAM, in a reserved block; CHBAS points to it", "the ROM font is already copied to $E000: it is modified in place"],
        ["DLI", "from the OS vector (VDSLST)", "from the NMI vector in RAM, without switching the ROM on"],
        ["Memory", "about 20 KB of stream", "about 24 KB of stream"],
        ["Compile-time defines", "<font face=\"Mono\">-DFONT_TOP</font> and reserved memory", "(<font face=\"Mono\">__ATARIXL__</font>, defined by the target)"],
    ], [42, 62, 66], font=7.8, caption="Table 6.5 — The differences between the two targets.")
    callout(S, "PITFALL", "Do not call <font face=\"Mono\">$E45C</font> directly on the atarixl target: the ROM is off and "
                          "there is RAM there. The program hangs at once (it happened on the first attempt: the emulator quit "
                          "after two and a half seconds). Use the <font face=\"Mono\">SETVBV</font> symbol from "
                          "<font face=\"Mono\">atari.inc</font>, which on atarixl is the wrapper.")
