# sid2pokey

Converts a C64 SID tune (PSID/RSID) into something an Atari 8-bit can play on
its POKEY chip, driven by the vertical blank interrupt.

SID files are 6502 code plus data, not audio.  `tools/sidconv` runs the tune's
`init`/`play` routines on a 6502 emulator, records what it writes to the SID
registers on every call, models the three SID voices (pitch, waveform, ADSR) and
maps them to POKEY `AUDF`/`AUDC` registers, one Atari video frame at a time.
The result (`song.bin`, a delta-coded register stream, about 3 bytes per frame)
is linked into the Atari binary together with a small VBI player
(`sp-common.asm`).

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
under about 40 KB to fit in memory: roughly 3 minutes of an ordinary tune, but
only about 90 seconds of a 4x one (the converter warns).

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
- Volume = ADSR envelope (linear approximation, one step per play call) x master volume.
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
- Not checked by ear: how it actually sounds.

## Notes

- On the `atarixl` target cc65 keeps the OS ROM banked out, so `SETVBV` must be
  taken from `atari.inc` (a wrapper), never called as `$E45C`.
- `sid2gumby/` is the older project this one grew out of (Ivo van Poorten, GPL 3):
  it runs the SID code natively on the Atari instead of pre-converting it.
