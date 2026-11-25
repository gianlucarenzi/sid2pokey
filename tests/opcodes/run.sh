#!/bin/sh
# Test of the undocumented "unstable" opcodes of tools/cpu6502.h.
#
# Builds a C64 program with several hundred cases (gen.py), runs it in
# cpu6502.h (driver.c) and compares every result record with vice_ref.txt,
# which holds what VICE x64sc 3.10 produced for the same program.  Needs
# python3, ca65/ld65 (cc65) and a C compiler; VICE is only needed to refresh
# the reference (vice_run.py).
set -e
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
[ -n "$tmp" ] || exit 2
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
python3 -I "$here/gen.py"
printf 'MEMORY { MAIN: file = "opc.prg", start = $07FF, size = $7800; }\nSEGMENTS { LOAD: load = MAIN, type = ro; CODE: load = MAIN, type = ro; }\n' > opc.cfg
ca65 opc.s -o opc.o
ld65 -C opc.cfg opc.o -o opc.prg
${CC:-gcc} -O2 -Wall -Wno-unused-function -I"$here/../../tools" -o driver "$here/driver.c"
./driver opc.prg "$(wc -l < cases.txt)" 0x080D > mine.txt
if cmp -s mine.txt "$here/vice_ref.txt"; then
	echo "opcodes: $(wc -l < mine.txt) cases, identical to VICE"
else
	echo "opcodes: MISMATCH against vice_ref.txt"
	diff mine.txt "$here/vice_ref.txt" | head -10
	exit 1
fi
