# Generates opc.s (ca65) and cases.txt for the opcode test (see run.sh).
#
# opc.s is a C64 program with many cases of the undocumented "unstable" 6502
# opcodes (ARR, XAA, LXA, AHX, TAS, SHX, SHY, LAS): for every case it sets the
# registers and flags, executes the opcode and records A, X, Y, P, SP and the
# first byte that was written in $C400-$C7FF (address and value).  cases.txt
# describes the cases, one per line.  The cases are random but seeded.
import itertools, random
random.seed(7)
RES = 0x8000
cases = []
HI = [0xFF, 0xC7, 0xC4, 0xC5, 0xF7, 0xCF, 0xE5, 0xD6]   # bits 7 and 6 set: stores stay inside $C0xx-$C7xx

# ARR #imm (binary and decimal, both carry values)
for a, imm, c, d in itertools.product([0x00, 0x55, 0xAA, 0xFF, 0x3C, 0xC3, 0x7F, 0x80], [0xFF, 0x0F, 0x55, 0x81], [0, 1], [0, 1]):
    cases.append(dict(op=0x6B, name="ARR", a=a, x=0x11, y=0x22, c=c, d=d, sp=0xF0, opnd=[imm]))
for _ in range(60):   # more decimal-mode values (BCD fix-up paths)
    cases.append(dict(op=0x6B, name="ARR", a=random.randrange(256), x=1, y=2, c=random.randrange(2), d=1, sp=0xF0, opnd=[random.randrange(256)]))
# XAA #imm
for a, x, imm in itertools.product([0x00, 0xFF, 0xAA, 0x55, 0xF0, 0x0F], [0xFF, 0x0F, 0xAA, 0x55, 0xF0], [0xFF, 0x3C, 0xA5]):
    cases.append(dict(op=0x8B, name="XAA", a=a, x=x, y=0x22, c=0, d=0, sp=0xF0, opnd=[imm]))
# LXA #imm
for a, imm, x in itertools.product([0x00, 0xFF, 0xAA, 0x55, 0xF0, 0x0F], [0xFF, 0x3C, 0xA5, 0x00, 0x81], [0x00, 0xFF]):
    cases.append(dict(op=0xAB, name="LXA", a=a, x=x, y=0x22, c=0, d=0, sp=0xF0, opnd=[imm]))

def store_cases(op, name, mode):
    n = 0
    for base_hi, base_lo, idx in itertools.product([0xC4, 0xC5, 0xC6], [0x00, 0x10, 0xF0, 0xFE, 0xFF, 0x80], [0x00, 0x05, 0x20, 0x80, 0xFF]):
        if n >= 40 or random.random() < 0.5:
            continue
        a, x, y = random.choice(HI), random.choice(HI), random.choice(HI)
        if mode in ("aby", "izy"): y = idx
        if mode == "abx": x = idx
        c = dict(op=op, name=name, a=a, x=x, y=y, c=0, d=0, sp=0xF0)
        if mode == "izy":
            c["opnd"] = [0xF0]; c["zp"] = [(0xF0, base_lo), (0xF1, base_hi)]
        else:
            c["opnd"] = [base_lo, base_hi]
        cases.append(c); n += 1

store_cases(0x93, "AHX izy", "izy")
store_cases(0x9F, "AHX aby", "aby")
store_cases(0x9B, "TAS aby", "aby")
store_cases(0x9E, "SHX aby", "aby")
store_cases(0x9C, "SHY abx", "abx")
# LAS abs,Y: reads memory (preset), result = mem & SP
for _ in range(50):
    base_hi, base_lo = random.choice([0xC4, 0xC5]), random.choice([0x00, 0x40, 0x80, 0xF0])
    y = random.choice([0x00, 0x05, 0x10])
    val = random.randrange(256); sp = random.choice([0xFF, 0xF0, 0xAA, 0x55, 0x7E, 0x1F, 0xC3])
    ea = base_hi * 256 + base_lo + y
    cases.append(dict(op=0xBB, name="LAS aby", a=random.randrange(256), x=random.randrange(256), y=y, c=0, d=0, sp=sp, opnd=[base_lo, base_hi], pre=[(ea, val)]))
assert len(cases) * 8 <= 0x1F00, len(cases)

out = []
w = out.append
w('.segment "LOAD"\n.word $0801\n.segment "CODE"')
w('.word next\n.word 10\n.byte $9E, "2061", 0\nnext: .word 0')
w('start:\n sei\n cld\n ldx #$ff\n txs')
for i, c in enumerate(cases):
    rec = RES + 8 * i
    w(f' lda #<{rec}\n sta $fb\n lda #>{rec}\n sta $fc\n jsr clr')
    for (addr, val) in c.get("pre", []): w(f' lda #{val}\n sta ${addr:04x}')
    for (addr, val) in c.get("zp", []): w(f' lda #{val}\n sta ${addr:02x}')
    w(f' ldx #{c["sp"]}\n txs\n lda #{c["a"]}\n ldx #{c["x"]}\n ldy #{c["y"]}')
    w(' sec' if c["c"] else ' clc')
    w(' sed' if c["d"] else ' cld')
    w(' .byte ' + ",".join("$%02x" % b for b in [c["op"]] + c["opnd"]))
    w(' jsr post\n ldx #$ff\n txs')
w(' lda #$a5\n sta $9fff\ndone: jmp done')
w('''clr: lda #0
 sta $fd
 tay
 ldx #4
 lda #$c4
 sta $fe
 lda #0
c1: sta ($fd),y
 iny
 bne c1
 inc $fe
 dex
 bne c1
 rts
post: sta $f2
 stx $f3
 sty $f4
 php
 pla
 sta $f5
 tsx
 inx
 inx
 stx $f6
 cld
 lda #0
 sta $fd
 lda #$c4
 sta $fe
 ldy #0
 ldx #4
sc: lda ($fd),y
 bne fnd
 iny
 bne sc
 inc $fe
 dex
 bne sc
 lda #$ff
 sta $f7
 sta $f8
 lda #0
 sta $f9
 jmp copy
fnd: sta $f9
 sty $f7
 lda $fe
 sta $f8
copy: ldy #0
cp: lda $f2,y
 sta ($fb),y
 iny
 cpy #8
 bne cp
 rts''')
open("opc.s", "w").write("\n".join(out) + "\n")
with open("cases.txt", "w") as f:
    for i, c in enumerate(cases):
        f.write("%d %s op=%02X a=%02X x=%02X y=%02X c=%d d=%d sp=%02X opnd=%s pre=%s zp=%s\n" % (
            i, c["name"], c["op"], c["a"], c["x"], c["y"], c["c"], c["d"], c["sp"],
            ",".join("%02X" % b for b in c["opnd"]), c.get("pre", []), c.get("zp", [])))
print(len(cases), "cases")
