; sp-data.asm - the converted tune (output of tools/sidconv) linked into the
; Atari binary.  Build it with:  make song.bin SID=path/to/tune.sid

.export song_data
.export song_end
.export _song_data = song_data		; for C (header access)

.segment "RODATA"

song_data:
	.incbin "song.bin"
song_end:
