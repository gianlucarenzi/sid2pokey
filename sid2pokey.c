#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <atari.h>
#include <cc65.h>
#include <6502.h>
#include <stdlib.h>

extern int setupAndStartPlayer();

#define CRAZY_COLOR		*((unsigned char *) 0xD018) = rand();
int main(void)
{
	char x;
	unsigned char *ztimer = (unsigned char *) 0x8f;
	unsigned char c;
	srand(0xdeadbeef);
	setupAndStartPlayer();
	for (;;)
	{
		x = rand();
		*((unsigned char *) 0xD018) = x;
		*(ztimer) = x;
	}
	return 0;
}
