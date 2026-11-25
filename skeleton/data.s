; data.s - the stream built by dump2raw.py

.export song_raw

.segment "RODATA"

song_raw:
	.incbin "song.raw"
