; sp-common.asm - POKEY player driven by the vertical blank (and, for
; multispeed tunes, by display list interrupts).
;
; Replays the stream produced by tools/sidconv (see the format description
; at the top of tools/sidconv.c): one LZ-compressed stream per POKEY register
; that changes, one value per register per record.  A video frame holds
; play_k records.  The deferred VBI plays the first record of a frame; when
; play_k > 1 the display list carries DLI bits (patched by sid2pokey.c) and the
; DLI handler plays the other records, in order.  When the last frame has been
; played (checked at the VBI) every decoder is reset and the tune restarts.
;
; Decoder, per register: a flag byte (read bit 7 first, a sentinel bit tells
; when it is empty) tells whether the next token is a literal (one byte) or a
; match (two bytes: offset bits 0-7; then bit 7 = offset bit 8, bits 0-6 =
; length - 3).  Every decoded value goes to a 512 byte ring buffer of the
; register (all registers share the position pos) and to POKEY.

.export _initPlayer
.export _startPlayer
.export _stopPlayer
.export _play_k

.import song_data			; sp-data.asm

; SETVBV (OS: A=6 immediate / 7 deferred VBI vector) and XITVBV (OS: exit from
; a VBI routine) come from atari.inc.  On the atarixl target cc65 keeps the OS
; ROM banked out while the program runs, so SETVBV is a wrapper that enables
; it for the call: never call $E45C directly.  XITVBV runs inside the
; interrupt, where the ROM is already enabled.
.include "atari.inc"

audf1  = $d200				; AUDF1 AUDC1 AUDF2 AUDC2 ... AUDF4 AUDC4
audctl = $d208
nmien  = $d40e				; bit 7 DLI, bit 6 VBI

HDR_REGS = 5				; header: register table (8 x 3 bytes)
RING_SIZE = 8 * 512

.zeropage
sptr:	.res 2				; compressed stream pointer
wp:	.res 2				; ring write pointer (low byte always 0)
rp:	.res 2				; ring read pointer  (low byte always 0)
tmp:	.res 1
tmp2:	.res 1
tmp3:	.res 1
ri:	.res 1				; index in reglist
reg:	.res 1

.bss
_play_k:	.res 1			; records per video frame (stream header)
old_vdslst:	.res 2
frames:		.res 2			; frames in the stream
left:		.res 2			; frames still to play
pos_lo:		.res 1			; position in the rings (0..511)
pos_hi:		.res 1
nl:		.res 1
ring_hi:	.res 1			; page of the first (page aligned) ring
reglist:	.res 9			; registers that have a stream, then $ff
outbuf:		.res 8			; values of the current record, per register
start_lo:	.res 8			; stream start per register
start_hi:	.res 8
st_lo:		.res 8			; stream read pointer per register
st_hi:		.res 8
fl:		.res 8			; flag shift register
cnt:		.res 8			; values left in the current match
srcl:		.res 8			; match source position in the ring
srch:		.res 8
rhi:		.res 8			; page of the ring of each register
ring:		.res RING_SIZE + 255

.segment "CODE"

; void initPlayer(void);   no interrupts are touched
.proc _initPlayer
	jsr silence
	lda song_data			; header: AUDCTL
	sta audctl
	lda song_data+2			; frames
	sta frames
	lda song_data+3
	sta frames+1
	lda song_data+4			; records per frame
	sta _play_k

	lda #0				; the rings are page aligned
	sta wp
	sta rp
	lda #<ring
	beq @aligned
	lda #>ring
	clc
	adc #1
	jmp @sethi
@aligned:
	lda #>ring
@sethi:
	sta ring_hi
	ldx #0
@rh:	sta rhi,x			; ring r: ring_hi + 2 * r
	clc
	adc #2
	inx
	cpx #8
	bne @rh

	lda #0				; register table
	sta nl
	sta reg
	tay				; Y = header offset of the register
@reg:
	lda song_data+HDR_REGS,y
	bne @lz
	lda song_data+HDR_REGS+1,y	; constant: write it once
	ldx reg
	sta audf1,x
	jmp @next
@lz:	ldx reg
	clc
	lda song_data+HDR_REGS+1,y	; stream offset -> address
	adc #<song_data
	sta start_lo,x
	lda song_data+HDR_REGS+2,y
	adc #>song_data
	sta start_hi,x
	txa
	ldx nl
	sta reglist,x
	inc nl
@next:	iny
	iny
	iny
	inc reg
	lda reg
	cmp #8
	bne @reg
	ldx nl
	lda #$ff
	sta reglist,x
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

; Reset every decoder and start from the first frame.
rewind:
	ldx #7
@l:	lda start_lo,x
	sta st_lo,x
	lda start_hi,x
	sta st_hi,x
	lda #0
	sta fl,x
	sta cnt,x
	dex
	bpl @l
	lda #0
	sta pos_lo
	sta pos_hi
	lda frames
	sta left
	lda frames+1
	sta left+1
	rts

; Play one record: decode the next value of every register that has a stream,
; then write them all to POKEY in one burst (so that a 16 bit pair and the
; channels change together).  Clobbers A, X, Y.
playrec:
	lda #0
	sta ri
@next:
	ldx ri
	lda reglist,x
	bmi @burst
	tax
	jsr decode
	inc ri
	bne @next			; at most 8 registers: always taken
@burst:	ldy #0
@w:	ldx reglist,y
	bmi @done
	lda outbuf,x
	sta audf1,x
	iny
	bne @w				; at most 8 registers: always taken
@done:
	inc pos_lo
	bne @ret
	lda pos_hi
	eor #1
	sta pos_hi
@ret:	rts

; X = register.  Decode its next value, put it in its ring and in outbuf.
decode:
	lda cnt,x
	beq @token
	dec cnt,x			; inside a match
@copy:	lda rhi,x			; value = ring[source]
	clc
	adc srch,x
	sta rp+1
	ldy srcl,x
	lda (rp),y
	sta tmp
	inc srcl,x			; source = (source + 1) mod 512
	bne @out
	lda srch,x
	eor #1
	sta srch,x
@out:	lda rhi,x			; ring[pos] = value
	clc
	adc pos_hi
	sta wp+1
	ldy pos_lo
	lda tmp
	sta (wp),y
	sta outbuf,x
	rts

@token:	lda st_lo,x
	sta sptr
	lda st_hi,x
	sta sptr+1
	asl fl,x			; next flag -> carry
	bne @have
	ldy #0				; empty: reload the flag byte
	lda (sptr),y
	inc sptr
	bne @fl1
	inc sptr+1
@fl1:	sec				; carry = first flag, bit 0 = sentinel
	rol a
	sta fl,x
@have:	bcc @match

	ldy #0				; literal
	lda (sptr),y
	sta tmp
	inc sptr
	bne @save
	inc sptr+1
@save:	lda sptr
	sta st_lo,x
	lda sptr+1
	sta st_hi,x
	jmp @out

@match:	ldy #0
	lda (sptr),y			; offset bits 0-7
	sta tmp2
	iny
	lda (sptr),y			; bit 7: offset bit 8, bits 0-6: length - 3
	pha
	asl a
	lda #0
	rol a
	sta tmp3			; offset bit 8
	pla
	and #$7f
	clc
	adc #2				; values left after this one: length - 1
	sta cnt,x
	clc				; advance the stream pointer by 2
	lda sptr
	adc #2
	sta st_lo,x
	lda sptr+1
	adc #0
	sta st_hi,x
	sec				; source = (pos - offset) mod 512
	lda pos_lo
	sbc tmp2
	sta srcl,x
	lda pos_hi
	sbc tmp3
	and #1
	sta srch,x
	jmp @copy

; Deferred VBI: first record of the frame.  vbim (multispeed) also makes
; sure the DLIs are on, in step with this frame.
vbim:
	lda #$c0			; VBI + DLI
	sta nmien
vbi:
	lda left			; all frames played? -> start again
	ora left+1
	bne @go
	jsr rewind
@go:	lda left
	bne @dec
	dec left+1
@dec:	dec left
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
