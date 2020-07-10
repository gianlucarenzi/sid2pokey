; VerticalBlankInterrupt routine setup

.export _setupAndStartPlayer


irqen  = $d20e
nmien  = $d40e
nmires = $d40f
nmi    = $fffa
colbk  = $d01a
ztimer = $a000
sysvbv = $e45f
xitvbv = $e462
setvbv = $e45c
vvblki = $0222
vvblkd = $0224
cdtma2 = $0228
cdtmv2 = $021a
volume = $af
audf1  = $d200
audc1  = $d201
freq   = $08
off    = $a0

.segment "CODE"

.proc _setupAndStartPlayer: near
	sei
	lda nmien
	pha
	lda #0
	sta nmien
	sta irqen
	sta nmires

	ldy #<_vbi
	ldx #>_vbi
	lda #7
	jsr setvbv
	pla
	sta nmien
	cli
	rts
_vbi:
	lda #$7f
	sta colbk
	jmp xitvbv

.endproc
