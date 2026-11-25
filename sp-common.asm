; sp-common.asm - POKEY player driven by the deferred vertical blank.
;
; Replays the stream produced by tools/sidconv (see the format description
; at the top of tools/sidconv.c): once per video frame it reads a mask byte
; and then one byte for every register ($D200+n) whose mask bit is set.
; When the end of the stream is reached it restarts from the first frame.

.export _setupAndStartPlayer
.export _stopPlayer

.import song_data			; sp-data.asm
.import song_end

; SETVBV (OS: A=6 immediate / 7 deferred VBI vector) and XITVBV (OS: exit from
; a VBI routine) come from atari.inc.  On the atarixl target cc65 keeps the OS
; ROM banked out while the program runs, so SETVBV is a wrapper that enables
; it for the call: never call $E45C directly.  XITVBV runs inside the
; interrupt, where the ROM is already enabled.
.include "atari.inc"

audf1  = $d200				; AUDF1 AUDC1 AUDF2 AUDC2 ... AUDF4 AUDC4
audctl = $d208

HEADER = 4				; AUDCTL, video_hz, frames (16 bit)

.zeropage
ptr:	.res 2				; read pointer into the stream
mask:	.res 1

.macro nextbyte				; A = (ptr)++   (clobbers Y)
	ldy #0
	lda (ptr),y
	inc ptr
	bne :+
	inc ptr+1
:
.endmacro

.segment "CODE"

; void setupAndStartPlayer(void);
.proc _setupAndStartPlayer
	jsr silence
	lda song_data			; header byte 0: AUDCTL
	sta audctl
	jsr rewind
	ldy #<vbi
	ldx #>vbi
	lda #7				; deferred VBI vector
	jsr SETVBV
	rts
.endproc

; void stopPlayer(void);
.proc _stopPlayer
	ldy #<XITVBV			; back to the OS default
	ldx #>XITVBV
	lda #7
	jsr SETVBV
	jmp silence
.endproc

silence:
	lda #0
	ldx #7
:	sta audf1,x
	dex
	bpl :-
	rts

rewind:
	lda #<(song_data + HEADER)
	sta ptr
	lda #>(song_data + HEADER)
	sta ptr+1
	rts

vbi:
	lda ptr+1			; end of stream? -> loop
	cmp #>song_end
	bne @play
	lda ptr
	cmp #<song_end
	bne @play
	jsr rewind
@play:
	nextbyte			; register mask
	sta mask
	ldx #0
@next:
	lda mask
	beq @done
	lsr mask			; bit 0 -> carry
	bcc @skip
	nextbyte
	sta audf1,x
@skip:
	inx
	bne @next			; X <= 8 here, so always taken
@done:
	jmp XITVBV
