; sp-font.asm - the character set built by tools/mkfont (font.bin: 1024 bytes,
; or empty when no C64 character ROM was available), linked into the Atari
; binary.  sid2pokey.c copies it where the screen can use it.

.export _font_data = font_data
.export _font_end = font_end

.segment "RODATA"

font_data:
	.incbin "font.bin"
font_end:
