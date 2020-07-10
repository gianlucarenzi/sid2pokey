#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <atari.h>
#include <cc65.h>
#include <6502.h>
#include <stdlib.h>
#include <peekpoke.h>
extern int setupAndStartPlayer();

#define COLPF2	0xd018
#define ZTIMER  0xcb
#define OSROMSELECTION (1 << 0)
#define PORTB   0xd301

int main(void)
{
	unsigned char x;
	unsigned char *ztimer = (unsigned char *) ZTIMER;
	unsigned char c;

	srand(0xdeadbeef);
	setupAndStartPlayer();

	c = *((unsigned char *) PORTB);
	c |= (OSROMSELECTION);
	*((unsigned char *)PORTB) = c;

	for (;;)
	{
		x = rand();
		*((unsigned char *)COLPF2) = x;
		*(ztimer) = x;
	}
	return 0;
}
