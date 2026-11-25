# ch_psid_conv.py - chapters 3 (PSID) and 4 (sidconv)
import os
import textwrap

import diagrams as D
from pdflib import (HERE, bullets, callout, chapter, code, excerpt, figure, flow, m, numbered, P, section, sub,
                    table, read_text)

MONO = 'face="Mono"'


def mm_(s):
    return '<font face="Mono">%s</font>' % s


def verbose_example(name, only=None):
    """a saved 'sidconv -v' output, with the long lines wrapped"""
    out = []
    for l in open(os.path.join(HERE, "examples", name)).read().rstrip().split("\n"):
        l = l.replace("doc/examples/commando.bin", "song.bin").replace("doc/examples/double.bin", "song.bin")
        if only and not any(l.startswith(k) or k in l for k in only):
            continue
        out.extend(textwrap.wrap(l, 100, subsequent_indent="    ", drop_whitespace=False) or [""])
    return "\n".join(out)


def build(S):
    ch3(S)
    ch4(S)


def ch3(S):
    chapter(S, "The PSID format and the HVSC tunes")
    section(S, "The header")
    P(S, "A PSID file is a header followed by the data. The header is 118 bytes long in version 1 and 124 from "
         "version 2 on; the <i>dataOffset</i> field says where the data begin. All numbers are big endian, unlike the "
         "6502. The table lists the fields and which ones the converter uses.")
    table(S, [
        ["Offset", "Size", "Field", "Use in sidconv"],
        ["$00", "4", "“PSID” or “RSID”", "RSID: warning (it is meant for a complete C64), but it is tried anyway"],
        ["$04", "2", "version (1-4)", "decides whether the v2/v3/v4 fields exist"],
        ["$06", "2", "dataOffset ($76 or $7C)", "start of the data"],
        ["$08", "2", "loadAddress", "0 = the first two data bytes (little endian) are the address"],
        ["$0A", "2", "initAddress", "0 = tune driven by BASIC: not supported"],
        ["$0C", "2", "playAddress", "0 = the tune installs its own IRQ (section 4.2)"],
        ["$0E", "2", "songs", "number of tunes in the file"],
        ["$10", "2", "startSong", "default tune (option <font face=\"Mono\">-s</font>)"],
        ["$12", "4", "speed", "one bit per tune: 0 = VBI, 1 = CIA timer (section 4.3)"],
        ["$16", "32", "title", "shown on the screen"],
        ["$36", "32", "author", "shown on the screen"],
        ["$56", "32", "copyright (“released”)", "shown on the screen"],
        ["$76", "2", "flags (v2+)", "bits 2-3: clock (01 PAL, 10 NTSC, 11 both); the others are not used"],
        ["$7A", "1", "second SID (v3)", "address = $D000 + value × 16 (section 3.3)"],
        ["$7B", "1", "third SID (v4)", "as above; the third SID is ignored"],
    ], [14, 11, 50, 95], mono_cols=(0,), caption="Table 3.1 — The fields of the PSID header.", font=7.8)
    callout(S, "NOTE", "The header strings are ASCII or Latin-1, at most 32 characters long and padded with zeros. "
                       "The converter copies them into the stream (96 bytes) and the screen draws them: characters "
                       "outside the range $20-$7A become a question mark.")
    section(S, "The play rate")
    P(S, "The <i>speed</i> bit of the chosen tune only says whether the code is called once per video frame "
         "(bit 0) or by a timer (bit 1); the actual rate is chosen by the tune itself, by programming timer A of "
         "CIA 1 (registers $DC04/$DC05) or the VIC raster interrupt. For this reason the converter does not trust the "
         "bit alone: it runs <font face=\"Mono\">init</font> and then looks at what it has programmed (Table 4.3). "
         "<b>Multispeed</b> tunes are those with a play rate that is a multiple of the frame rate: 100, 150, 200 Hz.")
    section(S, "Two and three SIDs")
    P(S, "Version 3 of the header adds the address of a second SID, version 4 that of a third. The address is "
         "one byte, in units of 16 bytes above $D000: the valid values are $42-$7E (even) and $E0-$FE (even), that is "
         "$D420-$D7E0 and $DE00-$DFE0. With several chips, each one answers only to its own 32 bytes; with a single SID "
         "the chip answers to all of $D400-$D7FF (mirrored every 32 bytes), as on the C64.")
    table(S, [
        ["In the HVSC (56,665 files)", "Files", "Notes"],
        ["version 2 header", "56,401", "a single SID"],
        ["version 3 header", "240", "up to two SIDs"],
        ["version 4 header", "24", "up to three SIDs: all of them with three SIDs"],
        ["with a second SID", "264", "$D420: 159, $D500: 85, $DE00: 14, $D440: 3, $D4A0, $D520, $D5A0: one each"],
        ["with a third SID", "24", "converted using only the first two"],
    ], [52, 22, 96], caption="Table 3.2 — The multi-SID tunes of the collection used for testing.")
    callout(S, "WARNING", "Nine voices (three SIDs) do not fit in the eight channels of two POKEYs. The converter "
                          "uses the first two SIDs and says so: <font face=\"Mono\">warning: the tune has 3 SIDs; only "
                          "the first two are converted</font>.")
    section(S, "Tunes that cannot be converted")
    P(S, "On a sample of 4370 HVSC tunes (one file out of every twelve in the <font face=\"Mono\">MUSICIANS</font> "
         "folder) 4292 are converted, that is 98.2%. The other 78 split as follows; every rejection comes with a "
         "message that says why.")
    table(S, [
        ["Reason", "Tunes", "Why it cannot be done"],
        ["driven by an NMI handler", "28", "they usually play digital samples with the CIA 2 timer and the NMI"],
        ["the main loop does the work", "26", "<font face=\"Mono\">play</font> = 0 without an IRQ: a whole C64 would be needed"],
        ["BASIC (init = 0)", "19", "they start from a BASIC program"],
        ["call the KERNAL", "2", "the emulated KERNAL contains only the interrupt exits"],
        ["do not return", "2", "the routine does not finish within 2 million instructions"],
        ["JAM", "1", "the opcode that locks up the CPU"],
    ], [52, 18, 100], caption="Table 3.3 — The 78 tunes rejected out of 4370. Other tunes convert but stay silent "
                              "(usually digital samples): the converter warns about it.")


def ch4(S):
    chapter(S, "The sidconv converter")
    P(S, "<font face=\"Mono\">tools/sidconv.c</font> is a C program of about 1300 lines plus "
         "<font face=\"Mono\">tools/cpu6502.h</font>, the 6502 core. It takes a SID file and writes a stream "
         "(<font face=\"Mono\">song.bin</font>) that the player reads. The sections that follow go through the "
         "four stages of Figure 1.1.")
    section(S, "The 6502 emulator")
    P(S, "The core executes one instruction at a time without counting cycles: it only serves to run "
         "<font face=\"Mono\">init</font> and <font face=\"Mono\">play</font> and to observe what they write to the SID. "
         "It has two safety limits (50 million instructions for <font face=\"Mono\">init</font>, 2 million for "
         "<font face=\"Mono\">play</font>) so that it never gets stuck in a loop.")
    table(S, [
        ["Group", "Opcodes", "Notes"],
        ["official", "151", "ADC and SBC also in decimal mode; indirect JMP with the page-crossing bug"],
        ["undocumented, stable", "84", "LAX, SAX, SLO, RLA, SRE, RRA, DCP, ISC, ANC, ALR, SBX, SBC $EB, 2- and 3-byte NOPs"],
        ["undocumented, unstable", "9", "ARR, XAA, LXA, AHX (2 forms), TAS, SHX, SHY, LAS: VICE model"],
        ["JAM", "12", "not implemented: the real CPU locks up, the converter stops with a message"],
    ], [42, 18, 110], caption="Table 4.1 — The opcodes of the core (256 in all).")
    callout(S, "VERIFIED", "The <font face=\"Mono\">tests/opcodes</font> test builds a C64 program with 588 cases of "
                           "the unstable opcodes (registers, flags, stack pointer, behavior at page crossings, "
                           "ARR in decimal mode too), runs it in the core and in VICE x64sc 3.10 and compares every "
                           "result: all identical. The “magic” constants are those of VICE: "
                           "XAA uses $EF, LXA uses $EE. On real chips they vary.")
    callout(S, "NOTE", "The core runs only on the PC. The code that runs on the Atari uses only documented 6502 "
                       "instructions (<font face=\"Mono\">cl65</font> compiles for <font face=\"Mono\">--cpu 6502</font>) "
                       "and is the same on the 400/800 and on the XL/XE: they all have a 6502C, and the XL/XE have no "
                       "extra opcodes (those belong to the 65C02/65816 of accelerator boards).")

    section(S, "A minimal C64 around the core", need=88)
    P(S, "The tune expects a C64: the memory, a bit of I/O, the KERNAL vectors. The converter emulates just "
         "what is needed.")
    table(S, [
        ["Element", "How it is emulated"],
        ["memory", "64 KB flat, zeroed; the tune is loaded at its declared address"],
        ["CPU port ($01)", "initial value given by the init address: &lt; $A000 → $37; &lt; $D000 → $36; "
                           "≥ $E000 → $35; otherwise $34. Bit 1 (HIRAM) decides whether the KERNAL is visible"],
        ["KERNAL", "a minimal ROM at $E000-$FFFF, visible above the tune's RAM when HIRAM = 1"],
        ["IRQ exits", "$EA31 and $EA34 → $EA81; $EA7B → $EA7E (reads $DC0D); $EA81: PLA TAY PLA TAX PLA RTI; $EA87: RTS"],
        ["every other KERNAL byte", "the illegal opcode $02: if the tune executes it, the message says <i>calls the KERNAL at $xxxx, not emulated</i>"],
        ["vectors", "$0314 = $EA31 (IRQ), $0316 = $FE66 (BRK), $0318 = $FE47 (NMI); in ROM NMI $FE43, RESET $FCE2, IRQ $FF48"],
        ["SID", "writes to $D400-$D418 are recorded; $D41B returns a pseudo-random value, $D41C zero"],
        ["VIC", "$D012 increases by 7 on every read (so that raster waits terminate); $D019 = $81 if the raster IRQ is enabled"],
        ["CIA 1", "the timer A latch ($DC04/05) and the mask ($DC0D) are recorded; $DC00/01 = $FF (no keys)"],
    ], [38, 132], font=7.8, caption="Table 4.2 — The emulated C64 environment.")
    sub(S, "Tunes with their own IRQ handler (play = 0)")
    P(S, "If the play address is zero, after <font face=\"Mono\">init</font> the tune has installed a handler: in "
         "vector $0314 if the KERNAL is visible, in $FFFE if RAM covers the ROM. The converter calls it once per "
         "frame, as a C64 would: it pushes the return address and the status register onto the stack and, with the "
         "KERNAL visible, A, X and Y as well, as the stub at $FF48 does. If <font face=\"Mono\">init</font> does not "
         "return but has installed a handler, the program is assumed to be parked in a main loop and conversion "
         "continues with the handler alone.")
    section(S, "Timing")
    table(S, [
        ["Condition", "Play rate"],
        ["play ≠ 0, speed bit = 0 (VBI)", "50.125 Hz (PAL) or 59.826 Hz (NTSC)"],
        ["play ≠ 0, speed bit = 1, timer programmed by init", "SID clock / (latch + 1)"],
        ["play ≠ 0, speed bit = 1, timer not programmed", "60 Hz"],
        ["play = 0, CIA 1 timer A IRQ enabled", "SID clock / (latch + 1)"],
        ["play = 0, raster IRQ enabled", "same as the VBI"],
    ], [92, 78], caption="Table 4.3 — How the rate at which the tune must be called is derived.")
    P(S, "The converter calls <font face=\"Mono\">play</font> at that rate for the requested time and then "
         "<b>resamples in real time</b> onto the frames of the Atari: for record <i>j</i> of frame <i>n</i> it uses "
         "call number <font face=\"Mono\">floor(((n + j/K) / f_atari) × f_play)</font>. In this way the tempo "
         "of the tune does not change with the video standard. <b>K</b> is the rounded ratio, limited to 1-4: a 2x "
         "tune has two records per frame; beyond 4x some calls are lost.")
    section(S, "The voice model")
    P(S, "After each call the converter reads the SID registers and computes three things for each voice.")
    bullets(S, [
        "<b>The frequency</b>: Fn × clock / 2<super>24</super>. A zero Fn, the test bit or a missing waveform "
        "make the voice silent.",
        "<b>The waveform</b>: noise (bit 7) or “other”; on the POKEY, “other” becomes a square wave.",
        "<b>The volume</b>: the envelope level (0-255) times the master volume (0-15), reduced to 4 bits with "
        "<font face=\"Mono\">(level × volume + 127) / 255</font>.",
    ])
    sub(S, "The envelope as the chip does it")
    P(S, "The envelope generator of the SID has an 8-bit counter and a rate counter that advances on every clock "
         "cycle. When the rate counter reaches the period of the state (attack, decay or release) "
         "the envelope can take a step. In attack it rises by one at every tick (linear ramp); in decay and "
         "release it falls by one every <i>p</i> ticks, where <i>p</i> grows as the level decreases. This is what "
         "gives SID sounds their fast decay followed by a long tail.")
    table(S, [
        ["The level drops below", "255", "93", "54", "26", "14", "6"],
        ["the step happens every (ticks)", "1", "2", "4", "8", "16", "30"],
    ], [52, 20, 20, 20, 20, 20, 18], align="LCCCCCC", caption="Table 4.4 — The exponential counter.")
    rates = [(9, 2.3, 2, 7.0, 6), (32, 8.3, 8, 24.6, 24), (63, 16.3, 16, 48.4, 48), (95, 24.7, 24, 73.0, 72),
             (149, 38.6, 38, 114.4, 114), (220, 56.9, 56, 168.9, 168), (267, 69.1, 68, 204.9, 204),
             (313, 81.1, 80, 240.2, 240), (392, 101.5, 100, 300.8, 300), (977, 252.9, 250, 749.8, 750),
             (1954, 505.8, 500, 1499.4, 1500), (3126, 809.1, 800, 2398.7, 2400), (3907, 1011.2, 1000, 2997.9, 3000),
             (11720, 3033.3, 3000, 8993.1, 9000), (19532, 5055.3, 5000, 14987.3, 15000),
             (31251, 8088.4, 8000, 23979.5, 24000)]

    def fmt(v):
        return ("%.1f" % v) if v < 1000 else ("%.0f" % v)
    rows = [["Index", "Period (cycles)", "Attack 0→255: model", "datasheet", "Release 255→ 0: model", "datasheet"]]
    for i, (per, a, ad, r, rd) in enumerate(rates):
        rows.append([str(i), str(per), fmt(a) + " ms", str(ad) + " ms", fmt(r) + " ms", str(rd) + " ms"])
    table(S, rows, [16, 28, 38, 22, 44, 22], align="CRRRRR", font=7.6, keep=False,
          caption="Table 4.5 — The sixteen envelope rates: model times and datasheet values of the SID.")
    callout(S, "VERIFIED", "The model was compared with the datasheet times for all sixteen rates: attack and "
                           "release are within 4% (within 2% from rate 4 up). Rate 0 gives 2.3 ms against the "
                           "2 ms of the datasheet because the datasheet rounds: "
                           "255 × 9 cycles are 2.33 ms. At rate 9 the level reaches half after 126 ms out of 750 "
                           "(17% of the time: a linear ramp would use 50%).")
    callout(S, "WARNING", "The chip flaw known as the <i>ADSR delay bug</i> (a rate counter past the new "
                          "period must first wrap around, with a delay of up to 32 ms) is not modeled.")
    code(S, excerpt("tools/sidconv.c", "static void voice_step(", "env_step(e, s * 17);") + "\n\t\t}\n\t}\n}",
         title="tools/sidconv.c — the envelope step for one play call")
    section(S, "The mapping onto the POKEY", need=60)
    sub(S, "The frequency: the nearest divider")
    P(S, "For a voice at frequency <i>f</i> and a channel with clock <i>clk</i> the divider is "
         "<i>N + d = clk / (2 f)</i>, with d = 1 for the 8-bit channels and d = 7 for the 16-bit pair at 1.79 MHz. "
         "It is rounded, clamped to 0-255 (or 0-65535) and the error is computed in cents. If the note is too "
         "low for the divider, the frequency is <b>doubled</b> until it fits: the note sounds a few octaves higher, "
         "and in the cost it counts 1200 cents per octave.")
    code(S, excerpt("tools/sidconv.c", "static quant_t quantize(", "return q;") + "\n}",
         title="tools/sidconv.c — quantize(): the divider and the error")
    callout(S, "NOTE", "For <b>noise</b> the divider uses 8 times the frequency: the shift register of the SID advances "
                       "at 16 times the note frequency, while the POKEY polynomial advances once per period of the "
                       "divider, that is at twice the frequency of the equivalent square wave.")
    sub(S, "The channel layouts")
    P(S, "The three voices of a SID can be placed on the four channels of a POKEY in many ways. The converter tries "
         "eight and keeps the one with the lowest average error, weighted by volume (noise does not count: it has no pitch).")
    flow(S, D.Layouts(), "Figure 4.1 — Two of the layouts: three 8-bit channels, or one voice on the 16-bit pair.")
    table(S, [
        ["#", "Layout", "AUDCTL", "Channels"],
        ["1", "three 8-bit channels, 64 kHz clock", "$00", "voice 1→1, 2→2, 3→3; channel 4 is free"],
        ["2", "three 8-bit channels, 15 kHz clock", "$01", "as above"],
        ["3-4", "voice 1 on the 16-bit pair; the others at 64 kHz (3) or 15 kHz (4)", "$50 / $51", "voice 1 → 1+2; voice 2 → 3; voice 3 → 4"],
        ["5-6", "voice 2 on the 16-bit pair", "$50 / $51", "voice 2 → 1+2; voice 1 → 3; voice 3 → 4"],
        ["7-8", "voice 3 on the 16-bit pair", "$50 / $51", "voice 3 → 1+2; voice 1 → 3; voice 2 → 4"],
    ], [12, 78, 22, 58], mono_cols=(2,), caption="Table 4.6 — The eight candidate layouts (option <font face=\"Mono\">-m</font> to restrict them).")
    P(S, "With the 16-bit pair channel 1 stays silent (AUDC1 = 0) and the divider uses AUDF1 as the low part and AUDF2 as "
         "the high part; volume and distortion are in AUDC2. With bits 6 and 4 of AUDCTL the clock is 1.79 MHz; "
         "bit 0 selects 15 kHz for the 8-bit channels.")
    code(S, verbose_example("commando_verbose.txt"),
         title="Example: sidconv -v on Commando by Rob Hubbard (average error of each layout, in cents)",
         size=6.9)
    callout(S, "NOTE", "With three 64 kHz channels the average error is 726 cents: the basses, below 124 Hz, "
                       "are folded by octaves. The chosen layout (voice 1 on the 16-bit pair, the others at "
                       "15 kHz) brings it down to 9 cents.")
    section(S, "Two SIDs, two POKEYs")
    P(S, "With a second SID the converter repeats the choice for each chip: <b>SID 1 goes to POKEY 1</b> (registers 0-7) "
         "and <b>SID 2 to POKEY 2</b> (registers 8-15), each with its own layout and its own AUDCTL. One may use "
         "the 16-bit pair and the other three channels. The option <font face=\"Mono\">-S 1</font> converts only the first.")
    code(S, verbose_example("double_verbose.txt", only=("PSID", "using", "frames")),
         title="Example: a two-SID tune (Double, by JVD and Udo Gorissen)", size=6.9)
    section(S, "Options and messages", need=100)
    table(S, [
        ["Option", "Meaning", "Default"],
        ["-o file", "output stream", "song.bin"],
        ["-s n", "tune in the file (from 1)", "the start tune of the file"],
        ["-t seconds", "duration to convert (a SID has no length)", "60"],
        ["-p pal|ntsc", "video standard of the target Atari", "pal"],
        ["-c pal|ntsc|auto", "clock the tune was written for", "auto (from the flags; otherwise PAL)"],
        ["-m auto|plain|bass16", "channel layout: all, only the 3-channel ones, only those with the 16-bit pair", "auto"],
        ["-k n", "records per frame, 1 to 4", "from the rate of the tune"],
        ["-S n", "SID chips to convert, 1 or 2", "all (at most 2)"],
        ["-d", "print the POKEY registers of every record (hex) on stdout", ""],
        ["-v", "print title, addresses, rate, layout errors", ""],
    ], [40, 94, 36], mono_cols=(0,), font=7.8, caption="Table 4.7 — The sidconv command line.")
    table(S, [
        ["Message", "Meaning"],
        ["warning: RSID files expect a real C64 environment", "it is tried anyway, but it may fail"],
        ["init address is 0: C64 BASIC tune, not supported", "the tune starts from a BASIC program"],
        ["play address is 0 and the tune is driven by an NMI handler", "digital sample player: not supported"],
        ["play address is 0 but init did not install an IRQ handler", "the main loop does everything: not supported"],
        ["the tune calls the KERNAL at $xxxx, which is not emulated", "it uses a KERNAL routine other than the IRQ exits"],
        ["JAM opcode $xx at $xxxx", "the real CPU would lock up here"],
        ["routine at $xxxx did not return", "beyond the instruction limit (probably an infinite loop)"],
        ["warning: the tune has 3 SIDs; only the first two are converted", "nine voices do not fit in eight channels"],
        ["warning: the converted tune is silent", "no sound: if there is an NMI, probably digital samples"],
        ["warning: stream larger than 20 KB", "does not fit in a 400/800 (an XL/XE holds about 24 KB)"],
        ["internal error: stream verification failed", "converter bug: the re-read stream does not match"],
    ], [86, 84], font=7.6, caption="Table 4.8 — The main messages.")
