#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <atari.h>
#include <cc65.h>
#include <6502.h>
#include <stdlib.h>

extern int setupAndStartPlayer();

#define COLPF2	0xd018
#define ZTIMER  0xcb
#define OSROMSELECTION (1 << 0)
#define PORTB   0xd301

/*
 * DLI 192 Display List interrupts (one each scanline)
 * get from a table (192 bytes full of x-coordinates) using an index
 *
 * index = $ZEROPAGE_INDEX  ; 1 byte
 * tabaddr = $ZEROPAGE_ADDR ; 2 bytes
 * dli
 * 		ldx $index
 * 		lda (tabaddr),x
 * 		sta hposm0
 * 		inx
 * 		cmp 192
 * 		beq resetindex
 * 		rti
 * resetindex
 *      lda #0
 *      sta $index
 *      rti
 */
#define SCANLINES 192
static unsigned char index = 0;
static unsigned char * hpos = (unsigned char *) 0xd200;
static unsigned char htab[ SCANLINES ];

void dli(void)
{
	*(hpos) = htab[index];
	++index;
	if (index > SCANLINES)
		index = 0;
	__asm__("rti");
}

/* VBI interrupts
 *
 * Increase by one every element of the table of hpos
 * every 8 blanks
 *
 * mcount = $ZEROPAGE_MCOUNTER
 * vbi
 * 		lda mcount
 * 		cmp #1
 * 		beq mov1
 * 		cmp #2
 * 		beq mov2
 * 		cmp #3
 * 		beq mov3
 * 		cmp #4
 * 		beq mov4
 * 		cmp #5
 * 		beq mov5
 * 		cmp #6
 * 		beq mov6
 * 		cmp #7
 * 		beq mov7
 * 		cmp #8
 * 		beq mov8
 *      lda #1
 *      sta mcount
 *      jmp vbi
 * outvbi
 *      jmp xitvbv
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov2
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      inc
 *      inx
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov2
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 * mov1
 *      ldx mcount
 *      lda (tabaddr),x
 *      inc
 *      sta (tabaddr),x
 *      jmp outvbi
 */
void vbi(void)
{
	static unsigned char counter = 0;
	unsigned char x;
	for (x = 0; x < SCANLINES; x++)
	{
	}
}

int main(void)
{
	unsigned char x;
	unsigned char *ztimer = (unsigned char *) ZTIMER;
	unsigned char c;

#ifdef __ATARIXL__
	// select OS ROM by default
	c = *((unsigned char *) PORTB);
	c |= (OSROMSELECTION);
	*((unsigned char *) PORTB) = c;
	__asm__("nop");
	__asm__("nop");
	__asm__("nop");
	__asm__("nop");
#endif

	srand(0xdeadbeef);
	setupAndStartPlayer();
	x = 10;
	for (;;)
	{
		c = cgetc();
		if (c == 'A' || c == 'a')
			++x;
		if (c == 'S' || c == 's')
			--x;
		if (x < 1)
			x = 1;
		if (x > 254)
			x = 254;
		printf("X: %d\n", x);
		//*(ztimer) = x;
	}
	return 0;
}
