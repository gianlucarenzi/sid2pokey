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
		lda #10
		sta ztimer			; set the timer vector
_init:
		lda #>_tick
		sta cdtma2
		lda #<_tick
		sta cdtma2+1
		ldy ztimer
		jsr _setime
        rts
_tick:
		lda #volume
		sta audc1
		lda #freq
		sta audf1
		ldy #$ff	; delay
_delay:
		dey
		bne _delay
		sty audc1
		jmp _init
_setime:
		ldx #0
		lda #2
		jsr setvbv
		rts
.endproc
