/*
 * mkfont - build an Atari character set (1024 bytes, 128 glyphs of 8 bytes in
 * the order of the Atari internal screen codes) out of a C64 character ROM.
 *
 * usage: mkfont chargen.bin font.bin
 *
 * chargen.bin is the 4096 byte C64 character ROM (for example VICE's
 * chargen-901225-01.bin): set 1 (upper case and graphics) in the first 2048
 * bytes and set 2 (lower case) in the next 2048; each set has the 256 screen
 * codes, the second half being the inverted glyphs, which the Atari makes by
 * itself from bit 7 of the screen code.  The ROM is Commodore's, so the output
 * is not part of the repository: the Makefile builds it from a local copy.
 *
 * Atari internal code        taken from the C64
 *   $00-$1F  space ! " # ... ?  screen codes 32-63 (digits, punctuation)
 *   $20      @                  screen code 0
 *   $21-$3A  A-Z                set 2, screen codes 65-90 (the upper case of
 *                               the lower case set)
 *   $3B-$3F  [ \ ] ^ _          screen codes 27-31 ([ pound ] up-arrow left-arrow)
 *   $40-$5F  graphics           set 1, screen codes 64-95
 *   $60      (graphic)          set 1, screen code 96
 *   $61-$7A  a-z                set 2, screen codes 1-26
 *   $7B-$7F  graphics           set 1, screen codes 123-127
 *
 * Both machines use the same bit order (bit 7 is the leftmost pixel), so the
 * glyphs are copied byte for byte.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
	static unsigned char rom[4096], font[1024];
	FILE *f;
	int a;

	if (argc != 3) {
		fprintf(stderr, "usage: mkfont chargen.bin font.bin\n");
		return 2;
	}
	f = fopen(argv[1], "rb");
	if (!f || fread(rom, 1, sizeof rom, f) != sizeof rom) {
		fprintf(stderr, "mkfont: %s: cannot read 4096 bytes\n", argv[1]);
		return 1;
	}
	fclose(f);

	for (a = 0; a < 128; a++) {
		const unsigned char *g;

		if (a < 0x20)
			g = rom + (a + 32) * 8;			/* set 1 */
		else if (a == 0x20)
			g = rom;				/* @ */
		else if (a <= 0x3A)
			g = rom + 2048 + (65 + a - 0x21) * 8;	/* set 2: A-Z */
		else if (a <= 0x3F)
			g = rom + (27 + a - 0x3B) * 8;
		else if (a <= 0x5F)
			g = rom + (64 + a - 0x40) * 8;
		else if (a == 0x60)
			g = rom + 96 * 8;
		else if (a <= 0x7A)
			g = rom + 2048 + (1 + a - 0x61) * 8;	/* set 2: a-z */
		else
			g = rom + (123 + a - 0x7B) * 8;
		memcpy(font + a * 8, g, 8);
	}

	f = fopen(argv[2], "wb");
	if (!f || fwrite(font, 1, sizeof font, f) != sizeof font || fclose(f)) {
		fprintf(stderr, "mkfont: cannot write %s\n", argv[2]);
		return 1;
	}
	return 0;
}
