/*
 * main.c - skeleton of the front end: start the player, wait for a key, stop it.
 * Everything else (the screen, the font, the VU meters) is in ../sid2pokey.c.
 */
#include <stdio.h>
#include <conio.h>

extern void playerInit(void);
extern void playerStart(void);
extern void playerStop(void);

int main(void)
{
	printf("SID2POKEY SKELETON\n\nPlaying. Press a key to stop.\n");
	playerInit();
	playerStart();		/* from now on the music plays by itself */
	cgetc();
	playerStop();
	printf("Stopped.\n");
	for (;;)		/* never return to DOS: without one the XL/XE reboots */
		;
}
