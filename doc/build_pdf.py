#!/usr/bin/env python3
# build_pdf.py - builds the guide
#
#   python3 doc/build_pdf.py              # Italian: doc/sid2pokey-guida.pdf
#   python3 doc/build_pdf.py --lang en    # English: doc/sid2pokey-guide.pdf
#
# The listings are read from the files of the repository, the figures from doc/img.
# The English text lives in doc/en/ (one module per chapter, same structure as the
# Italian ones in doc/); doc/en is put first on the module path, so the same
# driver builds either language from the same layout library (pdflib.py).
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

LANGS = {
    "it": dict(out="sid2pokey-guida.pdf",
               title="SID → POKEY: costruire un SID player per gli Atari 8-bit",
               footer="sid2pokey — guida alla realizzazione di un SID player"),
    "en": dict(out="sid2pokey-guide.pdf",
               title="SID → POKEY: building a SID player for the Atari 8-bit",
               footer="sid2pokey — a guide to building a SID player"),
}


def main():
    lang = "it"
    if "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]
    if lang not in LANGS:
        sys.exit("unknown language %r (it, en)" % lang)
    cfg = LANGS[lang]

    sys.path.insert(0, HERE)
    if lang != "it":
        sys.path.insert(0, os.path.join(HERE, lang))

    pdflib = importlib.import_module("pdflib")
    ch_intro = importlib.import_module("ch_intro")

    out = os.path.join(HERE, cfg["out"])
    doc = pdflib.Doc(out, cfg["title"], cfg["footer"])
    S = []
    ch_intro.cover(S)
    ch_intro.toc(S)
    ch_intro.how_to_read(S)
    ch_intro.ch1(S)
    ch_intro.ch2(S)
    for mod in ("ch_psid_conv", "ch_stream_player", "ch_ui", "ch_skeleton_tests", "ch_appendix"):
        importlib.import_module(mod).build(S)
    doc.multiBuild(S)
    print("written", out)


if __name__ == "__main__":
    main()
