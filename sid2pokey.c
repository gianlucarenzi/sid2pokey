/*
 * sid2pokey - front end of the player: a C64 style text screen with the title of
 * the tune and a VU meter for every SID voice.  The music itself is played by
 * the interrupt code in sp-common.asm; this program only draws.
 */
#include <string.h>

/* sp-common.asm: POKEY player running in the deferred vertical blank */
extern unsigned char play_k;		/* records per video frame (1 = normal) */
extern unsigned char play_chips;	/* POKEYs the tune is written for (1 or 2) */
extern unsigned char have_stereo;	/* $80 if a second POKEY answers at $D210 */
extern unsigned char outbuf[16];	/* the POKEY values of the last record */
extern unsigned play_left;		/* frames still to play */
extern unsigned play_frames;		/* frames in the stream */
extern void initPlayer(void);
extern void startPlayer(void);
extern void stopPlayer(void);

/* sp-data.asm: the converted tune.  Header layout: see tools/sidconv.c */
extern unsigned char song_data[];
#define H_VIDEO_HZ	1
#define H_VU		7		/* per voice: register with its volume, or $FF */
#define H_TITLE		13		/* 3 x 32 bytes: title, author, copyright */
#define H_AUTHOR	45
#define H_COPYRIGHT	77

/* sp-font.asm: the C64 character set built by tools/mkfont (empty if none) */
extern unsigned char font_data[];
extern unsigned char font_end[];

/* colours: the hue (high nibble) of the background, the text and the border */
#ifndef UI_HUE
#define UI_HUE	0x70
#endif

/* operating system */
#define SAVMSC	(*(unsigned char **) 0x0058)	/* screen memory */
#define ATRACT	(*(unsigned char *) 0x004D)	/* attract mode counter */
#define RTCLOK	(*(volatile unsigned char *) 0x0014)	/* jiffy clock, low byte */
#define MEMTOP	(*(unsigned *) 0x02E5)
#define COLOR1	(*(unsigned char *) 0x02C5)	/* text luminance */
#define COLOR2	(*(unsigned char *) 0x02C6)	/* background */
#define COLOR4	(*(unsigned char *) 0x02C8)	/* border */
#define CHBAS	(*(unsigned char *) 0x02F4)	/* character set page (shadow) */
#define CRSINH	(*(unsigned char *) 0x02F0)	/* 1 = no cursor */
#define CH	(*(volatile unsigned char *) 0x02FC)	/* last key pressed, $FF = none */
#define SKSTAT	(*(volatile unsigned char *) 0xD20F)	/* POKEY: bit 2 clear = a key is down */
#define SDLSTL	(*(unsigned *) 0x0230)	/* OS shadow of the display list pointer */
#define PALNT	(*(unsigned char *) 0xD014)	/* GTIA: 1 on PAL, $0F on NTSC */

/* ------------------------------------------------------------------ */
/* Multispeed: DLIs                                                    */
/* ------------------------------------------------------------------ */

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

/* ------------------------------------------------------------------ */
/* Character set                                                       */
/* ------------------------------------------------------------------ */

/*
 * Glyphs the screen needs whatever the base set is (the C64 set from font.bin,
 * or the Atari one).  Internal screen codes: the Atari uses $40-$5F for control
 * graphics and $60-$7F for lower case, the free ones are taken here.
 */
#define G_H	0x40			/* horizontal line */
#define G_V	0x5D			/* vertical line */
#define G_TL	0x60			/* corners */
#define G_TR	0x7B
#define G_BL	0x7C
#define G_BR	0x7D
#define G_LVL	0x47			/* + k (1..7): the bottom k pixel rows filled */
#define G_PEAK	0x50			/* + r (1..7): one line, r rows from the top */

static const unsigned char gl_h[8]  = { 0, 0, 0, 0xFF, 0xFF, 0, 0, 0 };
static const unsigned char gl_v[8]  = { 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18 };
static const unsigned char gl_tl[8] = { 0, 0, 0, 0x1F, 0x1F, 0x18, 0x18, 0x18 };
static const unsigned char gl_tr[8] = { 0, 0, 0, 0xF8, 0xF8, 0x18, 0x18, 0x18 };
static const unsigned char gl_bl[8] = { 0x18, 0x18, 0x18, 0x1F, 0x1F, 0, 0, 0 };
static const unsigned char gl_br[8] = { 0x18, 0x18, 0x18, 0xF8, 0xF8, 0, 0, 0 };

/*
 * Put a character set in RAM and make the screen use it.
 *
 *  - XL/XE (the atarixl target): cc65 keeps the OS ROM switched off and has
 *    already copied the ROM font to RAM at $E000, so the font is patched where it
 *    is, and CHBAS stays $E0.
 *  - 400/800 (the atari target): the linker was told to keep 2 KB at the top of
 *    RAM free (Makefile, __RESERVED_MEMORY__); the character set needs an address
 *    on a 1 KB boundary, which is found in that block.  Without a C64 font the OS
 *    font is copied from the ROM first.
 */
static void install_font(void)
{
	unsigned char *font, *g;
	unsigned char k, r;

#if defined(__ATARIXL__)
	font = (unsigned char *) 0xE000;
#elif defined(FONT_TOP)
	font = (unsigned char *) ((MEMTOP + 1 - 0x400) & 0xFC00);
	memcpy(font, (void *) 0xE000, 0x400);
#else
#error "the plain atari target needs the reserved memory of the Makefile (-DFONT_TOP)"
#endif
	if (font_end - font_data >= 0x400)
		memcpy(font, font_data, 0x400);

	memcpy(font + G_H * 8, gl_h, 8);
	memcpy(font + G_V * 8, gl_v, 8);
	memcpy(font + G_TL * 8, gl_tl, 8);
	memcpy(font + G_TR * 8, gl_tr, 8);
	memcpy(font + G_BL * 8, gl_bl, 8);
	memcpy(font + G_BR * 8, gl_br, 8);
	for (k = 1; k < 8; ++k) {
		g = font + (G_LVL + k) * 8;
		for (r = 0; r < 8; ++r)
			g[r] = (r >= 8 - k) ? 0xFF : 0;	/* bottom k rows */
		g = font + (G_PEAK + k) * 8;
		memset(g, 0, 8);
		g[k] = 0xFF;				/* the row k from the top */
	}
	CHBAS = (unsigned char) ((unsigned) font >> 8);
}

/* ------------------------------------------------------------------ */
/* Screen                                                              */
/* ------------------------------------------------------------------ */

static unsigned char *scr;		/* screen memory, 40 x 24 */
#define SCR(r, c) (scr + (r) * 40 + (c))

/* ASCII -> internal screen code (the font is only defined for $20-$7A) */
static unsigned char scode(unsigned char c)
{
	if (c < 0x20 || c > 0x7A)
		return 0x1F;			/* ? */
	if (c < 0x60)
		return c - 0x20;
	if (c == 0x60)
		return 0x07;			/* ` -> ' */
	return c;
}

/* A field of n characters at row, col: the string (0 ends it), then spaces. */
static void put_str(unsigned char row, unsigned char col, const unsigned char *s,
		    unsigned char n, unsigned char inv)
{
	unsigned char *p = SCR(row, col);
	unsigned char i, c;

	for (i = 0; i < n; ++i) {
		c = *s ? scode(*s++) : 0;
		p[i] = c | inv;
	}
}

#define ROW_VU_TOP	9		/* VU meter area: 9 rows, bottom one at 17 */
#define ROW_VU_BOTTOM	17
#define VU_ROWS		9
#define CELL		7		/* levels in a cell: 7 pixel rows, 1 blank */
#define VU_MAX		(VU_ROWS * CELL)

static void box(unsigned char r0, unsigned char r1)
{
	unsigned char r, *p;

	p = SCR(r0, 0);
	p[0] = G_TL;
	memset(p + 1, G_H, 38);
	p[39] = G_TR;
	for (r = r0 + 1; r < r1; ++r) {
		p = SCR(r, 0);
		p[0] = G_V;
		p[39] = G_V;
	}
	p = SCR(r1, 0);
	p[0] = G_BL;
	memset(p + 1, G_H, 38);
	p[39] = G_BR;
}

/* The voice meters: columns of the bars (1 or 2 groups of 3). */
static unsigned char nvoices;
static unsigned char bar_w;
static unsigned char bar_col[6];

static void layout(void)
{
	static const unsigned char col1[3] = { 5, 17, 29 };
	static const unsigned char col2[6] = { 2, 8, 14, 22, 28, 34 };
	unsigned char v;

	if (play_chips > 1) {
		nvoices = 6;
		bar_w = 4;
		for (v = 0; v < 6; ++v)
			bar_col[v] = col2[v];
	} else {
		nvoices = 3;
		bar_w = 6;
		for (v = 0; v < 3; ++v)
			bar_col[v] = col1[v];
	}
}

static void draw_static(unsigned char hz, unsigned char ntsc_machine)
{
	unsigned char v, c;

	scr = SAVMSC;
	memset(scr, 0, 40 * 24);	/* not clrscr(): an OS call switches the ROM on (XL/XE) */

	/* title bar */
	put_str(0, 0, (const unsigned char *) " SID 2 POKEY          C64 MUSIC ON ATARI ", 40, 0x80);

	/* the tune */
	box(2, 6);
	put_str(3, 2, song_data + H_TITLE, 32, 0);
	put_str(4, 2, song_data + H_AUTHOR, 32, 0);
	put_str(5, 2, song_data + H_COPYRIGHT, 32, 0);

	/* the meters */
	box(8, 21);
	put_str(8, 3, (const unsigned char *) " VOICES ", 8, 0);
	for (v = 0; v < nvoices; ++v) {
		c = bar_col[v] + bar_w / 2 - 1;
		*SCR(18, c) = 0x11 + (v % 3);		/* 1 2 3 */
	}
	if (play_chips > 1) {
		put_str(19, 3, (const unsigned char *) "POKEY 1", 7, 0);
		put_str(19, 24, (const unsigned char *) "POKEY 2", 7, 0);
	} else {
		put_str(19, 14, (const unsigned char *) "SID 1 - POKEY", 13, 0);
	}

	/* what we are playing */
	if (play_chips > 1)
		put_str(22, 1, (const unsigned char *) (have_stereo ? "2 POKEYS (STEREO)" : "SID 1 ONLY: NO 2ND POKEY"), 24, 0);
	else
		put_str(22, 1, (const unsigned char *) "1 POKEY", 7, 0);
	*SCR(22, 26) = 0x10 + hz / 10;
	*SCR(22, 27) = 0x10 + hz % 10;
	put_str(22, 28, (const unsigned char *) "HZ", 2, 0);
	*SCR(22, 31) = 0x10 + play_k;
	*SCR(22, 32) = 'X' - 0x20;
	if (song_data[H_VIDEO_HZ] != (ntsc_machine ? 60 : 50))
		put_str(1, 1, (const unsigned char *) "TUNE AND MACHINE USE DIFFERENT FRAME RATES", 38, 0);
}

static void draw_state(unsigned char playing)
{
	put_str(23, 0, (const unsigned char *) (playing ?
		" PLAYING - PRESS ANY KEY TO STOP         " :
		" STOPPED - PRESS ANY KEY TO PLAY         "), 40, 0x80);
}

/* ------------------------------------------------------------------ */
/* VU meters                                                           */
/* ------------------------------------------------------------------ */

#define FALL	3			/* levels per frame */
#define HOLD	24			/* frames the peak marker stays */

/* volume 0..15 -> level 0..VU_MAX (63) */
static const unsigned char lvl[16] = {
	0, 4, 8, 13, 17, 21, 25, 29, 34, 38, 42, 46, 50, 55, 59, 63
};

static unsigned char disp[6];		/* displayed level */
static unsigned char peak[6];		/* peak marker position, 0 = none */
static unsigned char hold[6];

static void vu_clear(void)
{
	memset(disp, 0, sizeof disp);
	memset(peak, 0, sizeof peak);
	memset(hold, 0, sizeof hold);
}

/* One bar, from the bottom cell up. */
static void draw_bar(unsigned char v)
{
	unsigned char *p = SCR(ROW_VU_BOTTOM, bar_col[v]);
	unsigned char level = disp[v], pk = peak[v];
	unsigned char i, base, code, pcell = 255, top = 255;

	if (pk > level) {
		pcell = (pk - 1) / CELL;
		top = level ? (level - 1) / CELL : 255;	/* the cell of the bar's top */
		if (level && pcell <= top)
			pcell = 255;			/* same cell: no marker */
	}
	for (i = 0, base = 0; i < VU_ROWS; ++i, base += CELL, p -= 40) {
		if (level >= base + CELL)
			code = G_LVL + CELL;
		else if (level > base)
			code = G_LVL + (level - base);
		else if (i == pcell)
			code = G_PEAK + (CELL - (pk - 1) % CELL);
		else
			code = 0;
		memset(p, code, bar_w);
	}
}

static void vu_update(void)
{
	unsigned char v, reg, vol, now;

	for (v = 0; v < nvoices; ++v) {
		reg = song_data[H_VU + v];
		vol = (reg < 16) ? (outbuf[reg] & 15) : 0;
		now = lvl[vol];
		if (now >= disp[v])
			disp[v] = now;
		else
			disp[v] = disp[v] > FALL ? disp[v] - FALL : 0;
		if (disp[v] >= peak[v]) {
			peak[v] = disp[v];
			hold[v] = HOLD;
		} else if (hold[v]) {
			--hold[v];
		} else if (peak[v]) {
			--peak[v];
		}
		draw_bar(v);
	}
}

/* ------------------------------------------------------------------ */
/* Time                                                                */
/* ------------------------------------------------------------------ */

static unsigned last_sec = 0xFFFF;

static void put_time(unsigned char col, unsigned sec)
{
	unsigned char m = (unsigned char) (sec / 60), s = (unsigned char) (sec % 60);
	unsigned char *p = SCR(22, col);

	p[0] = 0x10 + m / 10;
	p[1] = 0x10 + m % 10;
	p[2] = ':' - 0x20;
	p[3] = 0x10 + s / 10;
	p[4] = 0x10 + s % 10;
}

static void time_update(unsigned char hz)
{
	unsigned sec = (play_frames - play_left) / hz;

	if (sec != last_sec) {
		last_sec = sec;
		put_time(34, sec);
	}
}

/* ------------------------------------------------------------------ */

/*
 * The keyboard is read from CH, the OS keeps the last key there, and not with
 * cgetc() (nor kbhit()): cgetc() asks the screen editor, which echoes the key on
 * the screen at the cursor (a hole in the title bar for every key) and, on the
 * XL/XE, keeps the OS ROM on until it returns.
 */
static unsigned char key_pressed(void)
{
	return CH != 0xFF;
}

/* Take the key, after it is released (a key held down repeats). */
static void eat_key(void)
{
	while (!(SKSTAT & 0x04))
		;
	CH = 0xFF;
}

/* One video frame; also keeps the attract mode (colour cycling) away. */
static void wait_frame(void)
{
	unsigned char t = RTCLOK;

	while (RTCLOK == t)
		;
	ATRACT = 0;
}

int main(void)
{
	unsigned char ntsc = (PALNT & 0x0E) != 0;
	unsigned char hz = song_data[H_VIDEO_HZ];
	unsigned char t;

	install_font();
	CRSINH = 1;
	CH = 0xFF;
	COLOR4 = UI_HUE | 0x0A;		/* border: light blue */
	COLOR2 = UI_HUE | 0x04;		/* background: dark blue */
	COLOR1 = 0x0C;			/* text: light, same hue as the background */

	/*
	 * Never return: without a DOS, exiting to "DOS" ends in the OS booting
	 * again (BOOT ERROR on the XL/XE).  A key press stops the tune, the next
	 * one plays it again from the start.
	 */
	for (;;) {
		initPlayer();
		layout();
		draw_static(hz, ntsc);
		vu_clear();
		last_sec = 0xFFFF;
		draw_state(1);
		if (play_k > 1)
			patchDisplayList(play_k, ntsc);
		startPlayer();
		while (!key_pressed()) {
			wait_frame();
			vu_update();
			time_update(hz);
		}
		eat_key();
		stopPlayer();
		unpatchDisplayList();
		vu_clear();
		for (t = 0; t < nvoices; ++t)
			draw_bar(t);
		draw_state(0);
		while (!key_pressed())
			wait_frame();
		eat_key();
	}
}
