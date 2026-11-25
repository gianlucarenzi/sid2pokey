# ch_skeleton_tests.py - chapters 8 (the skeleton), 9 (verification), 10 (pitfalls)
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, read_text, section, sub,
                    table)


def build(S):
    ch8(S)
    ch9(S)
    ch10(S)


def ch8(S):
    chapter(S, "The skeleton: the smallest player")
    P(S, "Before reading the full player it is worth building and running the smallest possible one. The "
         "<font face=\"Mono\">skeleton/</font> folder contains a player that uses only one POKEY, one record per frame and "
         "an uncompressed stream: all the ingredients are there (the converter, a format, an interrupt that writes the "
         "registers, a C program that installs it) and nothing else. You can read it in ten minutes and grow it "
         "one step at a time (section 8.8).")
    section(S, "What is there and what is not")
    table(S, [
        ["File", "Lines", "Role"],
        ["player.s", "~110", "the vertical blank routine: reads the stream and writes AUDF1…AUDC4"],
        ["data.s", "8", "embeds the stream in the binary (<font face=\"Mono\">.incbin</font>)"],
        ["main.c", "~22", "starts the player, waits for a key, stops it"],
        ["dump2raw.py", "~33", "turns the output of <font face=\"Mono\">sidconv -d</font> into the skeleton stream"],
        ["Makefile", "20", "converts, builds <font face=\"Mono\">player.com</font>"],
    ], [34, 18, 118], mono_cols=(0,), caption="Table 8.1 — The five files of the skeleton.")
    table(S, [
        ["The skeleton has", "It does not have (see the full project)"],
        ["one POKEY, three channels (<font face=\"Mono\">-m plain</font>)", "16-bit pairs, second POKEY (chapters 4 and 6)"],
        ["one record per frame (<font face=\"Mono\">-k 1</font>)", "multispeed tunes and DLI (chapter 6)"],
        ["mask + changed values stream, uncompressed", "per-register LZ streams (chapter 5)"],
        ["one line of text", "C64 font, VU meters, title and author (chapter 7)"],
        ["documented 6502 instructions; runs on 400/800 and XL/XE", "handling of the two targets, stereo detection"],
    ], [85, 85], font=7.9, caption="Table 8.2 — The scope of the skeleton.")
    section(S, "Step 1: the tools")
    P(S, "You need cc65 and a C compiler. The converter is built from the project root; from the skeleton folder "
         "<font face=\"Mono\">make</font> is enough, because it does that by itself.")
    code(S, "cd skeleton\ncl65 --version            # cc65 2.19 or similar\nmake -C .. tools/sidconv  # the converter (gcc)",
         title="Step 1")
    section(S, "Step 2: converting a tune")
    P(S, "<font face=\"Mono\">sidconv</font> with the <font face=\"Mono\">-d</font> option prints the POKEY registers of "
         "each record, in hexadecimal. For the skeleton you ask for a single chip (<font face=\"Mono\">-S 1</font>), the "
         "plain layout (<font face=\"Mono\">-m plain</font>) and one record per frame (<font face=\"Mono\">-k 1</font>, "
         "multispeed tunes are reduced).")
    code(S, "../tools/sidconv -m plain -S 1 -k 1 -t 60 -d -o song.bin tune.sid > dump.txt", title="Step 2")
    code(S, open(__import__("os").path.join(__import__("pdflib").HERE, "examples", "dump_excerpt.txt")).read().rstrip(),
         title="An excerpt of dump.txt (Commando): frame number, then AUDF1 AUDC1 AUDF2 AUDC2 AUDF3 AUDC3 AUDF4 AUDC4")
    P(S, "Each line is the state of the registers at that instant. The AUDC values have the distortion in the high "
         "nibble ($A = square wave) and the volume in the low one. <font face=\"Mono\">song.bin</font> is the stream "
         "of the full project: the skeleton uses only its first byte, the AUDCTL chosen by the converter.")
    section(S, "Step 3: from the dump to the skeleton stream")
    P(S, "The skeleton stream is the simplest one that makes sense: for each frame one <b>mask</b> byte and "
         "the values of the registers that changed.")
    table(S, [
        ["Position", "Contents"],
        ["byte 0", "AUDCTL"],
        ["bytes 1-2", "number of frames (16 bits, little endian)"],
        ["then, for each frame", "one mask byte; bit <i>n</i> set to 1 means that register $D200 + <i>n</i> changes "
                                 "and its new value is one of the bytes that follow, in order"],
    ], [38, 132], caption="Table 8.3 — The format of the skeleton. The first frame always writes all the registers.")
    code(S, read_text("skeleton/dump2raw.py").rstrip(), title="skeleton/dump2raw.py", size=7)
    section(S, "Step 4: the player")
    P(S, "The player is a single routine, <font face=\"Mono\">vbi</font>, called by the deferred vertical blank. The "
         "functions <font face=\"Mono\">playerInit</font>, <font face=\"Mono\">playerStart</font> and "
         "<font face=\"Mono\">playerStop</font> are the ones the C program calls.")
    code(S, read_text("skeleton/player.s").rstrip(), title="skeleton/player.s", size=6.9)
    sub(S, "The points to understand")
    numbered(S, [
        "<b>SETVBV</b> ($E45C) installs a routine: register A says which vector (6 = immediate, 7 = deferred), "
        "X:Y the address. The deferred one runs after the OS work and must end with <b>XITVBV</b>.",
        "The <font face=\"Mono\">left</font> counter counts the frames remaining; at zero execution goes back to the "
        "start (<font face=\"Mono\">rewind</font>): the tune is a loop.",
        "The mask is consumed with <font face=\"Mono\">lsr</font>: bit 0 goes into the carry, and if it is 1 a byte is "
        "read and written to <font face=\"Mono\">AUDF1 + X</font>.",
        "<font face=\"Mono\">silence</font> clears the eight registers and AUDCTL to zero: it is needed at the start and "
        "at the end.",
        "The address of the registers ($D200) is the only hardware-specific thing: the rest is a stream reader.",
    ])
    section(S, "Step 5: the C program and the Makefile", need=95)
    code(S, read_text("skeleton/main.c").rstrip(), title="skeleton/main.c", size=7)
    code(S, read_text("skeleton/data.s").rstrip() + "\n", title="skeleton/data.s", size=7)
    code(S, read_text("skeleton/Makefile").rstrip(), title="skeleton/Makefile", size=7)
    section(S, "Step 6: building and running", need=70)
    code(S, "make SID=~/Music/C64Music/MUSICIANS/H/Hubbard_Rob/Commando.sid DURATION=20\n"
            "atari800 -atari -osb_rom ~/ATARI/ATARIOSB.ROM -run player.com   # 400/800\n"
            "atari800 -xe -xlxe_rom ~/ATARI/ATARIXL.ROM -run player.com      # XL/XE (this binary too)",
         title="Step 6")
    figure(S, "skeleton_screen.png", "Figure 8.1 — The skeleton running: one line of text, the music plays on its own.",
           width_mm=112)
    table(S, [
        ["Measure", "Value"],
        ["player.com (code + cc65 library + stream)", "7174 bytes"],
        ["20 s stream of Commando, uncompressed", "3982 bytes (about 200 bytes per second)"],
        ["the same with the LZ format of the full project", "676 bytes (5.9 times smaller)"],
    ], [92, 78], caption="Table 8.4 — What you gain by moving to the compressed format.")
    callout(S, "VERIFIED", "The skeleton was run on atari800, both as a 400/800 and as an XL/XE, recording the POKEY "
                           "registers at every frame: 475 out of 475 (400/800) and 428 out of 428 (XE) frames "
                           "identical to the starting dump.")
    callout(S, "NOTE", "The skeleton is compiled with <font face=\"Mono\">-t atari</font> and also runs on an XL/XE, where "
                       "the OS ROM stays on. The <font face=\"Mono\">atarixl</font> target of the full project "
                       "turns it off to have more memory, and this changes how the system and the interrupts are called.")
    section(S, "How to grow it", need=80)
    table(S, [
        ["Addition", "What changes", "Where it shows in the project", "Chapter"],
        ["better quality in the bass", "remove <font face=\"Mono\">-m plain</font>: 16-bit pair; the AUDCTL changes", "layout in <font face=\"Mono\">sidconv</font>", "4"],
        ["multispeed tunes", "K records per frame, DLI in the display list", "<font face=\"Mono\">patchDisplayList</font>, <font face=\"Mono\">vbim</font>", "6"],
        ["more music in the same memory", "per-register LZ streams, ring buffers", "<font face=\"Mono\">decode</font>, <font face=\"Mono\">lz_encode</font>", "5, 6"],
        ["two SIDs", "16 registers, second POKEY, detection", "<font face=\"Mono\">putreg</font>, <font face=\"Mono\">detect_stereo</font>", "6"],
        ["title, author, VU meters", "header with the strings, <font face=\"Mono\">outbuf</font> read by the C code", "<font face=\"Mono\">sid2pokey.c</font>", "7"],
        ["C64 font", "<font face=\"Mono\">mkfont</font>, CHBAS, reserved memory", "<font face=\"Mono\">install_font</font>", "7"],
    ], [34, 62, 52, 22], font=7.8, caption="Table 8.5 — A growth path.")
    callout(S, "TIP", "Add <b>one thing at a time</b> and after each one repeat the register comparison with the emulator "
                      "(chapter 9): when something breaks, the last change is the cause. This is how the full player "
                      "was built.")


def ch9(S):
    chapter(S, "Verification and tests")
    P(S, "You cannot verify sound by eye, but you can verify almost everything else: the registers the POKEY receives, "
         "the pitch, the opcodes, the screens. The method is always the same: compare what an independent emulator "
         "sees with what the converter decided.")
    section(S, "The five ways of verifying")
    table(S, [
        ["What", "How", "Reference"],
        ["the POKEY registers, frame by frame", "atari800 records the registers at every frame (<font face=\"Mono\">-pokeyrec</font>); "
                                                 "compare with <font face=\"Mono\">sidconv -d</font>", "the converter"],
        ["the undocumented 6502 opcodes", "588 cases run in the core and in VICE", "VICE x64sc 3.10"],
        ["the pitch", "synthetic tones recorded to WAV, FFT peak", "the divider formula"],
        ["the screen", "screenshots and pixel-by-pixel comparison (<font face=\"Mono\">compare -metric AE</font>) between states",
         "the screen itself"],
        ["regression over the collection", "conversion of thousands of HVSC tunes; the stream verifier runs on every conversion",
         "(no internal errors)"],
    ], [42, 88, 40], font=7.9, caption="Table 9.1 — The five checks.")
    section(S, "Comparing the registers")
    P(S, "atari800 can record the POKEY registers at regular intervals. With the interval equal to one frame "
         "(312 scanlines in PAL) you get one line per frame; with 312/K you get K of them, so the records "
         "played by the DLIs can be seen as well.")
    code(S, "atari800 -xe -xlxe_rom ATARIXL.ROM -pal -stereo -pokeyrec -pokeyrec-stereo -pokeyrec-ascii \\\n"
            "         -pokeyrec-interval 156 -pokeyrec-file pr.txt -run sid2pokey.com", title="Recording the registers (K = 2, two POKEYs)")
    bullets(S, [
        "The ASCII format gives 18 hexadecimal digits for each sample: the eight registers AUDF1…AUDC4 and AUDCTL; with "
        "<font face=\"Mono\">-pokeyrec-stereo</font> another 18 for the second POKEY.",
        "Sampling starts when the emulator starts: the line corresponding to the first record is found by looking for the "
        "<b>alignment</b> with the largest number of matching lines (usually a few tens of samples later, because of the "
        "OS start-up).",
        "If samples fall while the player is writing, the line contains half of the new record and half of the old one. "
        "That is why the player writes all the registers in a <b>burst</b> at the end of decoding: with register-by-register "
        "writing, at NTSC 2x 8% of the lines turned out to be half-updated, and after the fix none.",
        "With an interval that is not an exact divisor of the frame (NTSC, K = 3 or 4: 262/3 and 262/4) the sampling "
        "drifts. For those cases you record one line per frame and check that the same record is seen at every frame "
        "(838 frames out of 838).",
    ])
    code(S, "rows = [l.strip() for l in open('pr.txt') if len(l.strip()) == 36]      # 2 POKEYs: 2 x 18 digits\n"
            "p1 = [r[0:16] for r in rows];  p2 = [r[18:34] for r in rows]           # AUDF/AUDC only, not AUDCTL\n"
            "exp = [l.split(':')[1].split() for l in open('dump.txt')]               # sidconv -d\n"
            "e1 = [''.join(x[:8]).lower() for x in exp]; e2 = [''.join(x[8:16]).lower() for x in exp]\n"
            "best = max(range(len(rows) - 200), key=lambda o: sum(p1[o + i] == e1[i] for i in range(200)))\n"
            "print(sum(p1[best + i] == e1[i] for i in range(len(e1))), 'matching records out of', len(e1))",
         title="The comparison in Python (outline)", size=7)
    section(S, "Testing without windows: Xvfb")
    P(S, "For the automatic tests the emulator runs on a <b>virtual display</b> (Xvfb): no window appears and you "
         "can capture the screens with <font face=\"Mono\">import -window</font>. Keys are sent with "
         "<font face=\"Mono\">xdotool key</font>, which uses the XTEST extension: they arrive at the window under the "
         "pointer, so the pointer has to be moved into the emulator window.")
    code(S, "Xvfb :77 -screen 0 1024x768x24 &\n"
            "export DISPLAY=:77\n"
            "atari800 -xe -xlxe_rom ATARIXL.ROM -pal -stereo -run sid2pokey.com &\n"
            "WID=$(xdotool search --pid $! | head -1)\n"
            "xdotool mousemove --window $WID 336 240      # the pointer inside the window\n"
            "xdotool key space                           # a real key\n"
            "import -window $WID stopped.png", title="A test with a key, on a virtual display")
    callout(S, "PITFALL", "In keyboard tests the letters <font face=\"Mono\">a d w s</font> are the joystick 1 keys in "
                          "the atari800 configuration, and the other letters arrive as text events that, without a "
                          "window manager, do not reach the emulator. Use the space bar and Return: it is not a "
                          "defect of the player, but a test run with a key that does not arrive is a test that proves "
                          "nothing.")
    callout(S, "NOTE", "While working on this, for a certain period, atari800 quit by itself with exit code 0 less than a "
                       "second after starting on the real desktop (it received a request to close the window), with any "
                       "program and even with an empty configuration; on Xvfb it lived normally. The cause was not "
                       "found. If it happens, a virtual display lets you keep testing.")
    section(S, "The pitch")
    P(S, "To check the divider formulas, synthetic streams with a single tone were built (no SID): a 16-bit "
         "tone at 110 Hz, one at 55 Hz with the AUDCTL 15 kHz bit set, an 8-bit one on the 64 kHz clock (440 Hz) and one on "
         "the 15 kHz clock (220 Hz). They were recorded to WAV by atari800 and measured with the FFT:")
    table(S, [
        ["Tone", "AUDCTL", "Expected (Hz)", "Measured (Hz)", "Difference"],
        ["16-bit at 1.79 MHz, N = 8054", "$50", "110.002", "110.000", "−0.0 cents"],
        ["8-bit at 64 kHz, N = 71", "$00", "439.843", "439.854", "+0.0 cents"],
        ["8-bit at 15 kHz, N = 34", "$01", "222.237", "222.229", "−0.1 cents"],
        ["16-bit with the 15 kHz bit set", "$51", "55.001", "55.011", "+0.3 cents"],
    ], [64, 20, 28, 30, 28], align="LCRRR", mono_cols=(1,), caption="Table 9.2 — The divider formulas against the emulator audio.")
    section(S, "The results", need=110)
    table(S, [
        ["Test", "Outcome"],
        ["registers, 1x, 2x, 3x, 4x PAL, Atari 800 and XE", "all records identical to the converter"],
        ["registers, 2x NTSC (800); 3x and 4x NTSC with one sample per frame", "identical; 838 frames out of 838 in phase"],
        ["two SIDs on two POKEYs (2x and 4x, different layouts on the two chips)", "1396/1396 and 2792/2792 on both POKEYs, AUDCTL included"],
        ["two SIDs on an Atari without a second POKEY", "POKEY 1 receives exactly SID 1 and keeps its AUDCTL"],
        ["return to the start of the stream (3 s played for 14 s)", "1473/1473 (4x), 372/372 (1x), 641/641 (XE 2x)"],
        ["stop and restart with real keys", "294/294 on both POKEYs; 1109 samples at zero between the two playbacks"],
        ["screen, sound / pause / restart (Space and Return)", "0 pixels of difference, 400/800 and XL/XE"],
        ["undocumented opcodes against VICE", "588 cases out of 588 identical"],
        ["conversion of 4370 HVSC tunes (1 in 12 of MUSICIANS)", "4292 converted, no internal errors"],
        ["conversion of the 264 HVSC files with a second SID", "261 converted"],
    ], [86, 84], font=7.9, caption="Table 9.3 — The main results.")
    section(S, "What was not verified")
    bullets(S, [
        "<b>How it sounds.</b> No listening test is documented here: the judgment on the bass, on the envelope tails, "
        "on the stereo separation is up to whoever listens.",
        "<b>Real hardware.</b> Everything was tested on an emulator. In particular the detection of the second POKEY "
        "with “constant other than $FF” holds for atari800; on a real stereo board RANDOM should vary.",
        "<b>The ADSR defect</b> (<i>delay bug</i>) and the SID filters are not modeled, so there is nothing to "
        "compare.",
        "<b>Tunes with digital samples</b>, driven by NMI or by BASIC: not supported.",
    ])


def ch10(S):
    chapter(S, "Pitfalls and troubleshooting")
    P(S, "Every row of this table is a problem actually encountered while building the project: the symptom, "
         "the cause, the remedy.")
    table(S, [
        ["Symptom", "Cause", "Remedy"],
        ["on XL/XE the emulator exits after a few seconds", "direct call to $E45C with the ROM off (atarixl target)",
         "use the <font face=\"Mono\">SETVBV</font> symbol from <font face=\"Mono\">atari.inc</font>"],
        ["random sounds are heard at the end of the tune", "the DLIs started before the first VBI: records out of step",
         "enable the DLIs from the VBI (<font face=\"Mono\">vbim</font>), not in <font face=\"Mono\">startPlayer</font>"],
        ["the DLIs do not fire", "<font face=\"Mono\">SETVBV</font> sets NMIEN back to $40", "write NMIEN after SETVBV"],
        ["a two-SID tune sounds wrong on a normal Atari", "$D210+ mirror POKEY 1: the writes corrupt it",
         "detect the second POKEY before writing to it"],
        ["“No second POKEY” on atari800 with -stereo", "the emulator does not implement RANDOM of POKEY 2 (it reads 0)",
         "a constant other than $FF = present"],
        ["band of Atari characters halfway down the screen", "the DLI goes through a call that turns the OS ROM on",
         "serve the DLI from the NMI vector in RAM"],
        ["when stopped, the Atari glyphs come back", "blocking <font face=\"Mono\">cgetc()</font>: the ROM stays on", "wait for the key by reading CH"],
        ["the title line gets garbled when keys are pressed", "<font face=\"Mono\">cgetc()</font> echoes the key on the screen",
         "read CH, consume the key after release"],
        ["a BOOT ERROR page on exit (XL/XE)", "<font face=\"Mono\">main</font> returns to a DOS that does not exist", "never return"],
        ["the tune runs too fast or too slow", "PAL/NTSC does not match the stream", "<font face=\"Mono\">-p pal|ntsc</font>; the program warns you"],
        ["“stream larger than 20 KB”, or overflow at link time", "the program and the 16 buffers take about 17 KB",
         "a shorter <font face=\"Mono\">-t</font>, <font face=\"Mono\">-S 1</font>, or the XL/XE target (about 24 KB)"],
        ["the tune is silent", "digital samples via NMI or $D418: the three-voice model does not see them", "not supported: the warning says so"],
        ["the bass notes sound three octaves higher", "64 kHz divider: below 124 Hz the note cannot be reached",
         "leave <font face=\"Mono\">-m auto</font>: it uses the 16-bit pair"],
        ["<font face=\"Mono\">make</font> does not reconvert the tune", "<font face=\"Mono\">song.bin</font> depends only on the SID file",
         "<font face=\"Mono\">make -B song.bin ...</font>"],
        ["tests with letters do nothing", "a d w s are the joystick; the others arrive as text", "try Space and Return"],
    ], [52, 66, 52], font=7.6, keep=False, caption="Table 10.1 — Symptoms, causes, remedies.")
    callout(S, "TIP", "When a test gives a result you do not understand, first compare it with the "
                      "<font face=\"Mono\">sidconv -d</font> dump: it tells you whether the fault is in the conversion (the "
                      "expected registers are already wrong) or in the player (the expected registers are right, the "
                      "recorded ones are not).")
