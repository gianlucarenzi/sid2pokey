/*
 * cpu6502.h - minimal NMOS 6502 core used by sidconv to run SID tunes.
 *
 * Header-only, no timing: it only needs to execute INIT/PLAY routines of
 * a PSID file and let the caller observe the writes to the SID registers.
 *
 * Supported: all official opcodes (binary + decimal mode ADC/SBC) and the
 * common undocumented ones used by SID players (LAX, SAX, SLO, RLA, SRE,
 * RRA, DCP, ISC, ANC, ALR, SBX, multi-byte NOPs).
 * Not supported (cpu_step() returns -1 and sets cpu->bad_op): JAM opcodes
 * and the "unstable" undocumented ones (XAA, LXA, AHX, TAS, SHX, SHY, LAS,
 * ARR).
 */
#ifndef CPU6502_H
#define CPU6502_H

#include <stdint.h>

typedef struct cpu6502 {
	uint8_t  a, x, y, sp;
	uint8_t  c, z, i, d, v, n;	/* flags, each 0 or 1 */
	uint16_t pc;
	uint8_t  bad_op;		/* opcode that made cpu_step() fail */
	uint16_t bad_pc;		/* ... and where it was */
	uint8_t  (*read)(void *ctx, uint16_t addr);
	void     (*write)(void *ctx, uint16_t addr, uint8_t val);
	void     *ctx;
} cpu6502_t;

enum { M_IMM, M_ZP, M_ZPX, M_ZPY, M_ABS, M_ABX, M_ABY, M_IZX, M_IZY };

#define CRD(a)    (c->read(c->ctx, (uint16_t)(a)))
#define CWR(a, v) (c->write(c->ctx, (uint16_t)(a), (uint8_t)(v)))

static uint8_t cpu_fetch(cpu6502_t *c)
{
	return CRD(c->pc++);
}

static uint16_t cpu_fetch16(cpu6502_t *c)
{
	uint16_t lo = cpu_fetch(c);
	uint16_t hi = cpu_fetch(c);
	return (uint16_t)(lo | (hi << 8));
}

static uint16_t cpu_ea(cpu6502_t *c, int mode)
{
	uint16_t lo, hi, base;
	uint8_t zp;

	switch (mode) {
	case M_IMM: return c->pc++;
	case M_ZP:  return cpu_fetch(c);
	case M_ZPX: return (uint8_t)(cpu_fetch(c) + c->x);
	case M_ZPY: return (uint8_t)(cpu_fetch(c) + c->y);
	case M_ABS: return cpu_fetch16(c);
	case M_ABX: return (uint16_t)(cpu_fetch16(c) + c->x);
	case M_ABY: return (uint16_t)(cpu_fetch16(c) + c->y);
	case M_IZX:
		zp = (uint8_t)(cpu_fetch(c) + c->x);
		lo = CRD(zp);
		hi = CRD((uint8_t)(zp + 1));
		return (uint16_t)(lo | (hi << 8));
	default: /* M_IZY */
		zp = cpu_fetch(c);
		lo = CRD(zp);
		hi = CRD((uint8_t)(zp + 1));
		base = (uint16_t)(lo | (hi << 8));
		return (uint16_t)(base + c->y);
	}
}

static void cpu_nz(cpu6502_t *c, uint8_t v)
{
	c->z = (v == 0);
	c->n = v >> 7;
}

static uint8_t cpu_getp(cpu6502_t *c, int brk)
{
	return (uint8_t)(c->n << 7 | c->v << 6 | 0x20 | (brk ? 0x10 : 0) |
			 c->d << 3 | c->i << 2 | c->z << 1 | c->c);
}

static void cpu_setp(cpu6502_t *c, uint8_t p)
{
	c->n = p >> 7;
	c->v = (p >> 6) & 1;
	c->d = (p >> 3) & 1;
	c->i = (p >> 2) & 1;
	c->z = (p >> 1) & 1;
	c->c = p & 1;
}

static void cpu_push(cpu6502_t *c, uint8_t v)
{
	CWR(0x100 + c->sp, v);
	c->sp--;
}

static uint8_t cpu_pull(cpu6502_t *c)
{
	c->sp++;
	return CRD(0x100 + c->sp);
}

static void cpu_adc(cpu6502_t *c, uint8_t m)
{
	unsigned bin = c->a + m + c->c;

	if (c->d) {
		int al = (c->a & 0x0F) + (m & 0x0F) + c->c;
		int r;
		if (al >= 0x0A)
			al = ((al + 0x06) & 0x0F) + 0x10;
		r = (c->a & 0xF0) + (m & 0xF0) + al;
		c->z = ((bin & 0xFF) == 0);
		c->n = (r >> 7) & 1;
		c->v = (((c->a ^ r) & (m ^ r) & 0x80) != 0);
		if (r >= 0xA0)
			r += 0x60;
		c->c = (r >= 0x100);
		c->a = (uint8_t)r;
	} else {
		c->v = (((c->a ^ bin) & (m ^ bin) & 0x80) != 0);
		c->c = bin > 0xFF;
		c->a = (uint8_t)bin;
		cpu_nz(c, c->a);
	}
}

static void cpu_sbc(cpu6502_t *c, uint8_t m)
{
	unsigned bin = c->a - m - (1 - c->c);

	c->v = (((c->a ^ m) & (c->a ^ bin) & 0x80) != 0);
	if (c->d) {
		int al = (c->a & 0x0F) - (m & 0x0F) + c->c - 1;
		int r;
		if (al < 0)
			al = ((al - 0x06) & 0x0F) - 0x10;
		r = (c->a & 0xF0) - (m & 0xF0) + al;
		if (r < 0)
			r -= 0x60;
		c->c = !(bin > 0xFF);
		c->a = (uint8_t)r;
		cpu_nz(c, (uint8_t)bin);
	} else {
		c->c = !(bin > 0xFF);
		c->a = (uint8_t)bin;
		cpu_nz(c, c->a);
	}
}

static void cpu_cmp(cpu6502_t *c, uint8_t r, uint8_t m)
{
	c->c = (r >= m);
	cpu_nz(c, (uint8_t)(r - m));
}

static uint8_t cpu_asl(cpu6502_t *c, uint8_t v)
{
	c->c = v >> 7;
	v <<= 1;
	cpu_nz(c, v);
	return v;
}

static uint8_t cpu_lsr(cpu6502_t *c, uint8_t v)
{
	c->c = v & 1;
	v >>= 1;
	cpu_nz(c, v);
	return v;
}

static uint8_t cpu_rol(cpu6502_t *c, uint8_t v)
{
	uint8_t cin = c->c;
	c->c = v >> 7;
	v = (uint8_t)((v << 1) | cin);
	cpu_nz(c, v);
	return v;
}

static uint8_t cpu_ror(cpu6502_t *c, uint8_t v)
{
	uint8_t cin = c->c;
	c->c = v & 1;
	v = (uint8_t)((v >> 1) | (cin << 7));
	cpu_nz(c, v);
	return v;
}

static uint8_t cpu_inc(cpu6502_t *c, uint8_t v)
{
	v++;
	cpu_nz(c, v);
	return v;
}

static uint8_t cpu_dec(cpu6502_t *c, uint8_t v)
{
	v--;
	cpu_nz(c, v);
	return v;
}

typedef uint8_t (*cpu_rmw_fn)(cpu6502_t *, uint8_t);

static void cpu_rmw(cpu6502_t *c, int mode, cpu_rmw_fn f)
{
	uint16_t ad = cpu_ea(c, mode);
	CWR(ad, f(c, CRD(ad)));
}

static void cpu_branch(cpu6502_t *c, int cond)
{
	int8_t off = (int8_t)cpu_fetch(c);
	if (cond)
		c->pc = (uint16_t)(c->pc + off);
}

static void cpu_reset_state(cpu6502_t *c)
{
	c->a = c->x = c->y = 0;
	c->sp = 0xFF;
	c->c = c->z = c->i = c->d = c->v = c->n = 0;
}

/* Execute one instruction. Returns 0, or -1 on an unsupported opcode. */
static int cpu_step(cpu6502_t *c)
{
	uint16_t op_pc = c->pc;
	uint8_t op = cpu_fetch(c);
	uint16_t ad, t;
	uint8_t m;

	switch (op) {
	/* --- ADC --- */
	case 0x69: cpu_adc(c, CRD(cpu_ea(c, M_IMM))); break;
	case 0x65: cpu_adc(c, CRD(cpu_ea(c, M_ZP)));  break;
	case 0x75: cpu_adc(c, CRD(cpu_ea(c, M_ZPX))); break;
	case 0x6D: cpu_adc(c, CRD(cpu_ea(c, M_ABS))); break;
	case 0x7D: cpu_adc(c, CRD(cpu_ea(c, M_ABX))); break;
	case 0x79: cpu_adc(c, CRD(cpu_ea(c, M_ABY))); break;
	case 0x61: cpu_adc(c, CRD(cpu_ea(c, M_IZX))); break;
	case 0x71: cpu_adc(c, CRD(cpu_ea(c, M_IZY))); break;
	/* --- AND --- */
	case 0x29: c->a &= CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->a); break;
	case 0x25: c->a &= CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->a); break;
	case 0x35: c->a &= CRD(cpu_ea(c, M_ZPX)); cpu_nz(c, c->a); break;
	case 0x2D: c->a &= CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->a); break;
	case 0x3D: c->a &= CRD(cpu_ea(c, M_ABX)); cpu_nz(c, c->a); break;
	case 0x39: c->a &= CRD(cpu_ea(c, M_ABY)); cpu_nz(c, c->a); break;
	case 0x21: c->a &= CRD(cpu_ea(c, M_IZX)); cpu_nz(c, c->a); break;
	case 0x31: c->a &= CRD(cpu_ea(c, M_IZY)); cpu_nz(c, c->a); break;
	/* --- ASL --- */
	case 0x0A: c->a = cpu_asl(c, c->a); break;
	case 0x06: cpu_rmw(c, M_ZP,  cpu_asl); break;
	case 0x16: cpu_rmw(c, M_ZPX, cpu_asl); break;
	case 0x0E: cpu_rmw(c, M_ABS, cpu_asl); break;
	case 0x1E: cpu_rmw(c, M_ABX, cpu_asl); break;
	/* --- branches --- */
	case 0x90: cpu_branch(c, !c->c); break;
	case 0xB0: cpu_branch(c,  c->c); break;
	case 0xF0: cpu_branch(c,  c->z); break;
	case 0xD0: cpu_branch(c, !c->z); break;
	case 0x30: cpu_branch(c,  c->n); break;
	case 0x10: cpu_branch(c, !c->n); break;
	case 0x50: cpu_branch(c, !c->v); break;
	case 0x70: cpu_branch(c,  c->v); break;
	/* --- BIT --- */
	case 0x24:
	case 0x2C:
		m = CRD(cpu_ea(c, op == 0x24 ? M_ZP : M_ABS));
		c->z = ((c->a & m) == 0);
		c->n = m >> 7;
		c->v = (m >> 6) & 1;
		break;
	/* --- BRK --- */
	case 0x00:
		c->pc++;
		cpu_push(c, c->pc >> 8);
		cpu_push(c, c->pc & 0xFF);
		cpu_push(c, cpu_getp(c, 1));
		c->i = 1;
		c->pc = (uint16_t)(CRD(0xFFFE) | (CRD(0xFFFF) << 8));
		break;
	/* --- flags --- */
	case 0x18: c->c = 0; break;
	case 0xD8: c->d = 0; break;
	case 0x58: c->i = 0; break;
	case 0xB8: c->v = 0; break;
	case 0x38: c->c = 1; break;
	case 0xF8: c->d = 1; break;
	case 0x78: c->i = 1; break;
	/* --- CMP / CPX / CPY --- */
	case 0xC9: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_IMM))); break;
	case 0xC5: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_ZP)));  break;
	case 0xD5: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_ZPX))); break;
	case 0xCD: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_ABS))); break;
	case 0xDD: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_ABX))); break;
	case 0xD9: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_ABY))); break;
	case 0xC1: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_IZX))); break;
	case 0xD1: cpu_cmp(c, c->a, CRD(cpu_ea(c, M_IZY))); break;
	case 0xE0: cpu_cmp(c, c->x, CRD(cpu_ea(c, M_IMM))); break;
	case 0xE4: cpu_cmp(c, c->x, CRD(cpu_ea(c, M_ZP)));  break;
	case 0xEC: cpu_cmp(c, c->x, CRD(cpu_ea(c, M_ABS))); break;
	case 0xC0: cpu_cmp(c, c->y, CRD(cpu_ea(c, M_IMM))); break;
	case 0xC4: cpu_cmp(c, c->y, CRD(cpu_ea(c, M_ZP)));  break;
	case 0xCC: cpu_cmp(c, c->y, CRD(cpu_ea(c, M_ABS))); break;
	/* --- DEC / INC --- */
	case 0xC6: cpu_rmw(c, M_ZP,  cpu_dec); break;
	case 0xD6: cpu_rmw(c, M_ZPX, cpu_dec); break;
	case 0xCE: cpu_rmw(c, M_ABS, cpu_dec); break;
	case 0xDE: cpu_rmw(c, M_ABX, cpu_dec); break;
	case 0xE6: cpu_rmw(c, M_ZP,  cpu_inc); break;
	case 0xF6: cpu_rmw(c, M_ZPX, cpu_inc); break;
	case 0xEE: cpu_rmw(c, M_ABS, cpu_inc); break;
	case 0xFE: cpu_rmw(c, M_ABX, cpu_inc); break;
	case 0xCA: c->x--; cpu_nz(c, c->x); break;
	case 0x88: c->y--; cpu_nz(c, c->y); break;
	case 0xE8: c->x++; cpu_nz(c, c->x); break;
	case 0xC8: c->y++; cpu_nz(c, c->y); break;
	/* --- EOR --- */
	case 0x49: c->a ^= CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->a); break;
	case 0x45: c->a ^= CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->a); break;
	case 0x55: c->a ^= CRD(cpu_ea(c, M_ZPX)); cpu_nz(c, c->a); break;
	case 0x4D: c->a ^= CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->a); break;
	case 0x5D: c->a ^= CRD(cpu_ea(c, M_ABX)); cpu_nz(c, c->a); break;
	case 0x59: c->a ^= CRD(cpu_ea(c, M_ABY)); cpu_nz(c, c->a); break;
	case 0x41: c->a ^= CRD(cpu_ea(c, M_IZX)); cpu_nz(c, c->a); break;
	case 0x51: c->a ^= CRD(cpu_ea(c, M_IZY)); cpu_nz(c, c->a); break;
	/* --- JMP / JSR / RTS / RTI --- */
	case 0x4C: c->pc = cpu_fetch16(c); break;
	case 0x6C:
		ad = cpu_fetch16(c);
		/* NMOS bug: the high byte is fetched without page carry */
		t = (uint16_t)((ad & 0xFF00) | ((ad + 1) & 0x00FF));
		c->pc = (uint16_t)(CRD(ad) | (CRD(t) << 8));
		break;
	case 0x20:
		ad = cpu_fetch16(c);
		c->pc--;
		cpu_push(c, c->pc >> 8);
		cpu_push(c, c->pc & 0xFF);
		c->pc = ad;
		break;
	case 0x60:
		t = cpu_pull(c);
		t |= (uint16_t)(cpu_pull(c) << 8);
		c->pc = (uint16_t)(t + 1);
		break;
	case 0x40:
		cpu_setp(c, cpu_pull(c));
		t = cpu_pull(c);
		t |= (uint16_t)(cpu_pull(c) << 8);
		c->pc = t;
		break;
	/* --- LDA / LDX / LDY --- */
	case 0xA9: c->a = CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->a); break;
	case 0xA5: c->a = CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->a); break;
	case 0xB5: c->a = CRD(cpu_ea(c, M_ZPX)); cpu_nz(c, c->a); break;
	case 0xAD: c->a = CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->a); break;
	case 0xBD: c->a = CRD(cpu_ea(c, M_ABX)); cpu_nz(c, c->a); break;
	case 0xB9: c->a = CRD(cpu_ea(c, M_ABY)); cpu_nz(c, c->a); break;
	case 0xA1: c->a = CRD(cpu_ea(c, M_IZX)); cpu_nz(c, c->a); break;
	case 0xB1: c->a = CRD(cpu_ea(c, M_IZY)); cpu_nz(c, c->a); break;
	case 0xA2: c->x = CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->x); break;
	case 0xA6: c->x = CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->x); break;
	case 0xB6: c->x = CRD(cpu_ea(c, M_ZPY)); cpu_nz(c, c->x); break;
	case 0xAE: c->x = CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->x); break;
	case 0xBE: c->x = CRD(cpu_ea(c, M_ABY)); cpu_nz(c, c->x); break;
	case 0xA0: c->y = CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->y); break;
	case 0xA4: c->y = CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->y); break;
	case 0xB4: c->y = CRD(cpu_ea(c, M_ZPX)); cpu_nz(c, c->y); break;
	case 0xAC: c->y = CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->y); break;
	case 0xBC: c->y = CRD(cpu_ea(c, M_ABX)); cpu_nz(c, c->y); break;
	/* --- LSR --- */
	case 0x4A: c->a = cpu_lsr(c, c->a); break;
	case 0x46: cpu_rmw(c, M_ZP,  cpu_lsr); break;
	case 0x56: cpu_rmw(c, M_ZPX, cpu_lsr); break;
	case 0x4E: cpu_rmw(c, M_ABS, cpu_lsr); break;
	case 0x5E: cpu_rmw(c, M_ABX, cpu_lsr); break;
	/* --- NOP --- */
	case 0xEA:
	case 0x1A: case 0x3A: case 0x5A: case 0x7A: case 0xDA: case 0xFA:
		break;
	case 0x80: case 0x82: case 0x89: case 0xC2: case 0xE2:
		cpu_ea(c, M_IMM); break;
	case 0x04: case 0x44: case 0x64:
		cpu_ea(c, M_ZP); break;
	case 0x14: case 0x34: case 0x54: case 0x74: case 0xD4: case 0xF4:
		cpu_ea(c, M_ZPX); break;
	case 0x0C:
		cpu_ea(c, M_ABS); break;
	case 0x1C: case 0x3C: case 0x5C: case 0x7C: case 0xDC: case 0xFC:
		cpu_ea(c, M_ABX); break;
	/* --- ORA --- */
	case 0x09: c->a |= CRD(cpu_ea(c, M_IMM)); cpu_nz(c, c->a); break;
	case 0x05: c->a |= CRD(cpu_ea(c, M_ZP));  cpu_nz(c, c->a); break;
	case 0x15: c->a |= CRD(cpu_ea(c, M_ZPX)); cpu_nz(c, c->a); break;
	case 0x0D: c->a |= CRD(cpu_ea(c, M_ABS)); cpu_nz(c, c->a); break;
	case 0x1D: c->a |= CRD(cpu_ea(c, M_ABX)); cpu_nz(c, c->a); break;
	case 0x19: c->a |= CRD(cpu_ea(c, M_ABY)); cpu_nz(c, c->a); break;
	case 0x01: c->a |= CRD(cpu_ea(c, M_IZX)); cpu_nz(c, c->a); break;
	case 0x11: c->a |= CRD(cpu_ea(c, M_IZY)); cpu_nz(c, c->a); break;
	/* --- stack --- */
	case 0x48: cpu_push(c, c->a); break;
	case 0x08: cpu_push(c, cpu_getp(c, 1)); break;
	case 0x68: c->a = cpu_pull(c); cpu_nz(c, c->a); break;
	case 0x28: cpu_setp(c, cpu_pull(c)); break;
	/* --- ROL / ROR --- */
	case 0x2A: c->a = cpu_rol(c, c->a); break;
	case 0x26: cpu_rmw(c, M_ZP,  cpu_rol); break;
	case 0x36: cpu_rmw(c, M_ZPX, cpu_rol); break;
	case 0x2E: cpu_rmw(c, M_ABS, cpu_rol); break;
	case 0x3E: cpu_rmw(c, M_ABX, cpu_rol); break;
	case 0x6A: c->a = cpu_ror(c, c->a); break;
	case 0x66: cpu_rmw(c, M_ZP,  cpu_ror); break;
	case 0x76: cpu_rmw(c, M_ZPX, cpu_ror); break;
	case 0x6E: cpu_rmw(c, M_ABS, cpu_ror); break;
	case 0x7E: cpu_rmw(c, M_ABX, cpu_ror); break;
	/* --- SBC (0xEB is the undocumented duplicate of 0xE9) --- */
	case 0xE9: case 0xEB: cpu_sbc(c, CRD(cpu_ea(c, M_IMM))); break;
	case 0xE5: cpu_sbc(c, CRD(cpu_ea(c, M_ZP)));  break;
	case 0xF5: cpu_sbc(c, CRD(cpu_ea(c, M_ZPX))); break;
	case 0xED: cpu_sbc(c, CRD(cpu_ea(c, M_ABS))); break;
	case 0xFD: cpu_sbc(c, CRD(cpu_ea(c, M_ABX))); break;
	case 0xF9: cpu_sbc(c, CRD(cpu_ea(c, M_ABY))); break;
	case 0xE1: cpu_sbc(c, CRD(cpu_ea(c, M_IZX))); break;
	case 0xF1: cpu_sbc(c, CRD(cpu_ea(c, M_IZY))); break;
	/* --- STA / STX / STY --- */
	case 0x85: CWR(cpu_ea(c, M_ZP),  c->a); break;
	case 0x95: CWR(cpu_ea(c, M_ZPX), c->a); break;
	case 0x8D: CWR(cpu_ea(c, M_ABS), c->a); break;
	case 0x9D: CWR(cpu_ea(c, M_ABX), c->a); break;
	case 0x99: CWR(cpu_ea(c, M_ABY), c->a); break;
	case 0x81: CWR(cpu_ea(c, M_IZX), c->a); break;
	case 0x91: CWR(cpu_ea(c, M_IZY), c->a); break;
	case 0x86: CWR(cpu_ea(c, M_ZP),  c->x); break;
	case 0x96: CWR(cpu_ea(c, M_ZPY), c->x); break;
	case 0x8E: CWR(cpu_ea(c, M_ABS), c->x); break;
	case 0x84: CWR(cpu_ea(c, M_ZP),  c->y); break;
	case 0x94: CWR(cpu_ea(c, M_ZPX), c->y); break;
	case 0x8C: CWR(cpu_ea(c, M_ABS), c->y); break;
	/* --- transfers --- */
	case 0xAA: c->x = c->a; cpu_nz(c, c->x); break;
	case 0xA8: c->y = c->a; cpu_nz(c, c->y); break;
	case 0xBA: c->x = c->sp; cpu_nz(c, c->x); break;
	case 0x8A: c->a = c->x; cpu_nz(c, c->a); break;
	case 0x9A: c->sp = c->x; break;
	case 0x98: c->a = c->y; cpu_nz(c, c->a); break;
	/* --- undocumented immediates --- */
	case 0x0B: case 0x2B:		/* ANC */
		c->a &= CRD(cpu_ea(c, M_IMM));
		cpu_nz(c, c->a);
		c->c = c->n;
		break;
	case 0x4B:			/* ALR */
		c->a &= CRD(cpu_ea(c, M_IMM));
		c->a = cpu_lsr(c, c->a);
		break;
	case 0xCB:			/* SBX */
		m = CRD(cpu_ea(c, M_IMM));
		t = (uint16_t)((c->a & c->x) - m);
		c->c = ((c->a & c->x) >= m);
		c->x = (uint8_t)t;
		cpu_nz(c, c->x);
		break;
	default:
		if ((op & 3) == 3) {
			/* undocumented "cc=11" group: LAX, SAX and RMW+ALU combos */
			static const signed char modes[8] = {
				M_IZX, M_ZP, -1, M_ABS, M_IZY, M_ZPX, M_ABY, M_ABX
			};
			int g = op >> 5;
			int b = (op >> 2) & 7;
			int mode = modes[b];

			if ((g == 4 || g == 5) && b == 5) mode = M_ZPY;
			if (g == 5 && b == 7) mode = M_ABY;
			if (g == 4 && (b == 4 || b == 6 || b == 7)) mode = -1;
			if (g == 5 && b == 6) mode = -1;
			if (mode < 0)
				goto bad;

			if (g == 4) {			/* SAX */
				CWR(cpu_ea(c, mode), c->a & c->x);
			} else if (g == 5) {		/* LAX */
				c->a = c->x = CRD(cpu_ea(c, mode));
				cpu_nz(c, c->a);
			} else {
				ad = cpu_ea(c, mode);
				m = CRD(ad);
				switch (g) {
				case 0: m = cpu_asl(c, m); c->a |= m; cpu_nz(c, c->a); break; /* SLO */
				case 1: m = cpu_rol(c, m); c->a &= m; cpu_nz(c, c->a); break; /* RLA */
				case 2: m = cpu_lsr(c, m); c->a ^= m; cpu_nz(c, c->a); break; /* SRE */
				case 3: m = cpu_ror(c, m); cpu_adc(c, m); break;              /* RRA */
				case 6: m = cpu_dec(c, m); cpu_cmp(c, c->a, m); break;        /* DCP */
				default: m = cpu_inc(c, m); cpu_sbc(c, m); break;             /* ISC */
				}
				CWR(ad, m);
			}
			break;
		}
	bad:
		c->bad_op = op;
		c->bad_pc = op_pc;
		return -1;
	}
	return 0;
}

#endif /* CPU6502_H */
