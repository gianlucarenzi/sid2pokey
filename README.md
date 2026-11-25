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

`DURATION` is needed because a SID file has no length.  The stream must stay
under about 40 KB (roughly 3 minutes) to fit in memory.

## Current mapping (first milestone)

- SID voices 1-3 -> POKEY channels 1-3, 64 kHz clock, 8 bit dividers; channel 4 unused.
- Notes below about 124 Hz are folded up by octaves.
- Noise waveform -> distortion `$8x`; every other waveform -> pure tone `$Ax`.
- Volume = ADSR envelope (linear approximation, one step per play call) x master volume.
- The tempo follows real time: play calls are resampled to the Atari frame rate
  (PAL 49.86 Hz or NTSC 59.92 Hz).

Not handled yet: tunes with `play` address 0 (own IRQ handler, rejected with an
error), multispeed tunes (decimated to one play call per frame), filter, ring
modulation, sync, pulse width, sampled digi (`$D418`), 16 bit / 1.79 MHz
channel pairs for accurate bass, second POKEY (stereo), loop-point detection,
RSID tunes that need a real C64 environment, a few unstable undocumented 6502
opcodes.

## Checked so far

Commando (Rob Hubbard) converted and played in atari800 on both the Atari 800
and the XE target: the POKEY registers recorded by the emulator (`-pokeyrec`)
match the converter's frames one to one.  On a sample of 300 HVSC tunes by
various composers, 283 convert without errors; the other 17 are the
`play` address 0 case.

## Notes

- On the `atarixl` target cc65 keeps the OS ROM banked out, so `SETVBV` must be
  taken from `atari.inc` (a wrapper), never called as `$E45C`.
- `sid2gumby/` is the older project this one grew out of (Ivo van Poorten, GPL 3):
  it runs the SID code natively on the Atari instead of pre-converting it.
