# sid2pokey

Converts a C64 SID tune (PSID/RSID) into something an Atari 8-bit can play on
its POKEY chip, driven by the vertical blank interrupt.

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

`DURATION` is needed because a SID file has no length.  The stream must stay
under about 30 KB to fit in a 48 KB machine next to the player (which needs about
10 KB, rings included); the converter warns.  That is many minutes of music: 5
minutes of a 4x tune take 16 KB.

On the Atari, a key press stops the tune and the next one plays it again from the
start; the program never returns to DOS (without a DOS the XL/XE would end in a
page of `BOOT ERROR`).

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

Tunes with `play` address 0 install their own IRQ handler: sidconv emulates the
interrupt the way a C64 delivers it (vector at `$0314` with the KERNAL visible, at
`$FFFE` with RAM; a stub KERNAL provides the usual exits `$EA31`/`$EA34`/`$EA7B`/
`$EA81`).  The call rate comes from how the tune programs CIA1 timer A or the VIC
raster.  If `init` never returns (main loop) the IRQ handler is still called.

Not handled yet: NMI driven tunes (sampled digi players), tunes whose main loop
does the work, C64 BASIC tunes (`init` = 0), multispeed above 4x (resampled to 4),
filter, ring modulation, sync, pulse width, sampled digi
(`$D418`), second POKEY (stereo), loop-point detection, calls to KERNAL routines
other than the interrupt exits, a few unstable undocumented 6502 opcodes.  A
conversion that comes out silent is reported with a warning.

## Stream and player

`song.bin` has a 29 byte header (AUDCTL, frame rate, frames, records per frame,
and for each of the 8 POKEY registers either a constant or the offset of its
stream), then one LZ stream per register that changes, each with one value per
record.  Tokens come in groups of 8 behind a flag byte: a literal is one byte, a
match is two bytes (9 bit offset, length 3 to 130) into that register's own
last 512 values.  The format is described in the comment at the top of
`tools/sidconv.c`, which also decodes every stream it writes the way the player
does and refuses to write it if the result is not identical.

The player keeps a 512 byte ring buffer per register (4 KB of RAM), decodes one
value per register per record and writes them all to POKEY in one burst, so that
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
- On a sample of 4370 HVSC tunes (every 12th file of `MUSICIANS`), 4289 (98%)
  convert without errors, 40 of them silent (mostly sampled digi); the 81 refused
  are 28 NMI driven, 26 main-loop driven, 19 BASIC, 8 other.  Before the IRQ
  support the same sample converted 4137 (94.7%).
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
