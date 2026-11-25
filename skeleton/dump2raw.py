#!/usr/bin/env python3
"""
dump2raw.py - turn the output of "sidconv -d" into the stream of the skeleton.

    sidconv -m plain -S 1 -k 1 -t 60 -d -o song.bin tune.sid > dump.txt
    python3 dump2raw.py dump.txt song.bin song.raw

dump.txt has a line "frame: r0 r1 ... r7" (hexadecimal, AUDF1 AUDC1 ... AUDC4);
song.bin is only read for its first byte, the AUDCTL value sidconv chose.
"""
import sys

dump, header, out = sys.argv[1:4]
audctl = open(header, "rb").read(1)[0]
rows = [[int(x, 16) for x in line.split(":")[1].split()]
        for line in open(dump) if ":" in line]
if any(len(r) != 8 for r in rows):
    sys.exit("dump2raw: the skeleton plays one POKEY (8 registers): use sidconv -S 1")

last = [None] * 8                     # None: the first frame writes everything
body = bytearray()
for r in rows:
    mask, values = 0, []
    for i, v in enumerate(r):
        if v != last[i]:
            mask |= 1 << i
            values.append(v)
            last[i] = v
    body.append(mask)
    body += bytes(values)

open(out, "wb").write(bytes([audctl, len(rows) & 255, len(rows) >> 8]) + body)
print("%s: %d frames, %d bytes" % (out, len(rows), 3 + len(body)))
