#include <stdio.h>
#include <conio.h>

/* sp-common.asm: POKEY player running in the deferred vertical blank */
extern unsigned char play_k;		/* records per video frame (1 = normal) */
extern void initPlayer(void);
extern void startPlayer(void);
extern void stopPlayer(void);

/* sp-data.asm: the converted tune; byte 1 of the header is the video rate */
extern unsigned char song_data[];

#define SDLSTL	(*(unsigned *) 0x0230)	/* OS shadow of the display list pointer */
#define PALNT	(*(unsigned char *) 0xD014)	/* GTIA: 1 on PAL, $0F on NTSC */
#define NMI_LINE 248			/* scanline of the vertical blank NMI */

#define MAX_INS 48			/* display list instructions we look at */
#define MAX_DLI 3

static unsigned char *dli_ins[MAX_DLI];	/* instructions we gave a DLI bit */
static unsigned char dli_n;

/* scanlines of an ANTIC mode line, indexed by the low nibble of the opcode */
static const unsigned char mode_lines[16] = {
	0, 0, 8, 10, 8, 16, 8, 16, 8, 4, 4, 2, 1, 2, 1, 1
};

/*
 * Multispeed: the first record of a frame is played by the VBI, the other
 * k-1 by display list interrupts.  Set the DLI bit on the display list
 * instructions whose last scanline is closest to the points that split the
 * frame (counted from the VBI) in k equal parts.
 */
static void patchDisplayList(unsigned char k, unsigned char ntsc)
{
	static unsigned char *ins_p[MAX_INS];
	static int ins_fire[MAX_INS];
	unsigned char *p = (unsigned char *) SDLSTL;
	unsigned char n = 0, i, j, op;
	int line = 8, h, frame = ntsc ? 262 : 312, target, d, bestd;
	signed char best;

	for (;;) {
		op = *p;
		if ((op & 0x0F) == 1) {			/* JMP or JVB */
			if (op & 0x40)
				break;			/* JVB: end of the list */
			p = (unsigned char *) (p[1] | (p[2] << 8));
			continue;
		}
		if ((op & 0x0F) == 0) {			/* blank lines */
			h = ((op >> 4) & 7) + 1;
			i = 1;
		} else {				/* mode line (+LMS) */
			h = mode_lines[op & 0x0F];
			i = (op & 0x40) ? 3 : 1;
		}
		if (n < MAX_INS) {
			ins_p[n] = p;
			ins_fire[n] = line + h - 1;	/* DLI: last scanline */
			++n;
		}
		line += h;
		p += i;
	}

	dli_n = 0;
	for (j = 1; j < k && dli_n < MAX_DLI; ++j) {
		target = (NMI_LINE + j * frame / k) % frame;
		best = -1;
		bestd = 32767;
		for (i = 0; i < n; ++i) {
			if (*ins_p[i] & 0x80)
				continue;		/* already has a DLI */
			d = ins_fire[i] - target;
			if (d < 0)
				d = -d;
			if (d < bestd) {
				bestd = d;
				best = i;
			}
		}
		if (best < 0)
			break;
		*ins_p[best] |= 0x80;
		dli_ins[dli_n++] = ins_p[best];
	}
}

static void unpatchDisplayList(void)
{
	while (dli_n)
		*dli_ins[--dli_n] &= 0x7F;
}

int main(void)
{
	unsigned char ntsc = (PALNT & 0x0E) != 0;

	printf("sid2pokey\n\n");
	if (song_data[1] != (ntsc ? 60 : 50))
		printf("Warning: tune converted for %d Hz,\nthis machine is %d Hz.\n\n",
		       song_data[1], ntsc ? 60 : 50);

	/*
	 * Never return: without a DOS, exiting to "DOS" ends in the OS booting
	 * again (BOOT ERROR on the XL/XE).  A key press stops the tune, the next
	 * one plays it again from the start.
	 */
	for (;;) {
		printf("Playing... press a key to stop.\n");
		initPlayer();
		if (play_k > 1)
			patchDisplayList(play_k, ntsc);
		startPlayer();
		cgetc();
		stopPlayer();
		unpatchDisplayList();
		printf("Stopped.  Press a key to play again.\n");
		cgetc();
	}
	return 0;
}
