# ch_ui.py - chapter 7: the screen, the font, the VU meters
import diagrams as D
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, section, sub, table)


def build(S):
    chapter(S, "The screen, the font and the VU meters")
    P(S, "The screen is a C program (<font face=\"Mono\">sid2pokey.c</font>, about 500 lines) that plays nothing: "
         "it draws and it reads. The music belongs to the interrupts; the program, every frame, looks at the values the "
         "player has just decoded and moves the bars.")
    section(S, "How it is laid out")
    figure(S, "ui_single_xe.png", "Figure 7.1 — One SID, XL/XE: title, author and copyright from the file; three VU meters; status.",
           width_mm=128)
    table(S, [
        ["Rows", "Content"],
        ["0", "title bar in inverse video: “SID 2 POKEY” and “C64 MUSIC ON ATARI”"],
        ["1", "empty; the warning appears here if the stream and the machine have different frame rates"],
        ["2-6", "box: title, author, copyright (32 characters each)"],
        ["8-21", "“VOICES” box: 9 rows of bars (9-17), the voice numbers (18), the POKEY labels (19), a free row (20) and the border (21)"],
        ["22", "status: 1 or 2 POKEYs, frame rate, speed (1X-4X), elapsed time"],
        ["23", "“PLAYING / STOPPED — PRESS ANY KEY” in inverse video"],
    ], [20, 150], mono_cols=(0,), caption="Table 7.1 — The 24 rows of 40 columns.")
    P(S, "There are <b>three</b> VU meters with one POKEY, in columns 6 characters wide, and <b>six</b> with two POKEYs, in "
         "columns 4 characters wide split into two groups (figure 2.1). The numbers 1-3 are the SID voices; the labels say "
         "which chip each one is on.")
    section(S, "The colors")
    P(S, "The Atari text mode has two colors: the background (COLOR2) and the text, which takes the <b>hue</b> of the "
         "background and the <b>luminance</b> of COLOR1; the border (COLOR4) is separate. The C64 has the same scheme (light "
         "blue border, blue background, light blue text), so it is enough to choose one hue and three luminances.")
    table(S, [
        ["Register (shadow)", "Address", "Value", "Effect"],
        ["COLOR4", "$02C8", "$7A", "border: hue 7, luminance 10 (light blue)"],
        ["COLOR2", "$02C6", "$74", "background: hue 7, luminance 4 (dark blue)"],
        ["COLOR1", "$02C5", "$0C", "text luminance: 12 (the hue is that of the background)"],
    ], [38, 24, 18, 90], mono_cols=(0, 1, 2), caption="Table 7.2 — The colors of the screen (default hue $70, "
                                                      "can be changed with <font face=\"Mono\">-DUI_HUE=$..</font>).")
    figure(S, "colors.png", "Figure 7.2 — The three hues tried: $60 (purple), $70 (blue: the closest to the C64, chosen), "
                            "$80 (blue-green).", width_mm=162)
    callout(S, "NOTE", "The colors are written into the operating system's <b>shadow</b> registers, which it copies into the "
                       "hardware registers at every vertical blank. With only two colors you cannot give the bars different "
                       "colors without DLIs, which the player already uses for multispeed tunes.")
    section(S, "The C64 font")
    P(S, "The C64 character ROM is 4096 bytes: two sets of 256 glyphs (the second half is the negative of the first, "
         "which on the Atari is done by bit 7 of the code alone). Set 1 has uppercase letters and graphics, set 2 lowercase "
         "and uppercase letters. <font face=\"Mono\">tools/mkfont</font> derives the Atari font from it: 128 glyphs of 8 bytes "
         "in the order of the Atari's <b>internal screen codes</b>, which are not those of ASCII.")
    table(S, [
        ["Atari code", "Glyph", "Taken from the C64"],
        ["$00-$1F", "space ! \" # … ? (digits and punctuation)", "screen codes 32-63 (set 1)"],
        ["$20", "@", "code 0"],
        ["$21-$3A", "A-Z", "set 2, codes 65-90 (the uppercase letters of the lowercase set)"],
        ["$3B-$3F", "[ £ ] ↑ ←", "codes 27-31"],
        ["$40-$5F", "graphics (the PETSCII shapes)", "set 1, codes 64-95"],
        ["$60", "graphics", "code 96"],
        ["$61-$7A", "a-z", "set 2, codes 1-26"],
        ["$7B-$7F", "graphics", "codes 123-127"],
    ], [28, 80, 62], mono_cols=(0,), font=7.9, caption="Table 7.3 — From the C64 order to the Atari order. ASCII "
                                                        "$20-$5F becomes the code minus $20; $60-$7A stays the same.")
    figure(S, "font_map.png", "Figure 7.3 — The 128 glyphs of font.bin, by Atari screen code (the C64 ROM is "
                              "Commodore's: the file is built locally and is not in the repository).", width_mm=150)
    sub(S, "The glyphs the program draws itself")
    P(S, "The borders and the bars do not depend on the base font: the program overwrites some codes with glyphs of its own, "
         "so the screen works even without the C64 ROM (figure 7.5).")
    items = []
    for k in range(1, 8):
        items.append(("$%02X" % (0x47 + k), [0xFF if r >= 8 - k else 0 for r in range(8)]))
    flow(S, D.GlyphGrid(items, per_row=7, px=3.6, title="Bars: the k bottom pixels (codes $48-$4E)"), "")
    items = []
    for k in range(1, 8):
        items.append(("$%02X" % (0x50 + k), [0xFF if r == k else 0 for r in range(8)]))
    flow(S, D.GlyphGrid(items, per_row=7, px=3.6, title="Peak marker: one row (codes $51-$57)"), "")
    frame = [("$40", [0, 0, 0, 0xFF, 0xFF, 0, 0, 0]), ("$5D", [0x18] * 8),
             ("$60", [0, 0, 0, 0x1F, 0x1F, 0x18, 0x18, 0x18]), ("$7B", [0, 0, 0, 0xF8, 0xF8, 0x18, 0x18, 0x18]),
             ("$7C", [0x18, 0x18, 0x18, 0x1F, 0x1F, 0, 0, 0]), ("$7D", [0x18, 0x18, 0x18, 0xF8, 0xF8, 0, 0, 0])]
    flow(S, D.GlyphGrid(frame, per_row=7, px=3.6, title="Borders: horizontal line, vertical line and the four corners"),
         "Figure 7.4 — The 20 glyphs defined by the program; they are copies of the C64 shapes and go into the codes that "
         "the Atari uses for control graphics.")
    figure(S, "ui_nofont_xe.png", "Figure 7.5 — The same screen without the C64 ROM: the base font is the Atari one, "
                                  "borders and bars are identical.", width_mm=118)
    section(S, "Where the font lives", need=110)
    P(S, "The font must be in RAM, because it gets modified, and the register that points to it (CHBAS) wants a page "
         "aligned to 1 KB. How you get there depends on the model.")
    flow(S, D.MemoryMaps(), "Figure 7.6 — The memory of the two targets (simplified diagram).")
    bullets(S, [
        "<b>XL/XE (atarixl target).</b> cc65 turns the OS ROM off and has already copied the ROM font into RAM at $E000, "
        "where ANTIC looks for it: all you need is to overwrite it <b>in place</b>. CHBAS stays $E0.",
        "<b>400/800 (atari target).</b> The ROM is always on and cannot be modified. The linker reserves <b>2 KB</b> at the "
        "top of free RAM (<font face=\"Mono\">-Wl -D,__RESERVED_MEMORY__=0x800</font>); the program takes the aligned "
        "kilobyte inside that block and points CHBAS there. The block is 2 KB because the 1 KB boundary falls somewhere "
        "in the middle.",
    ])
    code(S, excerpt("sid2pokey.c", "static void install_font(void)", "CHBAS = (unsigned char) ((unsigned) font >> 8);") + "\n}",
         title="sid2pokey.c — install_font()", size=6.9)
    table(S, [
        ["Step", "400/800", "XL/XE"],
        ["font address", "(MEMTOP + 1 − $400) &amp; $FC00", "$E000"],
        ["starting base", "copy of the ROM font at $E000", "the font already in RAM"],
        ["C64 font", "copied onto the block, if font.bin is not empty", "copied in place, if font.bin is not empty"],
        ["the program's own glyphs", "written onto the block", "written in place"],
        ["CHBAS ($02F4)", "page of the block", "$E0 (unchanged)"],
    ], [40, 66, 64], mono_cols=(), font=7.8, caption="Table 7.4 — The same operations on the two models.")
    section(S, "The VU meters", need=80)
    P(S, "A bar represents the <b>volume of the POKEY channel</b> that plays that SID voice. The converter writes into the "
         "header, for each voice, the AUDC register that holds its volume (in the low 4 bits): that of the voice's channel, "
         "or AUDC2/AUDC4 of the 16-bit pair. The program reads that value from <font face=\"Mono\">outbuf</font>, "
         "the buffer where the player leaves the values of the last record.")
    table(S, [
        ["POKEY volume", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
        ["Level (0-63)", "0", "4", "8", "13", "17", "21", "25", "29", "34", "38", "42", "46", "50", "55", "59", "63"],
    ], [26] + [9.0] * 16, align="L" + "C" * 16, font=7.2,
          caption="Table 7.5 — From volume to bar level: 9 cells of 7 levels.")
    bullets(S, [
        "<b>Segments.</b> Each cell contains 7 filled pixels and one empty one (the thin gap between two segments): a full "
        "bar is 9 cells, 63 levels. A partial cell uses the glyph with k pixels at the bottom.",
        "<b>Decay.</b> The level jumps to the new value at once and falls by 3 levels per frame: from full to zero in about "
        "21 frames (0.4 s).",
        "<b>Peak.</b> A thin marker follows the maximum, holds for 24 frames (about half a second) and then falls by 1 "
        "level per frame. If it falls in the same cell as the top of the bar it is not drawn.",
    ])
    code(S, excerpt("sid2pokey.c", "static void vu_update(void)", "draw_bar(v);") + "\n\t}\n}",
         title="sid2pokey.c — vu_update(): volume, decay and peak of each voice", size=6.9)
    section(S, "Keyboard, time and states")
    bullets(S, [
        "<b>One frame at a time.</b> The program waits for the low byte of the system clock (RTCLOK, "
        "$0014) to change, which the VBI increments; every time it clears ATRACT ($004D) to avoid the color “attract mode”.",
        "<b>Time.</b> (frames − remaining frames) / 50 or 60: the counters are the player's, so the time restarts from "
        "zero when the tune restarts.",
        "<b>States.</b> A key stops the tune (bars at zero, “STOPPED”), the next one restarts it from the beginning. "
        "The program never returns to DOS: without a DOS the XL/XE would start booting again and fill the screen with "
        "<font face=\"Mono\">BOOT ERROR</font>.",
        "<b>Keyboard.</b> It reads CH ($02FC), where the system leaves the last key (“none” = $FF), and "
        "consumes it after the release (SKSTAT, $D20F, bit 2).",
    ])
    figure(S, "ui_stopped_xe.png", "Figure 7.7 — After a stop: bars at zero, “STOPPED”, the time stays where it was.",
           width_mm=118)
    code(S, excerpt("sid2pokey.c", "static unsigned char key_pressed(void)", "CH = 0xFF;") + "\n}",
         title="sid2pokey.c — the keyboard, read from CH", size=7)
    section(S, "The screen pitfalls", need=70)
    P(S, "On XL/XE the OS ROM is turned off and cc65 turns it back on for every system call or interrupt; at those "
         "moments ANTIC reads the font from the ROM. Three real defects came from here or from an operating system "
         "call.")
    figure(S, "pitfall_dli_band.png", "Figure 7.8 — Before: a band of Atari characters (hearts and arrows) in the middle of "
                                      "the screen, on multispeed tunes.", width_mm=112)
    callout(S, "PITFALL", "<b>The band of old characters.</b> The DLI went through the OS vector, and cc65's wrapper kept "
                          "the ROM on for the whole handler (about 35 scanlines with 16 registers): ANTIC read the ROM font "
                          "for those lines. <i>Fix</i>: on the atarixl target the DLI is served directly from the "
                          "NMI vector (chapter 6), without turning the ROM on.")
    figure(S, "pitfall_rom_font.png", "Figure 7.9 — Before: when stopped, the whole screen in the Atari font (hearts in place "
                                      "of the borders).", width_mm=112)
    callout(S, "PITFALL", "<b>The font that turns back to Atari when stopped.</b> Waiting for a key with <font face=\"Mono\">cgetc()</font> "
                          "is a blocking system call: the ROM stays on until a key is pressed. "
                          "<i>Fix</i>: wait with a loop that reads CH; no system calls after startup "
                          "(not even <font face=\"Mono\">clrscr()</font>, replaced by a <font face=\"Mono\">memset</font> "
                          "on the screen).")
    figure(S, "pitfall_key_echo.png", "Figure 7.10 — Before: the title row in the three states (playing, stopped, playing "
                                      "again): in the second one a character is missing, the “I” of SID.", width_mm=112)
    callout(S, "PITFALL", "<b>The key echo.</b> <font face=\"Mono\">cgetc()</font> reads through the screen handler, which "
                          "writes the typed character at the cursor position, at the top left: "
                          "every key punched a hole in the inverse bar of the title (the key itself, in normal video). "
                          "<i>Fix</i>: read CH directly.")
    callout(S, "VERIFIED", "With real keys sent to atari800 (space bar and Return, which for the screen handler is the "
                           "trickiest) the title box and row 0 stay identical pixel for pixel "
                           "across playing, pause and restart, on the 400/800 and on the XL/XE. Before, row 0 changed by 168 pixels.")
    callout(S, "NOTE", "One thing is not eliminated: the OS keyboard interrupt runs with the ROM on for a couple of "
                       "scanlines. A key press can make a scanline flicker for an instant; it leaves no marks.")
