#include <stdio.h>
#include <conio.h>

/* sp-common.asm: POKEY player running in the deferred vertical blank */
extern void setupAndStartPlayer(void);
extern void stopPlayer(void);

int main(void)
{
	printf("sid2pokey\n\nPlaying... press a key to stop.\n");
	setupAndStartPlayer();
	cgetc();
	stopPlayer();
	return 0;
}
