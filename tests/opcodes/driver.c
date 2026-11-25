/*
 * Runs opc.prg (see gen.py) in tools/cpu6502.h and prints the result records
 * ($8000, 8 bytes each: A X Y P SP address-lo address-hi value), one per line.
 *
 *   driver opc.prg <cases> <start address>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cpu6502.h"

static unsigned char mem[65536];
static uint8_t rd(void *c, uint16_t a) { (void)c; return mem[a]; }
static void wr(void *c, uint16_t a, uint8_t v) { (void)c; mem[a] = v; }

int main(int argc, char **argv)
{
	static unsigned char buf[65536];
	int ncases, start, i, k;
	long steps;
	cpu6502_t c;
	size_t n;
	FILE *f;

	if (argc != 4)
		return 2;
	f = fopen(argv[1], "rb");
	if (!f)
		return 2;
	ncases = atoi(argv[2]);
	start = (int)strtol(argv[3], NULL, 0);
	n = fread(buf, 1, sizeof buf, f);
	fclose(f);
	memcpy(mem + 0x0801, buf + 2, n - 2);		/* skip the load address */
	memset(&c, 0, sizeof c);
	c.read = rd;
	c.write = wr;
	c.sp = 0xFF;
	c.pc = (uint16_t)start;
	/* the program stores $A5 at $9FFF when it is done */
	for (steps = 0; steps < 50000000 && mem[0x9FFF] != 0xA5; steps++) {
		if (cpu_step(&c) < 0) {
			fprintf(stderr, "bad opcode %02X at %04X\n", c.bad_op, c.bad_pc);
			return 1;
		}
	}
	if (mem[0x9FFF] != 0xA5) {
		fprintf(stderr, "the program did not finish\n");
		return 1;
	}
	for (i = 0; i < ncases; i++) {
		for (k = 0; k < 8; k++)
			printf("%02x", mem[0x8000 + 8 * i + k]);
		printf("\n");
	}
	return 0;
}
