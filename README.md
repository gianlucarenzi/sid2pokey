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

`DURATION` is needed because a SID file has no length.  The stream must stay
under about 40 KB (roughly 3 minutes) to fit in memory.

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

Not handled yet: tunes with `play` address 0 (own IRQ handler, rejected with an
error), multispeed tunes (decimated to one play call per frame), filter, ring
modulation, sync, pulse width, sampled digi (`$D418`), second POKEY (stereo),
loop-point detection, RSID tunes that need a real C64 environment, a few
unstable undocumented 6502 opcodes.

## Checked so far

- Commando (Rob Hubbard) converted and played in atari800 on the Atari 800 and
  on the XE target: the POKEY registers recorded by the emulator (`-pokeyrec`),
  `AUDCTL` included, match the converter's frames one to one.
- The divider formulas were checked against the emulator's audio: synthetic
  tones (16 bit pair at 110 Hz and 55 Hz, 8 bit at 64 kHz and 15 kHz) recorded
  to WAV peak within 0.3 cents of the computed frequency.
- On a sample of 300 HVSC tunes by various composers, 283 convert without
  errors (a 16 bit pair is chosen in almost all of them); the other 17 are the
  `play` address 0 case.
- Not checked by ear: how it actually sounds.

## Notes

- On the `atarixl` target cc65 keeps the OS ROM banked out, so `SETVBV` must be
  taken from `atari.inc` (a wrapper), never called as `$E45C`.
- `sid2gumby/` is the older project this one grew out of (Ivo van Poorten, GPL 3):
  it runs the SID code natively on the Atari instead of pre-converting it.
