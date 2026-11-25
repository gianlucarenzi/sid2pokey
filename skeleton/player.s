; player.s - skeleton of a POKEY player for the Atari 8-bit computers.
;
; The whole player is one routine called from the deferred vertical blank, which
; replays a stream of register changes once per video frame.  It uses only
; documented 6502 instructions and the OS vectors, so it runs on the 400/800 and
; on the XL/XE.
;
; Stream (made by dump2raw.py from the output of tools/sidconv -d):
;
;   byte 0     AUDCTL
;   byte 1-2   number of frames (16 bit, little endian)
;   then, for every frame:
;     a mask byte, and one byte for every bit set in it: bit n of the mask
;     stands for the register $D200 + n  (AUDF1 AUDC1 AUDF2 AUDC2 ... AUDC4)
;     the registers whose bit is clear keep their value.

.export _playerInit
.export _playerStart
.export _playerStop
.import song_raw			; data.s

.include "atari.inc"			; SETVBV, XITVBV

audf1  = $d200				; the eight audio registers of POKEY
audctl = $d208
HEADER = 3				; size of the stream header

.zeropage
ptr:	.res 2				; read pointer into the stream
mask:	.res 1

.bss
left:	.res 2				; frames still to play

.segment "CODE"

; void playerInit(void);    silence POKEY, read the header, go to the first frame
_playerInit:
	jsr silence
	lda song_raw			; AUDCTL
	sta audctl
	; fall through

rewind:
	lda #<(song_raw + HEADER)
	sta ptr
	lda #>(song_raw + HEADER)
	sta ptr+1
	lda song_raw+1			; frames
	sta left
	lda song_raw+2
	sta left+1
	rts

; void playerStart(void);   install the deferred vertical blank routine
_playerStart:
	ldy #<vbi
	ldx #>vbi
	lda #7				; 6 = immediate VBI vector, 7 = deferred
	jsr SETVBV
	rts

; void playerStop(void);    back to the OS routine, and silence
_playerStop:
	ldy #<XITVBV
	ldx #>XITVBV
	lda #7
	jsr SETVBV
	; fall through

silence:
	ldx #7
	lda #0
:	sta audf1,x
	dex
	bpl :-
	sta audctl			; A = 0
	rts

; The deferred VBI: play one frame.
vbi:
	lda left			; all frames played? start again
	ora left+1
	bne play
	jsr rewind
play:
	lda left			; left = left - 1
	bne :+
	dec left+1
:	dec left

	ldy #0
	lda (ptr),y			; the mask of this frame
	sta mask
	inc ptr
	bne :+
	inc ptr+1
:
	ldx #0				; register 0..7
next:
	lsr mask			; bit 0 -> carry
	bcc skip
	lda (ptr),y			; the new value of register X
	sta audf1,x
	inc ptr
	bne skip
	inc ptr+1
skip:
	inx
	cpx #8
	bne next
	jmp XITVBV			; the deferred VBI ends here
