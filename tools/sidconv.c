/*
 * sidconv - convert a PSID tune into a POKEY register stream for Atari.
 *
 * The SID file contains 6502 code (init/play routines).  We run that code
 * on a 6502 emulator, record what it writes to the SID registers on each
 * call of the play routine, model the three SID voices (waveform, pitch,
 * ADSR envelope) and map them to POKEY AUDF/AUDC registers, one Atari
 * video frame at a time.  The result is a small delta-coded stream that a
 * tiny 6502 player (sp-common.asm) replays from the vertical blank.
 *
 * Output stream format (all values bytes):
 *
 *   header:  AUDCTL, video_hz (50|60), frames (16 bit little endian)
 *   frame:   mask, then one byte for each set bit of mask
 *            bit n of mask -> register $D200+n:
 *              AUDF1 AUDC1 AUDF2 AUDC2 AUDF3 AUDC3 AUDF4 AUDC4
 *            registers whose bit is clear keep their previous value.
 *
 * The first frame always writes all eight registers, so the stream can be
 * looped by simply restarting from the first frame.
 *
 * Current mapping (first milestone, see TODO in the README):
 *   - SID voice 1..3 -> POKEY channel 1..3, 64 kHz base clock, 8 bit
 *     dividers (AUDCTL = 0); channel 4 unused.
 *   - pitch below the 64 kHz range (about 124 Hz) is folded up by octaves.
 *   - noise waveform -> distortion $8x (17 bit poly), everything else
 *     -> pure tone $Ax.  Filter, ring modulation, sync and PWM are ignored.
 *   - volume = ADSR envelope (frame-rate approximation) * master volume.
 *   - multispeed tunes are decimated to one play call per video frame.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>
#include <math.h>

#include "cpu6502.h"

#define TRAP_ADDR	0xFFF0		/* RTS of INIT/PLAY returns here */
#define INIT_STEPS	50000000L	/* runaway guard, instructions */
#define PLAY_STEPS	2000000L

#define PAL_SID_CLK	985248.0
#define NTSC_SID_CLK	1022727.0
#define PAL_VBI_HZ	(PAL_SID_CLK / (312.0 * 63.0))	/* C64 PAL  frame rate */
#define NTSC_VBI_HZ	(NTSC_SID_CLK / (263.0 * 65.0))	/* C64 NTSC frame rate */

#define PAL_CPU_CLK	1773447.0	/* Atari 6502/POKEY clock */
#define NTSC_CPU_CLK	1789773.0
#define PAL_ATARI_HZ	(PAL_CPU_CLK / (312.0 * 114.0))
#define NTSC_ATARI_HZ	(NTSC_CPU_CLK / (262.0 * 114.0))

#define MAX_FRAMES	65535

/* ------------------------------------------------------------------ */

static void die(const char *fmt, ...)
{
	va_list ap;

	fprintf(stderr, "sidconv: ");
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fputc('\n', stderr);
	exit(1);
}

/* ------------------------------ PSID ------------------------------- */

typedef struct {
	char     magic[5];
	int      version;
	int      load, init, play;
	int      songs, start;
	uint32_t speed;
	int      flags;
	char     title[33], author[33], copyright[33];
	uint8_t *data;		/* payload (without the load address word) */
	size_t   len;
	uint8_t *file;		/* whole file, owns the memory */
} psid_t;

static unsigned be16(const uint8_t *p) { return (unsigned)(p[0] << 8 | p[1]); }

static void psid_load(psid_t *s, const char *path)
{
	FILE *f = fopen(path, "rb");
	size_t size, hdr;
	long end;

	if (!f)
		die("cannot open %s", path);
	fseek(f, 0, SEEK_END);
	end = ftell(f);
	fseek(f, 0, SEEK_SET);
	if (end < 0x76)
		die("%s: too short for a PSID file", path);
	size = (size_t)end;
	s->file = malloc(size);
	if (!s->file || fread(s->file, 1, size, f) != size)
		die("%s: read error", path);
	fclose(f);

	memset(s->magic, 0, sizeof s->magic);
	memcpy(s->magic, s->file, 4);
	if (strcmp(s->magic, "PSID") && strcmp(s->magic, "RSID"))
		die("%s: not a PSID/RSID file", path);

	s->version = (int)be16(s->file + 4);
	hdr        = be16(s->file + 6);
	s->load    = (int)be16(s->file + 8);
	s->init    = (int)be16(s->file + 10);
	s->play    = (int)be16(s->file + 12);
	s->songs   = (int)be16(s->file + 14);
	s->start   = (int)be16(s->file + 16);
	s->speed   = (uint32_t)be16(s->file + 18) << 16 | be16(s->file + 20);
	s->flags   = (s->version >= 2 && size >= 0x7C) ? (int)be16(s->file + 0x76) : 0;

	memcpy(s->title,     s->file + 0x16, 32); s->title[32] = 0;
	memcpy(s->author,    s->file + 0x36, 32); s->author[32] = 0;
	memcpy(s->copyright, s->file + 0x56, 32); s->copyright[32] = 0;

	if (hdr < 0x76 || hdr > size)
		die("%s: bad data offset", path);
	s->data = s->file + hdr;
	s->len  = size - hdr;
	if (s->load == 0) {
		if (s->len < 2)
			die("%s: no load address", path);
		s->load = s->data[0] | s->data[1] << 8;
		s->data += 2;
		s->len  -= 2;
	}
	if ((size_t)s->load + s->len > 0x10000)
		die("%s: data does not fit in 64 KB (load $%04X, %zu bytes)",
		    path, s->load, s->len);
	if (s->songs < 1)
		s->songs = 1;
	if (s->start < 1 || s->start > s->songs)
		s->start = 1;
}

/* ----------------------------- machine ----------------------------- */

typedef struct {
	uint8_t  mem[65536];
	uint8_t  sid[0x20];		/* last value written to each SID register */
	int      gate_on[3];		/* gate 0->1 transitions during this call  */
	int      cia_set;		/* tune programmed CIA1 timer A latch      */
	uint16_t cia_latch;
	uint8_t  raster;
	uint32_t lfsr;
} machine_t;

static uint8_t bus_read(void *ctx, uint16_t addr)
{
	machine_t *m = ctx;

	if (addr >= 0xD400 && addr < 0xD800) {
		switch (addr & 0x1F) {
		case 0x1B:			/* OSC3: pseudo random */
			m->lfsr = m->lfsr * 1664525u + 1013904223u;
			return (uint8_t)(m->lfsr >> 24);
		case 0x1C:			/* ENV3 */
			return 0;
		}
		return 0;
	}
	if (addr == 0xD012)			/* VIC raster: always moving */
		return m->raster += 7;
	if (addr == 0xD011)
		return 0;
	return m->mem[addr];
}

static void bus_write(void *ctx, uint16_t addr, uint8_t val)
{
	machine_t *m = ctx;

	if (addr >= 0xD400 && addr < 0xD800) {
		unsigned r = addr & 0x1F;
		if (r <= 0x18) {
			if (r == 4 || r == 11 || r == 18) {
				int v = (int)(r / 7);
				if (!(m->sid[r] & 1) && (val & 1))
					m->gate_on[v]++;
			}
			m->sid[r] = val;
		}
		return;
	}
	if (addr == 0xDC04) {
		m->cia_latch = (uint16_t)((m->cia_latch & 0xFF00) | val);
		m->cia_set = 1;
	} else if (addr == 0xDC05) {
		m->cia_latch = (uint16_t)((m->cia_latch & 0x00FF) | val << 8);
		m->cia_set = 1;
	}
	m->mem[addr] = val;
}

/* Run a subroutine until it returns to TRAP_ADDR. */
static int call_sub(machine_t *m, cpu6502_t *cpu, uint16_t addr, uint8_t a,
		    long max_steps)
{
	long n;

	cpu_reset_state(cpu);
	cpu->a = a;
	cpu_push(cpu, (TRAP_ADDR - 1) >> 8);
	cpu_push(cpu, (TRAP_ADDR - 1) & 0xFF);
	cpu->pc = addr;

	for (n = 0; n < max_steps; n++) {
		if (cpu->pc == TRAP_ADDR)
			return 0;
		if (cpu_step(cpu) < 0) {
			fprintf(stderr,
				"sidconv: unsupported opcode $%02X at $%04X\n",
				cpu->bad_op, cpu->bad_pc);
			return -1;
		}
	}
	(void)m;
	fprintf(stderr, "sidconv: routine at $%04X did not return "
		"(%ld instructions)\n", addr, max_steps);
	return -1;
}

/* --------------------------- voice model --------------------------- */

enum { ENV_IDLE, ENV_ATTACK, ENV_DECAY, ENV_SUSTAIN, ENV_RELEASE };

static const double attack_ms[16] = {
	2, 8, 16, 24, 38, 56, 68, 80, 100, 250, 500, 800, 1000, 3000, 5000, 8000
};
/* decay and release take three times longer than attack */
#define DECAY_MS(i) (attack_ms[i] * 3.0)

typedef struct {
	int    state;
	double level;		/* 0..255 */
} voice_t;

/* Advance the envelope of one voice by one play call (dt milliseconds). */
static void voice_step(voice_t *vm, const uint8_t *r, int gate_events,
		       double dt)
{
	int gate = r[4] & 1;
	int a = r[5] >> 4, d = r[5] & 15, s = r[6] >> 4, rel = r[6] & 15;
	double target = s * 17.0;

	if (gate_events)
		vm->state = ENV_ATTACK;
	else if (!gate && vm->state != ENV_IDLE)
		vm->state = ENV_RELEASE;
	if (!gate && gate_events && vm->state == ENV_ATTACK)
		vm->state = ENV_RELEASE;	/* gated on and off in one frame */

	switch (vm->state) {
	case ENV_ATTACK:
		vm->level += 255.0 * dt / attack_ms[a];
		if (vm->level >= 255.0) {
			vm->level = 255.0;
			vm->state = ENV_DECAY;
		}
		break;
	case ENV_DECAY:
		vm->level -= 255.0 * dt / DECAY_MS(d);
		if (vm->level <= target) {
			vm->level = target;
			vm->state = ENV_SUSTAIN;
		}
		break;
	case ENV_SUSTAIN:
		vm->level = target;
		break;
	case ENV_RELEASE:
		vm->level -= 255.0 * dt / DECAY_MS(rel);
		if (vm->level <= 0.0) {
			vm->level = 0.0;
			vm->state = ENV_IDLE;
		}
		break;
	default:
		break;
	}
}

/* --------------------------- POKEY mapping -------------------------- */

typedef struct {
	double sid_clk;		/* SID clock, Hz */
	double clk64;		/* POKEY 64 kHz base clock, Hz */
	uint8_t audctl;
	int    last_f[4];	/* last AUDF / distortion used per channel, kept */
	int    last_dist[4];	/* while a channel is silent to save stream bytes */
} map_t;

/* One SID snapshot (the voice model must already be stepped) -> 8 regs. */
static void map_frame(map_t *mp, const uint8_t *sid, const voice_t *vm,
		      uint8_t out[8])
{
	int mastervol = sid[0x18] & 15;
	int v;

	memset(out, 0, 8);
	for (v = 0; v < 3; v++) {
		const uint8_t *r = sid + 7 * v;
		int ctrl = r[4];
		int wave = ctrl >> 4;
		int fn = r[0] | r[1] << 8;
		int vol = (int)((vm[v].level * mastervol + 127.0) / 255.0);
		int f, dist;

		if (vol > 15)
			vol = 15;
		if ((ctrl & 8) || wave == 0 || fn == 0)	/* test bit, no wave */
			vol = 0;

		if (vol == 0) {
			f = mp->last_f[v];
			dist = mp->last_dist[v];
		} else {
			double hz = fn * mp->sid_clk / 16777216.0;
			double div = mp->clk64 / (2.0 * hz);	/* = N + 1 */

			while (div > 256.0)
				div /= 2.0;			/* fold octaves up */
			f = (int)floor(div + 0.5) - 1;
			if (f < 0)
				f = 0;
			if (f > 255)
				f = 255;
			dist = (wave & 8) ? 0x80 : 0xA0;
			mp->last_f[v] = f;
			mp->last_dist[v] = dist;
		}
		out[2 * v]     = (uint8_t)f;
		out[2 * v + 1] = (uint8_t)(dist | vol);
	}
	/* channel 4 stays silent */
}

/* ------------------------------ stream ----------------------------- */

static size_t stream_encode(const uint8_t (*fr)[8], int n, uint8_t audctl,
			    int video_hz, uint8_t *out)
{
	int last[8], i, r;
	size_t pos = 0;

	out[pos++] = audctl;
	out[pos++] = (uint8_t)video_hz;
	out[pos++] = (uint8_t)(n & 0xFF);
	out[pos++] = (uint8_t)(n >> 8);
	for (r = 0; r < 8; r++)
		last[r] = -1;
	for (i = 0; i < n; i++) {
		size_t mpos = pos++;
		uint8_t mask = 0;

		for (r = 0; r < 8; r++) {
			if (fr[i][r] != last[r]) {
				mask |= (uint8_t)(1 << r);
				out[pos++] = fr[i][r];
				last[r] = fr[i][r];
			}
		}
		out[mpos] = mask;
	}
	return pos;
}

/* Decode the stream exactly like the 6502 player does and compare. */
static int stream_verify(const uint8_t *s, size_t len, const uint8_t (*fr)[8],
			 int n)
{
	uint8_t reg[8] = { 0 };
	size_t pos = 4;
	int i, r;

	for (i = 0; i < n; i++) {
		uint8_t mask;
		if (pos >= len)
			return -1;
		mask = s[pos++];
		for (r = 0; mask; r++, mask >>= 1)
			if (mask & 1) {
				if (pos >= len)
					return -1;
				reg[r] = s[pos++];
			}
		if (memcmp(reg, fr[i], 8))
			return -1;
	}
	return pos == len ? 0 : -1;
}

/* ------------------------------- main ------------------------------ */

static void usage(void)
{
	fprintf(stderr,
"usage: sidconv [options] input.sid\n"
"  -o file     output stream (default: song.bin)\n"
"  -s n        song number, 1-based (default: the file's start song)\n"
"  -t seconds  duration to convert (default 60)\n"
"  -p pal|ntsc Atari video standard of the target (default pal)\n"
"  -c pal|ntsc|auto  clock the SID tune was written for (default auto)\n"
"  -d          dump the POKEY registers of every frame\n"
"  -v          verbose\n");
	exit(2);
}

int main(int argc, char **argv)
{
	const char *in = NULL, *outname = "song.bin";
	int song = 0, verbose = 0, dump = 0, ntsc_target = 0;
	int sid_clock = 0;		/* 0 auto, 1 pal, 2 ntsc */
	double seconds = 60.0;
	psid_t psid;
	machine_t *m;
	cpu6502_t cpu;
	map_t mp;
	voice_t vm[3];
	uint8_t (*pk)[8], (*fr)[8];
	uint8_t *stream;
	double play_hz, atari_hz, call_ms;
	int ncalls, nframes, video_hz, speed_cia, i, v, r;
	size_t outlen;
	FILE *f;

	for (i = 1; i < argc; i++) {
		const char *a = argv[i];
		if (!strcmp(a, "-o") && i + 1 < argc) outname = argv[++i];
		else if (!strcmp(a, "-s") && i + 1 < argc) song = atoi(argv[++i]);
		else if (!strcmp(a, "-t") && i + 1 < argc) seconds = atof(argv[++i]);
		else if (!strcmp(a, "-p") && i + 1 < argc) {
			a = argv[++i];
			if (!strcmp(a, "pal")) ntsc_target = 0;
			else if (!strcmp(a, "ntsc")) ntsc_target = 1;
			else usage();
		} else if (!strcmp(a, "-c") && i + 1 < argc) {
			a = argv[++i];
			if (!strcmp(a, "auto")) sid_clock = 0;
			else if (!strcmp(a, "pal")) sid_clock = 1;
			else if (!strcmp(a, "ntsc")) sid_clock = 2;
			else usage();
		} else if (!strcmp(a, "-d")) dump = 1;
		else if (!strcmp(a, "-v")) verbose = 1;
		else if (a[0] == '-') usage();
		else if (!in) in = a;
		else usage();
	}
	if (!in || seconds <= 0)
		usage();

	psid_load(&psid, in);
	if (!strcmp(psid.magic, "RSID"))
		fprintf(stderr, "sidconv: warning: RSID files expect a real C64 "
			"environment; trying anyway\n");
	if (psid.play == 0)
		die("play address is 0: the tune installs its own IRQ handler "
		    "(not supported yet)");
	if (song == 0)
		song = psid.start;
	if (song < 1 || song > psid.songs)
		die("song %d out of range (1..%d)", song, psid.songs);

	if (sid_clock == 0) {
		int c = (psid.flags >> 2) & 3;
		sid_clock = (c == 2) ? 2 : 1;	/* NTSC only if explicitly so */
	}

	/* ---- load and init ---- */
	m = calloc(1, sizeof *m);
	if (!m)
		die("out of memory");
	m->lfsr = 0x1234567;
	memcpy(m->mem + psid.load, psid.data, psid.len);
	cpu.read = bus_read;
	cpu.write = bus_write;
	cpu.ctx = m;

	if (call_sub(m, &cpu, (uint16_t)psid.init, (uint8_t)(song - 1), INIT_STEPS))
		die("init routine failed");

	/* ---- timing ---- */
	{
		/* speed bit of this song: 0 = VBI, 1 = CIA timer.  Songs above
		 * 32 reuse bit 31 per the PSID specification. */
		int bit = (song - 1) < 32 ? (song - 1) : 31;
		double sidclk = sid_clock == 2 ? NTSC_SID_CLK : PAL_SID_CLK;
		speed_cia = (psid.speed >> bit) & 1;
		if (speed_cia) {
			play_hz = m->cia_set && m->cia_latch
				  ? sidclk / (m->cia_latch + 1.0)
				  : 60.0;
		} else {
			play_hz = sid_clock == 2 ? NTSC_VBI_HZ : PAL_VBI_HZ;
		}
		mp.sid_clk = sidclk;
	}
	atari_hz = ntsc_target ? NTSC_ATARI_HZ : PAL_ATARI_HZ;
	video_hz = ntsc_target ? 60 : 50;
	mp.clk64 = (ntsc_target ? NTSC_CPU_CLK : PAL_CPU_CLK) / 28.0;
	mp.audctl = 0;
	for (i = 0; i < 4; i++) {
		mp.last_f[i] = 0;
		mp.last_dist[i] = 0xA0;
	}

	nframes = (int)(seconds * atari_hz);
	if (nframes > MAX_FRAMES)
		die("duration too long: %d frames (max %d)", nframes, MAX_FRAMES);
	ncalls = (int)ceil(nframes / atari_hz * play_hz) + 2;
	call_ms = 1000.0 / play_hz;

	if (verbose) {
		fprintf(stderr, "title     : %s\nauthor    : %s\ncopyright : %s\n",
			psid.title, psid.author, psid.copyright);
		fprintf(stderr, "%s v%d  load $%04X  %zu bytes  init $%04X  play $%04X\n",
			psid.magic, psid.version, psid.load, psid.len,
			psid.init, psid.play);
		fprintf(stderr, "song %d/%d  %s  SID %s  play rate %.3f Hz  "
			"-> Atari %s %.3f Hz\n", song, psid.songs,
			speed_cia ? "CIA timer" : "VBI",
			sid_clock == 2 ? "NTSC" : "PAL", play_hz,
			ntsc_target ? "NTSC" : "PAL", atari_hz);
		if (play_hz > atari_hz * 1.5)
			fprintf(stderr, "note: multispeed tune (%.1fx), "
				"decimated to one play call per frame\n",
				play_hz / atari_hz);
	}

	/* ---- run the tune, one play call at a time ---- */
	pk = calloc((size_t)ncalls, 8);
	fr = calloc((size_t)nframes, 8);
	stream = malloc((size_t)nframes * 9 + 4);
	if (!pk || !fr || !stream)
		die("out of memory");
	memset(vm, 0, sizeof vm);

	for (i = 0; i < ncalls; i++) {
		memset(m->gate_on, 0, sizeof m->gate_on);
		if (call_sub(m, &cpu, (uint16_t)psid.play, 0, PLAY_STEPS))
			die("play routine failed at call %d", i);
		for (v = 0; v < 3; v++)
			voice_step(&vm[v], m->sid + 7 * v, m->gate_on[v], call_ms);
		map_frame(&mp, m->sid, vm, pk[i]);
	}

	/* ---- resample play calls to Atari video frames ---- */
	for (i = 0; i < nframes; i++) {
		int c = (int)floor(i / atari_hz * play_hz);
		if (c >= ncalls)
			c = ncalls - 1;
		memcpy(fr[i], pk[c], 8);
	}

	if (dump) {
		for (i = 0; i < nframes; i++) {
			printf("%5d:", i);
			for (r = 0; r < 8; r++)
				printf(" %02X", fr[i][r]);
			printf("\n");
		}
	}

	outlen = stream_encode((const uint8_t (*)[8])fr, nframes, mp.audctl,
			       video_hz, stream);
	if (stream_verify(stream, outlen, (const uint8_t (*)[8])fr, nframes))
		die("internal error: stream verification failed");

	f = fopen(outname, "wb");
	if (!f || fwrite(stream, 1, outlen, f) != outlen || fclose(f))
		die("cannot write %s", outname);

	fprintf(stderr, "%s: %d frames (%.1f s), %zu bytes (%.1f bytes/frame)\n",
		outname, nframes, nframes / atari_hz, outlen,
		(double)outlen / nframes);
	if (outlen > 40000)
		fprintf(stderr, "warning: stream larger than 40 KB, it may not "
			"fit in a 48 KB Atari\n");
	return 0;
}
