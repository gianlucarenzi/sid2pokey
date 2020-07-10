	.opt nolist
	*=$1f00
bp
	lda #2        ;init reset key
	sta 9
	lda #bp&255
	sta 2
	lda #bp/256
	sta 3
	lda #0
	sta 580
	sta ln        ;lvl var=0
	sta sp        ;spd var=0
	sta 82        ;lmar=0
	sta jlock     ;unlok joystik
	lda #39
	sta 83        ;rmar=0
	lda #7
	jsr graphics
	lda #64
	sta 16
	sta 53774     ;no break
	lda #hpos&255
	sta $c0       ;dec adr l
	sta phpos     ;hpos ptr l
	lda #hpos/256
	sta $c1       ;dec adr h
	sta phpos+1   ;hpos ptr h
	ldy #0
makedec
	lda #$de      ;"dec abs,x"
	sta decs,y
	lda $c0       ; adr to dec l
	iny
	sta decs,y
	lda $c1       ; adr to dec h
	iny
	sta decs,y
	lda $c0       ;inc by 8 adr for
	clc           ; 'dec' instr to
	adc #$08      ; get nxt in lyr
	sta $c0       ; of strs
	lda $c1
	adc #0
	sta $c1
	iny           ;make nxt instr.
	cpy #72       ;done all?
	bcc makedec   ;n:cont
	lda #dlii&255 ;y:init adr to
	sta $c0       ; make dli in
	lda #dlii/256
	sta $c1
	lda #lt&255   ;init ptr to
	sta plt       ; lum tbl
	lda #lt/256
	sta plt+1
	ldx #0        ;#dli's done
omdli
	ldy #0        ;#instr's done
imdli
	lda dlip,y    ;get instr.
	sta ($c0),y   ;put in dli
	iny           ;nxt byt
	cpy #15       ;done?
	bcc imdli     ;n:get another
	lda $c0       ;y:inc adr where
	clc           ; dli is put in
	adc #15       ; mem
	sta $c0
	lda $c1
	adc #0
	sta $c1
	lda phpos     ;chg dli instr
	clc           ; tbl so nxt dli
	adc #1        ; refers to nxt
	sta phpos     ; star's hpos
	lda phpos+1
	adc #0
	sta phpos+1
	lda plt       ;same for lum.
	clc
	adc #1
	sta plt
	lda plt+1
	adc #0
	sta plt+1
	inx
	cpx #192      ;done 192 dlis?
	bcc omdli     ;n:keep making
	lda #3        ;y:enable p/m
	sta 53277
	sta erp       ;lvl 1 pse
	lda #$40      ;pmbase=$4000
	sta 54279
	lda #62       ;sdmctl=sgl line
	sta 559
	lda #1        ;grprior
	sta 623
	sta 752       ;cursor off
	lda elvt      ;get lvl 1 spd
	sta elvl      ;store in pgm
	lda #$31      ;init msgs
	sta lngm
	sta spgm
	lda #14       ;set up p/m col
	sta 704
	sta 705
	sta 706
	ldy #0
	tya
blankpm
	sta $4300,y   ;clr m1-4
	sta $4400,y   ; p0
	sta $4500,y   ; p1
	sta $4600,y   ; p2
	iny
	bne blankpm   ;done all 256?
	ldx #32       ;y:x=ofset to m0
	lda #$80
	sta x         ;init crshr pos
	sta y
fm
	sta $4300,x ;fill m3
	inx
	cpx #224      ;bot of screen?
	bcc fm        ;n:cont fill
	ldx #0        ;y:init str cols
	stx ctr
olp
	ldy #0
ilp
	lda c,y       ;get lum from tbl
	sta lt,x      ;store in big tbl
	inx
	iny
	cpy #8        ;done w/sml tbl?
	bcc ilp       ;n:keep xfer
	inc ctr       ;y:nxt grp
	lda ctr
	cmp #24       ;done w/screen?
	bcc olp       ;n:xfer sml tbl
	lda #0        ;y:blk bckground
	sta 710
	tax
fill
	lda $d20a
	sta hpos,x    ;rnd star hpos
	inx
	cpx #192      ;done 192?
	bcc fill      ;n:more rnd hpos
	lda 560       ;y:set up dli
	sta $c0       ; line
	lda 561
	sta $c1
	ldy #2
	lda ($c0),y
	ora #$80
	sta ($c0),y
	lda #svbi&255 ;adr for setup
	sta $0228     ; countdown timer
	lda #svbi/256 ; routine
	sta $0229
	lda #dli&255  ;dli adr
	sta 512
	lda #dli/256
	sta 513
	ldx #0
inite
	lda $d20a
	and #$7f
	clc
	adc #60       ;rnd enm x
	sta ex,x
	and #$3f      ;rnd enm move
	sta elim,x    ; limit
	and #$03      ;rnd enm dx
	sec
	sbc #1
	sta edx,x
reinity
	lda $d20a     ;rnd enm y
	and #$7f
	clc
	adc #46
	sta ey,x
	and #$03      ;rnd enm dy
	sec
	sbc #1
	beq reinity   ;no zero dy!
	sta edy,x
	lda #0        ;mvment ctr=0
	sta ectr,x
	sta elock,x   ;unlok enm
	lda #$ff      ;#vects moved=
	sta nv,x      ; neg:enm advanc
	lda #5        ;enm shp ctr=5=
	sta esc,x     ; smallest frame
	lda #7
	sta ep,x      ;tmr pse=7
	sta et,x      ;tmr=7
	inx
	cpx #3        ;done all 3 enm?
	bcc inite     ;n:init next
	lda erp       ;y:enm rtn pse*8=
	asl a         ; enm firing pse
	asl a
	asl a
	sta okf
	lda #$70
	sta shield    ;init shield
	lda #$99
	sta rem       ;init remaining
	lda #0        ;pos 0,0
	sta 656
	sta 657
	sta 658
	tax           ;x=iocb0=scrn
	lda #11       ;iccom=putchr
	sta $0342
	lda #smsg&255 ;icbadr=smsg
	sta $0344
	lda #smsg/256
	sta $0345
	lda #158      ;icblen=158
	sta $0348
	stx $0349
	stx $02ff     ;no ctrl-1
	jsr $e456     ;ciov
st
	ldx #0      ;pse abt 1 sec
op
	ldy #0
ip
	dey
	bne ip
	dex
	bne op
	stx $02ff     ;no ctrl-1
	lda 53279     ;console key
	cmp #7        ;touching a key?
	beq st
	cmp #5        ;select?
	bne nsel
	jmp select
nsel
	cmp #3    ;option?
	bne nopt
	jmp option
nopt
	cmp #6    ;start?
	bne st
	jmp start
option
	ldx ln        ;inc level number
	inx
	cpx #3
	bcc lns
	ldx #0
lns
	stx ln
	lda elvt,x    ;get enm lvl
	sta elvl      ;store in pgm
	lda #35       ;pos 33,0
	sta 657
	lda #0
	sta 658
	sta 656
	sta $0348     ;icblen=0:data
	sta $0349     ; stored in accu.
	lda #11       ;iccom=putchr
	sta $0342
	inx           ;chg lvl to ascii
	txa
	ora #$30
	sta lngm      ;store in gmsg
	ldx #$00      ;x=iocb0:screen
	jsr $e456     ;ciov
	jmp st        ;back to pause
select
	ldx sp        ;inc enm spd by 1
	inx
	cpx #3
	bcc sps
	ldx #0
sps
	stx sp
	lda erpt,x    ;get new pause
	sta erp       ; &store in pgm
	lda #35       ;pos 33,1
	sta 657
	lda #0
	sta 658
	sta $0348     ;icblen=0:data in
	sta $0349     ; accu.
	lda #1
	sta 656
	lda #11       ;iccom=putchr
	sta $0342
	inx           ;chg spd to ascii
	txa
	ora #$30
	sta spgm      ;store in gmsg
	ldx #0        ;x=iocb0:screen
	jsr $e456     ;ciov
	jmp st        ;back to pause
start
	ldx #0        ;pos 0,0
	stx 656
	stx 657
	stx 658
	lda #11       ;iccom=putchr
	sta $342
	lda #gmsg&255 ;icbadr=gmsg
	sta $0344
	lda #gmsg/256
	sta $0345
	lda #158      ;icblen=158
	sta $0348
	lda #0
	sta $0349
	jsr $e456     ;ciov
	lda #1        ;set flag=put
	sta eflag     ; crshair on scr
	sta $21a      ;enable set rtn
	lda #192
	sta 54286     ;enable dli
main
	lda $d20f
	and #$04      ;pressng any key?
	bne nospace
	lda 53769
	cmp #$21      ;pressing space?
	bne nospace
	jsr stpi      ;stp all inter.
keyed
	lda $d20f
	and #$04      ;still pressing?
	beq keyed
paused
	lda $d20f
	and #$04      ;pressing a key?
	bne paused
	lda 53769
	cmp #$21      ;pressing space?
	bne paused
release
	lda $d20f
	and #$04      ;still pressing?
	beq release
	jsr stri      ;restart inter.
nospace
	lda #0
	sta 77        ;no attract mode
	lda $d010     ;fire button?
	bne efire     ;n:enm's fire
	jmp fire      ;y:you fire
efire
	lda okf       ;time for enm to
	beq doefire   ; fire?
	jmp main
doefire
	lda erp       ;restore enm fire
	asl a         ; ctr
	asl a
	asl a
	sta okf
	lda $d20a
elvl=*+1
	cmp #64       ;fire according
	bcs main      ; to probability
	and #$03
	cmp #3
	beq main
	tax           ;enemy # firing
	lda nv,x
	beq main      ;if receding,quit
	bmi main      ;if advancng,quit
	lda elock,x
	bne main      ;if locked,quit
	stx el
	lda #$20      ;start enm laser
	sta $d200     ; sound
	lda #$4f
	sta $d201
	lda #1        ;lock enemy
	sta elock,x
	lda #2        ;color 2
	jsr color
	ldx el
	lda ey,x      ;chg enm plr y
	sec           ; into gr 7 ypos
	sbc #26
	lsr a
	pha
	tay
	lda ex,x      ;chg enm plr x
	sec           ; into gr 7 xpos
	sbc #45
	pha
	tax
	lda #0
	jsr plot      ;plot
	lda $d20a     ;rnd ypos
	and #$3f
	clc
	adc #8
	tay
	sta ly
	lda $d20a     ;rnd xpos
	and #$7f
	clc
	adc #16
	tax
	sta lx
	lda #0
	jsr drawto    ;drawto to here
	lda #64       ;flash screen red
	sta 712
	sta 710
	lda #0        ;color 0
	jsr color
	pla           ;start xpos for
	tax           ; laser
	pla           ;start ypos for
	tay           ; laser
	lda #0
	jsr plot      ;'unplot' this pt
	lda #0        ;end xpos for
	ldx lx        ; laser
	ldy ly        ;end ypos
	jsr drawto    ;erase line
	ldx el
	lda #0        ;unlock enemy
	sta elock,x
	sta $d200     ;turn off sound
	sta $d201
	sta 712       ;blacken screen
	sta 710
	lda shield
	pha
	cmp #2
	bcc lose      ;you killed?
	jsr stpi
	sed
	pla
	sec
	sbc #2        ;decrease shield
	sta shield
	pha
	cld
	jsr stri
	lda #36       ;pos 36,0
	sta 657
	lda #0
	sta 658
	sta 656
	pla
	jsr pn        ;print new shield
	jmp main      ;back to main
lose
	lda #$8f      ;distortion,vol
	sta $d201     ; for your expl
	sta jlock     ;lock jstick
	ldx #$80      ;expl duration
lo
	ldy #0
li
	lda $d20a
	sta $d200     ;rnd freq
	sta 712       ;rnd col
	sta 710
	dey
	bne li
	dex
	bne lo        ;loop your expl
	stx $d200     ;turn off sound
	stx $d201
	stx 712       ;bck col=0
	stx 710
	stx 656       ;pos 0,0
	stx 657
	stx 658
	lda #11
	sta $0342     ;iccom=prnchr
	lda #lmsg&255 ;icbadr=lmsg
	sta $0344
	lda #lmsg/256
	sta $0345
	lda #39       ;icblen=39
	sta $0348
	stx $0349
	jsr $e456     ;ciov
	jmp res       ;wait for restart
fire
	lda #$4f  ;start your laser
	sta $d201     ; sound
	lda #1
	sta $d200
	sta jlock     ;lock joystik
	jsr color     ;color 1
	lda #0
	sta 53278     ;clr old coll.
	ldx #80
	ldy #79
	jsr plot      ;plot 80,79
	lda x         ;chg crosshair x
	sec           ; to gr.7 xpos
	sbc #45
	pha
	tax
	lda y         ;chg crosshair y
	sec           ; to gr.7 ypos
	sbc #26
	lsr a
	pha
	tay
	lda #0
	jsr drawto    ;drawto to here
	lda #0
	jsr color     ;color 0
	lda #0
	ldx #80
	ldy #79
	jsr plot      ;erase laser strt
	pla           ;laser end y
	tay
	pla           ;laser end x
	tax
	lda #0        ;turn off sound
	sta $d200
	sta $d201
	jsr drawto    ;erase laser
	lda #0        ;unlok joystik
	sta jlock
	lda $d008     ;check for any
	beq ch2       ; collisions
	jsr hit
ch2
	lda $d009
	beq ch3
	jsr hit
ch3
	lda $d00a
	beq nohit
	jsr hit
nohit
	jmp efire     ;let enm fire
hit
	bit one       ;hit p0?
	beq oneok
	ldx #0
	jsr explode
oneok
	bit two       ;hit p1?
	beq twook
	ldx #1
	jsr explode
twook
	bit four      ;hit p2?
	beq fourok
	ldx #2
	jsr explode
fourok
	rts
explode
	pha           ;save coll reg
	txa           ;save which enm
	pha           ; to explode
	lda elock,x   ;enm locked?
	beq canexp
	pla
	pla
	rts
canexp pla     ;restore which to
	pha           ; expl.&save agn
	clc           ;get which plr
	adc #$44      ; band to use
	sta expadr
	lda #1        ;lock enemy
	sta elock,x
	lda ey,x      ;get enm ypos
	tay
	ldx #0
explp
	lda expshp,x  ;put explosion
expadr=*+2
	sta $ff00,y
	inx
	iny
	cpx #12       ;all 12?
	bcc explp
	pla
	tax
	lda #60       ;keep this expl.
	sta expctr,x  ; on for 1 sec
	jsr stpi      ;stp int
	sed
	lda rem
	sec
	sbc #1
	sta rem       ;rem=rem-1(dec)
	lda shield
	cmp #$99
	beq nois
	clc
	adc #1
	sta shield    ;shield=shield+1
nois
	cld
	jsr stri      ;str int
	lda rem
	pha
	cmp #3        ;>=3 left?
	bcs canr
	lda #0        ;cant restore
	jmp storr
canr
	lda #1    ;can restore
storr
	sta r,x
	pla
	beq win       ;if kill all,win!
	ldy #36       ;pos 36,1
	sty 657
	ldy #0
	sty 658
	ldy #1
	sty 656
	jsr pn        ;prnt #remaining
	lda #36       ;pos 36,0
	sta 657
	lda #0
	sta 658
	sta 656
	lda shield
	jsr pn        ;print new shield
	pla           ;restore col reg
	rts           ;back to caller
win
	ldx #0     ;pos 0,0
	stx 656
	stx 657
	stx 658
	lda #11       ;iccom=putchr
	sta $342
	lda #wmsg&255 ;icbadr=wmsg
	sta $344
	lda #wmsg/256
	sta $345
	lda #79       ;icblen=79
	sta $348
	stx $349
	jsr $e456     ;ciov
res
	lda 53279  ;pressing start?
	cmp #6
	bne res
	jmp $e474     ;'press' reset
pn
	pha
	lsr a         ;get high nibble
	lsr a
	lsr a
	lsr a
	jsr ca        ;print
	pla
	and #$0f      ;get low nbl&prt
ca
	ora #$30    ;chg to ascii
	ldx #11       ;iccom=putchr
	stx $342
	ldx #0        ;icblen=0=data in
	stx $348      ; accu.
	stx $349
	jmp $e456     ;ciov
stpi
	lda #$80      ;stop interrupts
	sta $d40e
	sei
	rts
stri
	lda #$c0  ;enable inter.'s
	sta $d40e
	cli
	rts
svbi
	lda #dvbi&255 ;enable def vbi
	sta $0224
	lda #dvbi/256
	sta $0225
	lda #ivbi&255 ;enable imm vbi
	sta $0222
	lda #ivbi/256
	sta $0223
	lda #crtn&255 ;enable ctdn tmr
	sta $0228     ; routine
	lda #crtn/256
	sta $0229
	lda #1
	sta $021a
	rts
crtn
	lda #0
	sta $02ff     ;no ctrl-1
	inc 708       ;pulse your laser
	lda okf       ;update okf (enm
	beq nuokf     ; fire ctr)
	dec okf
nuokf
	ldx #2
ckexp
	lda expctr,x  ;enm exploding?
	beq nxexp
	dec expctr,x  ;dec expl ctr
	beq stpexp    ;if done exp,stop
	lda #$20      ;else,keep expl
	sta $d202     ; sound on
	lda #$0f
	sta $d203
nxexp
	dex
	bpl ckexp     ;done all enm's?
	lda #1        ;reset ctdn tmr
	sta $21a
	rts
stpexp
	txa
	pha
	clc           ;get which plr
	adc #$44      ; band to use
	sta erexad
	lda ey,x
	tay
	lda #0
	sta $d202     ;stop expl sound
	sta $d203
	tax
erex
erexad=*+2
	sta $ff00,y   ;erase expl
	inx
	iny
	cpx #12       ;done erasing?
	bcc erex
	pla
	tax
	lda $d20a     ;rnd xpos
	and #$7f
	clc
	adc #60
	sta ex,x
	lda $d20a     ;rnd ypos
	and #$7f
	clc
	adc #46
	sta ey,x
	lda #$ff      ;enemy=advancing
	sta nv,x
	lda #0
	sta 53278     ;no coll w/expl.
	lda #5        ;enemy=starts
	sta esc,x     ; out small
	lda #7
	sta et,x      ;enm tmr=7
	sta ep,x      ;enm tmr pse=7
	lda r,x
	beq nou       ;can we unlok?
	lda #0
	sta elock,x   ;unlok
nou
	jmp nxexp  ;nxt expl.
dvbi
	inc s1        ;star1 ctr=..+1
	inc s2        ; 2
	inc s3        ; 3
	inc s4        ; 4
	inc s5        ; 5
	inc s6        ; 6
	inc s7        ; 7
	inc s8        ; 8
	ldx #0
pause
	lda s1,x      ;need to reset
	cmp ps,x      ; this ctr?
	bcc skip
	lda #0        ;reset ctr
	sta s1,x
	jsr decs      ;and mov the strs
	cpx #1
	bcs skip
	jsr decs
skip
	inx           ;next level
	cpx #8        ;done all 8 lvls?
	bcc pause
	jmp $e462     ;ret to system
decs
	*=*+72        ;dec strs in lyr
	rts           ; (created rtne)
dli
	pha           ;save regs
	txa
	pha
	tya
	pha
dlii
	*=*+2880      ;set str hpos,lum
	pla           ;restore regs
	tay
	pla
	tax
	pla
	rti
ivbi
	lda jlock     ;locked joystik?
	beq jmove
	jmp ertn
jmove
	ldx #1
checkjoy
	lda #15       ;get 15-stick(0)
	sec
	sbc 632
	bit one       ;up?
	beq notone
	ldy y
	cpy #32       ;is y at top?
	bcc notone
	dec y         ;dec y twice
	dec y
	stx eflag     ;flag-redraw
notone
	bit two       ;down?
	beq nottwo
	ldy y
	cpy #182      ;is y at bot?
	bcs nottwo
	inc y         ;inc y twice
	inc y
	stx eflag     ;flag-redraw
nottwo
	bit four      ;left?
	beq notfour
	ldy x
	cpy #50       ;is x leftmost?
	bcc notfour
	dec x         ;dec x twice
	dec x
notfour
	bit eight     ;right?
	beq noteight
	ldy x
	cpy #201      ;is x rtmost?
	bcs noteight
	inc x         ;inc x twice
	inc x
noteight
	ldx x         ;update xpos
	stx $d004
	inx
	inx
	stx $d005
	inx
	inx
	stx $d006     ;store in hposm2
	lda eflag     ;need to redraw?
	beq ertn      ;n:move enemies
	lda #0        ;y:redraw cross-
	sta eflag     ; hair
	tax
	ldy y
putloop
	lda $4300,y   ;get old mbyte
	and #$c0      ;save only m3
	ora pshap,x   ;force in c-hair
	sta $4300,y   ;store final byt
	inx
	iny
	cpx #12       ;done all 12?
	bcc putloop
ertn
	lda #0
	sta ec
	sta $c0       ;($c0)=ptr to plr
	lda #$44      ; band currently
	sta $c1       ; in use
	ldx ec
eloop
	lda elock,x   ;enemy locked?
	beq cktm
	jmp nexenm
cktm
	dec et,x  ;dec enm's timer
	beq dothisenm ;if zero,move him
	jmp nexenm    ;else do next enm
dothisenm
	lda ep,x      ;reset this enm's
	sta et,x      ; timer
	lda nv,x      ;get #vectrs movd
	beq dsappr    ;zero=dsappr
	bmi appear    ;neg#=appear
	jmp contertn  ;pos#=moving
dsappr
	sta ctr
	lda esc,x
	cmp #5
	bcs setapr    ;done disappring?
	asl a
	clc
	adc esc,x
	asl a
	asl a
	ldy ey,x      ;y=ptr to enm plr
	tax           ;x=ptr 2 eshp tbl
reclp
	lda eshap,x   ;get shape byte
	sta ($c0),y   ;store it in p0
	inx
	iny
	inc ctr
	lda ctr
	cmp #12
	bcc reclp
	ldx ec
	inc esc,x     ;next frame
	jmp nexenm    ;nxt enm
setapr
	lda #$ff      ;#vect ctr=neg #:
	sta nv,x      ; enm will appear
	lda ey,x
	clc
	adc #5
	sta ey,x
	tay
	lda #0        ;erase enemy
	sta ($c0),y
	lda $d20a     ;rnd enm xpos
	and #$7f
	clc
	adc #60
	sta ex,x
	lda $d20a     ;rnd enm ypos
	and #$7f
	clc
	adc #46
	sta ey,x
	jmp nexenm    ;nxt enm
appear
	dec esc,x
	bmi dnappr    ;done appearing?
	lda esc,x
	asl a
	clc
	adc esc,x
	asl a
	asl a
	ldy ey,x      ;y=ptr to enm plr
	tax           ;x=ptr to shp tbl
	lda #0
	sta ctr
aplp
	lda eshap,x   ;get enm shp byt
	sta ($c0),y   ;put it in plr
	inx
	iny
	inc ctr
	lda ctr       ;done 12 bytes?
	cmp #12
	bcc aplp
	ldx ec
	lda ex,x      ;get enm's xpos
	sta $d000,x   ;store in hpos
	jmp nexenm    ;nxt enm
dnappr
	lda $d20a     ;rnd max # vectrs
	and #$07
	clc
	adc #4
	sta mnv,x
erp=*+1
	lda #1
	sta et,x      ;enm tmr=1
	sta ep,x      ;enm tmr pse=1
	lda #1
	sta nv,x      ;#vetcs moved=1
	jmp nexenm    ;nxt enm
contertn
	lda ex,x      ;enm's x=..+dx
	clc
	adc edx,x
	sta ex,x
	cmp #48       ;off left edge?
	bcc cedir
	cmp #201      ;off right edg?
	bcs cedir
	lda ey,x      ;enm y=..+dy
	clc
	adc edy,x
	sta ey,x
	cmp #186      ;off bot edge?
	bcs cedir
	cmp #33       ;off top edge?
	bcc cedir
	inc ectr,x    ;n:inc ctr 4 enm
	lda ectr,x    ;has it moved
	cmp elim,x    ; the limit?
	bcs cedir
putenm
	ldy ey,x      ;y=ptr to enm plr
	ldx #0        ;x=ptr to shp tbl
putelp
	lda eshap,x   ;get enm shapbyt
	sta ($c0),y   ;store in enm plr
	iny
	inx
	cpx #12       ;done all 12?
	bcc putelp
	ldx ec
	lda ex,x      ;get enm xpos
	sta $d000,x   ;store in hpos
nexenm
	inc $c1 ;nxt plr band
	inc ec        ;nxt enm ctr
	ldx ec        ;done w/all 3
	cpx #3        ; enms?
	bcs retimm
	jmp eloop     ;cont w/nxt enm
retimm
	jmp $e45f     ;back to system
cedir
	lda ey,x      ;restore enm ypos
	sec
	sbc edy,x
	sta ey,x
	lda ex,x      ;restore enm xpos
	sec
	sbc edx,x
	sta ex,x
	inc nv,x      ;#vects mved=..+1
	lda nv,x      ;limit yet?
	cmp mnv,x
	bcc cntcedir
	lda #0        ;nv=0:flag-enm
	sta nv,x      ; will recede
	sta esc,x     ;rset enm shp ctr
	lda #7
	sta et,x      ;enm tmr=7
	sta ep,x      ;enm tmr pse=7
	jmp nexenm    ;update nxt enm
cntcedir
	lda #0        ;reset mvemnt ctr
	sta ectr,x
	lda 53770     ;set a new
	and #$3f      ; movement limit
	sta elim,x
	lda ex,x
	bpl posedx    ;if x=lf,dx=rt
	bmi negedx    ;if x=rt,dx=lf
newedy
	lda ey,x
	bpl posedy    ;if y=up,dy=dn
	bmi negedy    ;if y=dn,dy=up
	jmp putenm    ;draw shape
posedx
	jsr getpos    ;get rnd enm +dx
	sta edx,x
	jmp newedy
negedx
	jsr getneg    ;get rnd enm -dx
	sta edx,x
	jmp newedy
posedy
	jsr getpos    ;get rnd enm +dy
	sta edy,x
	jmp putenm
negedy
	jsr getneg    ;get rnd enm -dy
	sta edy,x
	jmp putenm
getpos
	lda 53770     ;get rnd 1-3
	and #$03
	beq getpos
	rts
getneg
	lda 53770     ;get rnd -1 to -3
	and #$03
	beq getneg
	eor #$ff
	clc
	adc #1
	rts
one
	.byte 1 ;for 'bit' instr.
two
	.byte 2 ; same
four
	.byte 4 ; same
eight
	.byte 8 ; same
y
	.byte 0 ;crosshair y
x
	.byte 0 ;crosshair x
eflag
  .byte 0 ;c-hair redraw flag
pshap
	.byte $00,$00,$0c,$0c,$0c,$3f,$3f,$0c,$0c,$0c,$00,$00 ;crsshair shape
c
	.byte 14,12,10,8,8,6,4,2 ;stars' color (luminance) table
s1
	.byte 0 ;ctr for star layer 1
s2
	.byte 0 ;                   2
s3
	.byte 0 ;                   3
s4
	.byte 0 ;                   4
s5
	.byte 0 ;                   5
s6
	.byte 0 ;                   6
s7
	.byte 0 ;                   7
s8
	.byte 0 ;                   8
ps
	.byte 1,1,2,3,4,6,9,14 ;str spd
ctr
	.byte 0 ;misc counter
dlip
	.byte $ad  ;"lda absolute"
phpos
	.word hpos ; adr for lda
	.byte $ac  ;"ldy absolute"
plt
	.word lt          ;adr for ldy
	.byte $8d,$0a,$d4 ;sta wsync
	.byte $8d,$07,$d0 ;sta hposm3
	.byte $8c,$15,$d0 ;sty colrm3
ex
	.byte 0,0,0 ;enemy xpos table
ey
	.byte 0,0,0 ;enemy ypos table
eshap
	.byte 0,0,0,0,146,186,254,198,0,0,0,0
	.byte 0,0,0,0,146,254,198,0,0,0,0,0
	.byte 0,0,0,0,84,124,68,0,0,0,0,0
	.byte 0,0,0,0,0,56,0,0,0,0,0,0
	.byte 0,0,0,0,0,16,0,0,0,0,0,0
edx
	.byte 0,0,0 ;enemy dx table
edy
	.byte 0,0,0 ;enemy dy table
ectr
	.byte 0,0,0 ;# steps traveled
elim
	.byte 0,0,0 ;max # steps to xvl
nv
	.byte 0,0,0 ;#vectors traveled
mnv
	.byte 0,0,0 ;max vects to xvel
esc
	.byte 0,0,0 ;enm shape ctr
ep
	.byte 0,0,0 ;enm timer pauses
et
	.byte 0,0,0 ;enm timers
ec
	.byte 0     ;ctr for enm mvemnt
jlock
	.byte 0
elock
	.byte 0,0,0 ;enm 'lock' status
el
	.byte 0     ;enemy firing laser
lx
	.byte 0     ;laser terminal x
ly
	.byte 0     ;laser terminal y
expshp
	.byte 20,64,10,160,4,17,132,33,4,80,2,40 ;explos shape
expctr
	.byte 0,0,0 ;explosion counter
okf
	.byte 0     ;enm ok2fire ctr
elvt
	.byte 64,128,192 ;enm lvl tbl
erpt
	.byte 3,2,1 ;enm rtn pause tbl
ln
	.byte 0     ;level #
sp
	.byte 0     ;enemy speed
smsg
	.byte "    �����������Π���  option-level:1    "
	.byte "    ����������������  select-speed:1    "
	.byte "    ��������������  start -play game  "
	.byte "    �����㩠��������  space -pause      "
gmsg
	.byte "    �����������Π���  shield energy:70  "
	.byte "    ����������������  enemies left :99  "
lngm=*+37
	.byte "    ��������������  level number : 1  "
spgm=*+37
	.byte "    �����㩠��������  enemy speed  : 1  "
wmsg
	.byte "    �����������Π���  ���Ġ��¡��ՠ��Ρ "
	.byte "    ����������������  �������Ӡ����Լ�� "
lmsg
	.byte "    �����������Π���you lose-push start "
shield
	.byte 0 ;shield energy
rem
	.byte 0   ;#enm left
r
	.byte 0,0,0 ;enm unlock flag
graphics
	pha          ;save orig. #
	ldx #$60     ;iocb 6(screen)
	lda #12      ;close #6
	sta $342,x   ;(just to be
	jsr $e456    ; safe!)
	lda #3       ;open #6
	sta $342,x   ;command #
	lda #scrdev&255 ;addr of "s:"
	sta $344,x   ;lo byte
	lda #scrdev/256 ;and now the
	sta $345,x   ;    hi byte
	lda #1       ;length of scrn
	sta $348,x   ; i.d. is only
	lda #0       ; one character
	sta $349,x   ; (the 's')
	pla          ;get it back
	pha          ;but still save
	eor #16      ;reverse bit 5
	and #16      ;keep only bit 5
	clc          ;add 12 to it
	adc #12
	sta $34a,x   ;=icax1 spec
	pla          ;orig. mode #=
	sta $34b,x   ; icax2 spec
	jmp $e456    ;and jmp to cio!
color
	sta colnum    ;store it for
	rts          ; later use
position
	sty 84       ;vert pos
	stx 85       ;hor pos lo byte
	sta 86       ;hor pos hi byte
	rts          ;bye!
plot
	jsr position ;position cursor
	ldx #$60     ;screen (iocb6)
	lda #11      ;put chars comd
	sta $342,x   ;store in iccom
	lda #$00     ;buflen of zero
	sta $348,x   ; means get/put
	sta $349,x   ; data to/from
	;               the accum.
	lda colnum   ;put color # in
	;               accu b/c len=0
	jmp $e456    ;jmp to cio
drawto
	jsr position ;position cursr
	ldx #$60     ;scrn (iocb6)
	lda #17      ;draw line cmd
	sta $342,x   ;store in iccom
	lda #0       ;zero buf len
	sta $348,x   ; b/c no data
	sta $349,x   ; is xferred!
	lda colnum   ;store col # in
	sta $02fb    ; 2fb for cio
	jmp $e456    ;and go to cio
scrdev
	.byte "s"    ;screen i.d.
colnum
	brk          ;color# storage
hpos
	*=*+192      ;tbl str pos
lt
	*=*+192      ;tbl str lum
	*=$02e0
	.word bp     ;dos run adr
