; sp-common.asm - POKEY player driven by the vertical blank (and, for
; multispeed tunes, by display list interrupts).
;
; Replays the stream produced by tools/sidconv (see the format description
; at the top of tools/sidconv.c).  A video frame holds play_k records; each
; record is a mask byte followed by one byte for every register ($D200+n)
; whose mask bit is set.  The deferred VBI plays the first record of a frame;
; when play_k > 1 the display list carries DLI bits (patched by sid2pokey.c)
; and the DLI handler plays the other records, in order.  When the end of the
; stream is reached (checked at the VBI) it restarts from the beginning.

.export _initPlayer
.export _startPlayer
.export _stopPlayer
.export _play_k

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
nmien  = $d40e				; bit 7 DLI, bit 6 VBI

HEADER = 5				; AUDCTL, video_hz, frames (16 bit), play_k

.zeropage
ptr:	.res 2				; read pointer into the stream
mask:	.res 1

.bss
_play_k:	.res 1			; records per video frame (stream header)
old_vdslst:	.res 2

.macro nextbyte				; A = (ptr)++   (clobbers Y)
	ldy #0
	lda (ptr),y
	inc ptr
	bne :+
	inc ptr+1
:
.endmacro

.segment "CODE"

; void initPlayer(void);   no interrupts are touched
.proc _initPlayer
	jsr silence
	lda song_data			; header byte 0: AUDCTL
	sta audctl
	lda song_data+4			; header byte 4: records per frame
	sta _play_k
	jmp rewind
.endproc

; void startPlayer(void);  install the VBI (and the DLI handler)
;
; For multispeed tunes the VBI itself switches the DLIs on (vbim), so that
; they only start after the first VBI: the records of a frame must always be
; played in the order VBI, DLI, DLI, ... or the end of the stream would not
; fall on a frame boundary.
.proc _startPlayer
	lda _play_k
	cmp #2
	bcs @multi
	ldy #<vbi
	ldx #>vbi
	jmp @set
@multi:
	lda VDSLST			; keep the previous DLI vector
	sta old_vdslst
	lda VDSLST+1
	sta old_vdslst+1
	lda #<dli
	sta VDSLST
	lda #>dli
	sta VDSLST+1
	ldy #<vbim
	ldx #>vbim
@set:
	lda #7				; deferred VBI vector
	jsr SETVBV
	rts
.endproc

; void stopPlayer(void);
.proc _stopPlayer
	lda _play_k
	cmp #2
	bcc @vbi
	lda #$40			; DLI off
	sta nmien
	lda old_vdslst
	sta VDSLST
	lda old_vdslst+1
	sta VDSLST+1
@vbi:
	ldy #<XITVBV			; back to the OS default
	ldx #>XITVBV
	lda #7
	jsr SETVBV
	jsr silence
	lda #0				; the stream may have set 16 bit / 15 kHz modes
	sta audctl
	rts
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

; Play one record.  Clobbers A, X, Y.
playrec:
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
	rts

; Deferred VBI: first record of the frame.  vbim (multispeed) also makes
; sure the DLIs are on, in step with this frame.
vbim:
	lda #$c0			; VBI + DLI
	sta nmien
vbi:
	lda ptr+1			; end of stream? -> loop
	cmp #>song_end
	bcc @play			; below the end
	bne @loop			; beyond it (must not happen)
	lda ptr
	cmp #<song_end
	bcc @play
@loop:
	jsr rewind
@play:
	jsr playrec
	jmp XITVBV

; Display list interrupt: next record of the frame.
dli:
	pha
	txa
	pha
	tya
	pha
	jsr playrec
	pla
	tay
	pla
	tax
	pla
	rti
