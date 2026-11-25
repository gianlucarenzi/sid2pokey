#!/usr/bin/env python3
# build_pdf.py - builds doc/sid2pokey-guida.pdf
#
#   python3 doc/build_pdf.py
#
# The listings are read from the files of the repository, the figures from doc/img.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pdflib
from pdflib import Doc, HERE

import ch_intro

OUT = os.path.join(HERE, "sid2pokey-guida.pdf")


def main():
    doc = Doc(OUT, "SID → POKEY: costruire un SID player per gli Atari 8-bit",
              "sid2pokey — guida alla realizzazione di un SID player")
    S = []
    ch_intro.cover(S)
    ch_intro.toc(S)
    ch_intro.how_to_read(S)
    ch_intro.ch1(S)
    ch_intro.ch2(S)
    for mod in ("ch_psid_conv", "ch_stream_player", "ch_ui", "ch_skeleton_tests", "ch_appendix"):
        if os.path.exists(os.path.join(HERE, mod + ".py")):
            __import__(mod).build(S)
    doc.multiBuild(S)
    print("written", OUT)


if __name__ == "__main__":
    main()
