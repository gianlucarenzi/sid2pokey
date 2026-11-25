# sid2pokey

Converts a C64 SID tune (PSID/RSID) into something an Atari 8-bit can play on
its POKEY chip, driven by the vertical blank interrupt.  Tunes with two SIDs
(PSID v3) play on two POKEYs, one per SID, on an Atari with a stereo POKEY upgrade.

SID files are 6502 code plus data, not audio.  `tools/sidconv` runs the tune's
`init`/`play` routines on a 6502 emulator, records what it writes to the SID
registers on every call, models the three SID voices (pitch, waveform, ADSR) and
maps them to POKEY `AUDF`/`AUDC` registers, one Atari video frame at a time.
The result (`song.bin`, one LZ-compressed stream per POKEY register, about 1
byte per video frame) is linked into the Atari binary together with a small VBI
player (`sp-common.asm`) that decodes it on the fly.

## Build

    make                                  # atarixl target (default)
    make MACH=atari                       # Atari 800, 48 KB
    make SID=path/to/tune.sid SONG=3 DURATION=90 VIDEO=ntsc
    make -B song.bin                      # re-convert after changing SONG/DURATION/VIDEO

Requires cc65 and a host C compiler.  The converter alone:

    gcc -O2 -o tools/sidconv tools/sidconv.c -lm
    tools/sidconv -v -s 1 -t 60 -p pal -o song.bin tune.sid     # -d dumps the POKEY registers
    tools/sidconv -m plain|bass16 ...                           # force a channel layout (default: auto)
    tools/sidconv -k 1 ...                                      # force 1-4 records per video frame (default: from the tune)
    tools/sidconv -S 1 ...                                      # convert only the first SID of a dual SID tune

`DURATION` is needed because a SID file has no length.  The stream must stay
under about 20 KB on a 400/800 and about 24 KB on an XL/XE (the linker decides:
it was tried with a large stream), next to the player, the screen code, the font
and 16 ring buffers; the converter warns above 20 KB.  That is many minutes of
music for most tunes (5 minutes of a 4x tune take 16 KB), but only about 80 seconds
of a tune that compresses as badly as `Slanted_2SID`.

On the Atari, a key press stops the tune and the next one plays it again from the
start; the program never returns to DOS (without a DOS the XL/XE would end in a
page of `BOOT ERROR`).

### The screen

A text screen in the style of the C64: a title bar, a box with the title, author and
copyright of the tune (taken from the SID file, 32 characters each), and a box
with one VU meter per SID voice: three bars with one POKEY, six (two groups of
three, "POKEY 1" and "POKEY 2") with two.  Below, how it plays (1 or 2 POKEYs, frame
rate, speed 1x-4x) and the time.  The colours are the C64 blue and light blue
(border, background and text), as the Atari text mode has two colours.

The bars are built from block characters of 7 pixel rows plus a blank one, so they
look like segments; the level falls smoothly after a peak and a thin marker holds the
peak for half a second.  A voice's level is the volume of the POKEY channel the
converter gave it (the stream header says which register that is for each of the
6 voices) read from the values the player has just decoded, so the meters show what
the POKEY plays, not what the SID would.

The font is the C64 character set, built by `tools/mkfont` from the C64 character
ROM (the Makefile looks for VICE's `/usr/lib/vice/C64/chargen-901225-01.bin`, or
the file in `CHARGEN=`).  The ROM is Commodore's, so the font is built locally into
`font.bin` and is not part of the repository; without the ROM the build goes on and
the screen uses the Atari font (the frames and the meters are drawn with glyphs that
the program defines itself).  Letters, digits and punctuation are put in the order of
the Atari screen codes, the lower case comes from the C64 lower case set.

How the font gets to the screen depends on the machine:

- XL/XE (`atarixl` target): cc65 keeps the OS ROM switched off and has already
  copied the ROM font to RAM at `$E000`, so the font is patched where it is.  A
  multispeed tune plays from DLIs, and cc65 switches the ROM on while the OS
  handles them, which would make the ANTIC read the ROM font for those scanlines
  (a band of the old characters across the screen); so on this target a DLI is
  served straight from the NMI vector, without the ROM.  For the same reason the
  screen code makes no OS call that can last: a blocking `cgetc()` (the program waits
  for the key in the stopped state) kept the ROM on and the Atari characters came
  back until the key was pressed, so the program polls `kbhit()` and clears the
  screen by itself instead of `clrscr()`.  The one OS call left, `cgetc()` once a key
  is there, is short.
- 400/800 (`atari` target): the linker keeps 2 KB at the top of RAM free
  (`__RESERVED_MEMORY__`) and the font, which has to sit on a 1 KB boundary, goes
  in the aligned KB of that block; `CHBAS` points to it.  The OS font is copied
  from the ROM first if there is no C64 font.

### Which Atari

The Atari side only uses documented 6502 instructions (it is assembled and compiled
for the plain NMOS 6502: no 65C02 instructions and no undocumented opcodes), so it
runs the same on the 400/800 and on the XL/XE.  They all have the same 6502C, and the
XL/XE do not add opcodes (those belong to the 65C02/65816 of accelerator boards, which
this project does not use).  What differs is the system: `make MACH=atari` builds for
a 400/800 with 48 KB and the OS ROM, the default `make` (`atarixl`) for an XL/XE,
where cc65 banks the OS ROM out.  The 6502 core in `tools/` runs on the PC only, to
execute the SID tune while converting; its undocumented opcodes have nothing to do
with the Atari.

## Current mapping

The three SID voices are laid out on the four POKEY channels in whichever way
gives the smallest pitch error for the tune (`-v` prints the average error in
cents of every layout it tried):

- three 8 bit channels on the 64 kHz or the 15 kHz base clock, or
- one voice on the 16 bit pair 1+2 at 1.79 MHz (precise bass, `AUDCTL $50`/`$51`)
  and the other two on channels 3 and 4 (64 kHz or 15 kHz).

Details:

- Notes below the range of a divider are folded up by octaves.
- Noise waveform -> distortion `$8x`, with the divider set from the SID noise
  LFSR clock (16 x pitch); every other waveform -> pure tone `$Ax`.
- Volume = ADSR envelope x master volume.  The envelope follows the SID's own
  generator (as in reSID): an 8 bit counter driven by a rate counter in SID clock
  cycles, linear attack, and decay and release whose step time grows as the level
  falls (periods 1, 2, 4, 8, 16, 30 below 255, 93, 54, 26, 14, 6), so notes drop
  fast and then have a long tail.  The ADSR delay bug is not modelled.  The result
  is quantized to the 16 POKEY volume levels, which cuts the very end of the tail.
- The tempo follows real time: play calls are resampled to the Atari frame rate
  (PAL 49.86 Hz or NTSC 59.92 Hz).

Multispeed tunes (two or more play calls per video frame, CIA timer set to
100/150/200 Hz) get several records per frame, up to 4: the vertical blank plays
the first one and display list interrupts play the others.  `sid2pokey.c` sets the
DLI bit on the display list instructions closest to the points that split the
frame in equal parts (it patches the OS display list in place and restores it on
stop; the lines are computed for PAL or NTSC at run time).  The VBI itself turns
the DLIs on, so that they are always in step with the frame.  Tunes faster than
4x are resampled to 4 records per frame, so some of their play calls are dropped,
and a rate that is not a whole multiple of the frame rate (such as a 4x PAL tune
on an NTSC machine) is resampled too.

### Two SIDs, two POKEYs

A tune whose PSID v3/v4 header gives a second SID address (`$D420`, `$D500`, `$DE00`
and a few others: 264 of the 56665 HVSC files) is converted for two POKEYs: SID 1
goes to the POKEY at `$D200` and SID 2 to the second POKEY of a stereo upgrade at
`$D210`, each with its own channel layout and `AUDCTL` (they are chosen separately,
so one chip may use a 16 bit pair and the other three plain channels).  A third SID
is ignored with a warning, since nine voices do not fit in eight channels.  `-S 1`
converts only the first SID.

On a machine without a second POKEY `$D210-$D21F` mirror the first one, so writing
them would overwrite the first chip.  The player therefore looks for the second
POKEY first: it sets it running and the first one in initialization mode, then reads
RANDOM at `$D21A`.  If RANDOM moves, or reads a constant other than `$FF`, the
second POKEY is there (the constant case is atari800 with `-stereo`, which plays
the second chip but returns 0 for its RANDOM); `$FF` constant is the mirror of the
first chip.  Without a second POKEY only the first SID is played, nothing is
written to `$D210+`, and the program says so.

Tunes with `play` address 0 install their own IRQ handler: sidconv emulates the
interrupt the way a C64 delivers it (vector at `$0314` with the KERNAL visible, at
`$FFFE` with RAM; a stub KERNAL provides the usual exits `$EA31`/`$EA34`/`$EA7B`/
`$EA81`).  The call rate comes from how the tune programs CIA1 timer A or the VIC
raster.  If `init` never returns (main loop) the IRQ handler is still called.

Not handled yet: NMI driven tunes (sampled digi players), tunes whose main loop
does the work, C64 BASIC tunes (`init` = 0), multispeed above 4x (resampled to 4),
filter, ring modulation, sync, pulse width, sampled digi
(`$D418`), a third SID, loop-point detection, using the second POKEY to improve
single SID tunes (a 16 bit pair for every voice), calls to KERNAL routines
other than the interrupt exits, the 12 JAM opcodes (they hang a real CPU).  A
conversion that comes out silent is reported with a warning.

## Stream and player

`song.bin` has a header of 109 + 3 bytes per register (AUDCTL, frame rate, frames,
records per frame, AUDCTL of the second POKEY, number of POKEYs, the register of
each voice's volume for the VU meters, title, author and copyright, and for each of
the 8 or 16 POKEY registers either a constant or the offset of its stream), then
one LZ stream per register that changes, each with one value per record.  Tokens come in groups of 8 behind a flag byte: a literal is one byte, a
match is two bytes (9 bit offset, length 3 to 130) into that register's own
last 512 values.  The format is described in the comment at the top of
`tools/sidconv.c`, which also decodes every stream it writes the way the player
does and refuses to write it if the result is not identical.

The player keeps a 512 byte ring buffer per register (8 KB of RAM for the 16
registers of two POKEYs), decodes one value per register per record and writes them all to POKEY in one burst, so that
channels and 16 bit pairs change together.  A decode takes in the order of a
thousand cycles per record (not measured), which is why even 4 records per frame
fit comfortably.  At the end the decoders are reset and the tune loops.

Planar streams were chosen after measuring the alternatives on 31 tunes (every
register as raw values or as deltas, LZ windows of 256, 512 and 1024 values):
raw values with a 512 window were the smallest, so no delta arithmetic is needed.

## Checked so far

- Commando (Rob Hubbard) converted and played in atari800 on the Atari 800 and
  on the XE target: the POKEY registers recorded by the emulator (`-pokeyrec`),
  `AUDCTL` included, match the converter's frames one to one.
- The divider formulas were checked against the emulator's audio: synthetic
  tones (16 bit pair at 110 Hz and 55 Hz, 8 bit at 64 kHz and 15 kHz) recorded
  to WAV peak within 0.3 cents of the computed frequency.
- On a sample of 4370 HVSC tunes (every 12th file of `MUSICIANS`), 4292 (98%)
  convert without errors, some of them silent (mostly sampled digi); the 78 refused
  are 28 NMI driven, 26 main-loop driven, 19 BASIC, 2 that call the KERNAL, 2 that
  never return and 1 JAM.  Before the IRQ support the same sample converted 4137
  (94.7%).
- IRQ driven tunes (First Strike, CBM64-2, 1200 A.D., Caverns of Eriban) give
  sequences of real notes.
- Multispeed in atari800 (POKEY recorder sampling several times per frame),
  PAL: 2x, 3x and 4x on the Atari 800, 2x on the XE, every record identical
  to the converter's; the stream also loops correctly (a 3 s stream played for
  14 s) and stop / play again works on both machines.  NTSC: 2x identical; 3x
  and 4x checked with one sample per frame (838 frames in step).
- Of the 4370 tunes, 199 convert with 2 or more records per frame (120 at 2x, 11
  at 3x, 68 at 4x or faster).
- The envelope model against the SID datasheet: attack 0 to 255 and release 255
  to 0 for the 16 rates (2 ms to 8 s, 6 ms to 24 s) are within 4% (within 2% from
  rate 4 up; rate 0 is 2.3 ms against the datasheet's rounded 2 ms), and the level
  stops at the sustain value.  Streams are about 4% larger than with the old
  linear model (39.8 KB against 38.1 KB on the 31 tunes below).
- Dual SID in atari800 with `-stereo` (both POKEYs recorded): records identical on
  both chips, `AUDCTL` of each included, for 2x and 4x tunes, with different
  layouts on the two chips, on the Atari 800 and the XE; stop / play again silences
  both POKEYs and restarts from the first record.  Without `-stereo` the first
  POKEY gets exactly SID 1 and keeps its `AUDCTL`.
- All 264 HVSC files with a second SID: 261 convert (the second SID was audible in
  258 of the first 260 checked, with every address type); the other 3 hit existing
  limits (two never return, one is driven by a main loop).
- The 6502 core of the converter is checked against VICE x64sc 3.10, undocumented
  opcodes included: `sh tests/opcodes/run.sh` runs 588 cases of ARR (also in decimal
  mode), XAA, LXA, AHX, TAS, SHX, SHY and LAS (registers, flags, stack pointer, the
  page-crossing behaviour of the stores) and compares each result with the reference
  recorded from VICE: all identical.  The magic constants of XAA (`$EF`) and LXA
  (`$EE`) are VICE's; on real chips they vary.  Three tunes of the sample (AHX, ARR,
  LXA) were refused before.
- Compression, 31 tunes of 45 s: 238 KB in the previous mask/delta format, 38 KB
  now (6.2x smaller; per tune from 3.8x to 13.3x, median 6.7x; 60 s of Commando
  take 2 KB, 60 s of the 4x tune 3.5 KB).
- The LZ player was run in atari800 on the Atari 800 and the XE: 1x, 2x, 3x and 4x
  PAL and 2x NTSC give the converter's records exactly, the stream loops over
  several wraps, and stop / play again restarts from the first record.
- Not checked by ear: how it actually sounds.

## Notes

- On the `atarixl` target cc65 keeps the OS ROM banked out, so `SETVBV` must be
  taken from `atari.inc` (a wrapper), never called as `$E45C`.
- `sid2gumby/` is the older project this one grew out of (Ivo van Poorten, GPL 3):
  it runs the SID code natively on the Atari instead of pre-converting it.
