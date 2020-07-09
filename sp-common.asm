.export _setupAndStartPlayer

sid_init = $2000
sid_play = $2003
siddata = $2000

irqen = $d20e
nmien = $d40e
nmires = $d40f
nmi = $fffa

.segment "CODE"

.proc _setupAndStartPlayer
		sei
		lda #0
		sta nmien
		sta irqen
		sta nmires
		lda #<_interrupt	; point IRQ Vector to our custom irq routine
		sta nmi
        lda #>_interrupt
       	sta nmi+1
       	cli
       	lda #64
       	sta nmien
        rts
.endproc

.proc _interrupt
		pha
		txa
		pha
		tya
		pha
		lda $8f
		sta $d01a
		pla
		tay
		pla
		tax
		pla
		rti
.endproc

