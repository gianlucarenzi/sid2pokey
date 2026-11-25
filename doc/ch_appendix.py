# ch_appendix.py - appendices
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, section, sub, table)
import pdflib
from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak


def appendix(S, title, need_mm=None):
    """New page, or only if less than need_mm are left (so short appendices share a page)."""
    if need_mm is None:
        S.append(pdflib.PageBreak())
    else:
        S.append(CondPageBreak(need_mm * mm))
    S.append(pdflib.Heading(title, pdflib.ST["h1"]))


def build(S):
    pdflib.NUM.ch += 0
    # appendices are numbered A, B, ...
    appendix(S, "Appendice A — Gli indirizzi usati")
    P(S, "Le posizioni del sistema operativo e dell'hardware che il codice tocca.")
    table(S, [
        ["Nome", "Indirizzo", "Uso"],
        ["VDSLST", "$0200", "vettore del DLI dell'OS (il player lo punta al gestore, per K &gt; 1)"],
        ["SDLSTL", "$0230", "ombra del puntatore alla display list: la si scorre per mettere i bit di DLI"],
        ["ATRACT", "$004D", "contatore dell'attract mode, azzerato a ogni quadro"],
        ["SAVMSC", "$0058", "puntatore alla memoria schermo"],
        ["RTCLOK", "$0012-$0014", "orologio dei quadri; il byte basso ($14) scandisce «un quadro»"],
        ["MEMTOP", "$02E5", "ultimo indirizzo di RAM libera (400/800: base del blocco del font)"],
        ["COLOR1, COLOR2, COLOR4", "$02C5, $02C6, $02C8", "ombre dei colori: testo, sfondo, bordo"],
        ["CRSINH", "$02F0", "1 = cursore nascosto"],
        ["CHBAS", "$02F4", "pagina del set di caratteri (ombra)"],
        ["CH", "$02FC", "ultimo tasto premuto, $FF = nessuno"],
        ["AUDF1 … AUDC4", "$D200-$D207", "i quattro canali del POKEY 1"],
        ["AUDCTL", "$D208", "controllo audio del POKEY 1"],
        ["RANDOM, SKCTL, SKSTAT", "$D20A, $D20F", "numero casuale; controllo della tastiera (scrittura) / stato (lettura, bit 2 = tasto giù)"],
        ["POKEY 2", "$D210-$D217, $D218", "gli stessi registri del secondo POKEY (AUDCTL a $D218); RANDOM a $D21A, SKCTL a $D21F"],
        ["PALNT", "$D014", "GTIA: $01 su PAL, $0F su NTSC"],
        ["NMIEN, NMIST", "$D40E, $D40F", "abilitazione degli NMI (bit 7 DLI, bit 6 VBI); stato (bit 7 = era un DLI)"],
        ["SETVBV, XITVBV", "$E45C, $E462", "installa un vettore del VBI; uscita da un VBI (nell'XL/XE: i simboli di atari.inc)"],
        ["Vettore NMI", "$FFFA", "RAM sull'XL/XE con la ROM spenta: il player vi mette nmi_dli"],
    ], [38, 34, 98], mono_cols=(0, 1), font=7.8, keep=False, caption="Tabella A.1 — Indirizzi di sistema.")

    appendix(S, "Appendice B — Comandi")
    sub(S, "Makefile del progetto")
    table(S, [
        ["Bersaglio", "Effetto"],
        ["make", "costruisce <font face=\"Mono\">sid2pokey.com</font> per il target scelto (<font face=\"Mono\">MACH</font>)"],
        ["make build", "come sopra e lancia atari800 con <font face=\"Mono\">-stereo</font>"],
        ["make song.bin", "converte <font face=\"Mono\">$(SID)</font> (se il SID è più recente dello stream)"],
        ["make font.bin", "costruisce il font C64 da <font face=\"Mono\">$(CHARGEN)</font> (vuoto se non c'è la ROM)"],
        ["make atr", "copia il programma in <font face=\"Mono\">$(ATRFOLDER)/build</font> e crea l'immagine ATR con <font face=\"Mono\">dir2atr</font> (MyPicoDos 4.06)"],
        ["make clean", "toglie i file generati (compresi font.bin e i due programmi del PC)"],
    ], [38, 132], mono_cols=(0,), font=7.9)
    table(S, [
        ["Variabile", "Predefinito", "Significato"],
        ["MACH", "atarixl", "<font face=\"Mono\">atarixl</font> (XL/XE) o <font face=\"Mono\">atari</font> (400/800)"],
        ["SID", "Commando.sid (Rob Hubbard)", "il file da convertire, in $(HOME)/Music/C64Music/..."],
        ["SONG", "1", "il brano del file"],
        ["DURATION", "60", "secondi da convertire"],
        ["VIDEO", "pal", "<font face=\"Mono\">pal</font> o <font face=\"Mono\">ntsc</font>"],
        ["CHARGEN", "/usr/lib/vice/C64/chargen-901225-01.bin", "ROM dei caratteri C64"],
        ["STEREO", "-stereo", "opzione di atari800 per il secondo POKEY (vuoto per togliere)"],
        ["EMULATOR", "atari800", "l'emulatore di <font face=\"Mono\">make build</font>"],
        ["ROM", "~/ATARI/ATARIXL.ROM", "ROM dell'OS per l'emulatore (con MACH=atari: ATARIOSB.ROM)"],
        ["ATRFOLDER", "~/ATARI/ATR", "cartella di lavoro di <font face=\"Mono\">make atr</font>"],
    ], [28, 66, 76], mono_cols=(0,), font=7.8)
    code(S, "# convertire e provare, un SID, XL/XE (make ricostruisce sempre il .com)\n"
            "make -B song.bin SID=brano.sid DURATION=90 && make && make build\n\n"
            "# un 400/800 (48 KB): stream sotto circa 20 KB\n"
            "make -B song.bin SID=brano.sid DURATION=60 && make MACH=atari && make build MACH=atari\n\n"
            "# i test e lo skeleton\n"
            "sh tests/opcodes/run.sh     # core 6502 contro il riferimento di VICE (vice_ref.txt)\n"
            "cd skeleton && make SID=brano.sid", title="Ricette")

    appendix(S, "Appendice C — Mappa del repository", 85)
    table(S, [
        ["Percorso", "Contenuto"],
        ["tools/sidconv.c", "il convertitore (lettura PSID, ambiente C64, modello SID, mappatura POKEY, codificatore LZ)"],
        ["tools/cpu6502.h", "il core 6502 (solo PC)"],
        ["tools/mkfont.c", "ROM dei caratteri C64 → font Atari"],
        ["sp-common.asm", "il player: decodifica, VBI, DLI, due POKEY, rilevamento stereo"],
        ["sp-data.asm, sp-font.asm", "incorporano <font face=\"Mono\">song.bin</font> e <font face=\"Mono\">font.bin</font>"],
        ["sid2pokey.c", "la schermata: font, riquadri, VU meter, tastiera, preparazione dei DLI"],
        ["Makefile", "costruzione di tutto"],
        ["tests/opcodes/", "il test del core contro VICE: generatore, driver, riferimento, script"],
        ["skeleton/", "il player minimo, con convertitore di dump e Makefile"],
        ["doc/", "questo documento: <font face=\"Mono\">build_pdf.py</font> lo rigenera (listati letti dai sorgenti)"],
        ["sid2gumby/", "il progetto d'origine (GPL 3): il caso «eseguire il brano sull'Atari»"],
        ["README.md", "il riassunto del progetto, con le misure"],
    ], [42, 128], mono_cols=(0,), font=7.9)

    appendix(S, "Appendice D — Le formule", 125)
    table(S, [
        ["Grandezza", "Formula"],
        ["frequenza di una voce SID", "f = Fn × clock_SID / 2<super>24</super>"],
        ["divisore POKEY a 8 bit", "N = clk / (2 f) − 1;  clk = CPU/28 (64 kHz) o CPU/114 (15 kHz)"],
        ["divisore POKEY a 16 bit, 1,79 MHz", "N = CPU / (2 f) − 7"],
        ["rumore", "come l'onda, con f → 8 f"],
        ["errore di intonazione", "1200 × log<sub>2</sub>(f_ottenuta / f_voluta) centesimi; + 1200 per ogni ottava ripiegata"],
        ["volume POKEY", "(livello × volume_SID + 127) / 255, 0-15"],
        ["frequenza di quadro", "CPU / (righe × 114)"],
        ["frequenza di play (CIA)", "clock_SID / (latch + 1)"],
        ["record per quadro", "K = round(f_play / f_quadro), 1-4"],
        ["chiamata di play per un record", "floor(((n + j/K) / f_quadro) × f_play)"],
        ["punto di un DLI", "(248 + j × righe / K) mod righe, j = 1 … K−1"],
        ["inviluppo, attacco", "255 × periodo cicli (periodo 9…31251)"],
        ["inviluppo, decadimento", "un passo ogni p scatti, p = 1, 2, 4, 8, 16, 30 sotto 255, 93, 54, 26, 14, 6"],
        ["posizione sorgente di un match", "(pos − offset) mod 512"],
        ["dimensione dell'header", "109 + 3 × N byte (N = 8 o 16)"],
        ["indirizzo del font (400/800)", "(MEMTOP + 1 − $400) &amp; $FC00"],
    ], [58, 112], font=7.9)

    appendix(S, "Appendice E — Glossario", 125)
    table(S, [
        ["Termine", "Significato"],
        ["ADSR", "Attack, Decay, Sustain, Release: l'inviluppo di volume del SID"],
        ["ANTIC", "il chip video dell'Atari: legge la display list e il set di caratteri"],
        ["AUDF / AUDC / AUDCTL", "divisore, controllo e controllo generale del POKEY"],
        ["CIA", "il chip dei timer del C64; il suo timer A fissa il ritmo dei brani non legati al quadro"],
        ["DLI", "Display List Interrupt: un NMI a una scanline scelta, richiesto da un bit della display list"],
        ["HIRAM", "il bit 1 della porta $01 del C64: se vale 1 il KERNAL è visibile"],
        ["HVSC", "High Voltage SID Collection: l'archivio di brani SID"],
        ["init / play", "le due routine di un brano SID: prepara un brano; chiamata a ogni quadro"],
        ["KERNAL", "il sistema operativo del C64 (qui una ROM minima finta)"],
        ["multispeed", "brano con più chiamate di play per quadro (2x, 3x, 4x)"],
        ["NMI", "interrupt non mascherabile: VBI e DLI dell'Atari lo usano"],
        ["PSID / RSID", "i formati dei file SID; RSID pretende un C64 vero"],
        ["record", "i valori di tutti i registri POKEY per un istante (una chiamata di play)"],
        ["VBI", "Vertical Blank Interrupt: una volta per quadro, a inizio dell'intervallo di ritorno"],
        ["VU meter", "indicatore di livello: qui una barra per voce"],
    ], [42, 128], font=7.9)

    appendix(S, "Appendice F — Riferimenti e licenze", 100)
    bullets(S, [
        "<b>cc65</b>: compilatore, assemblatore e linker per il 6502; la documentazione dei target <i>atari</i> e "
        "<i>atarixl</i> descrive la memoria riservata, il banking della ROM e gli interrupt.",
        "<b>atari800</b>: l'emulatore usato per tutte le prove; il registratore dei POKEY (<font face=\"Mono\">-pokeyrec</font>) "
        "è stato la base delle verifiche.",
        "<b>VICE</b> (x64sc): il riferimento per gli opcode non documentati e la fonte della ROM dei caratteri C64.",
        "<b>reSID</b>: il modello da cui deriva il generatore di inviluppo del SID usato qui (contatore di velocità "
        "e contatore esponenziale).",
        "<b>sid2gumby</b> (Ivo van Poorten, GPL 3): il progetto da cui questo è partito, nella cartella "
        "<font face=\"Mono\">sid2gumby/</font>.",
        "<b>HVSC</b>: la raccolta di brani su cui sono state fatte le misure.",
        "Per i dettagli hardware dell'Atari sono utili l'<i>Altirra Hardware Reference Manual</i>, l'<i>Atari 400/800 "
        "Technical Reference Notes</i> e l'<i>Operating System User's Manual</i>.",
    ])
    callout(S, "ATTENZIONE", "La ROM dei caratteri del C64 è di Commodore. Il repository non la contiene e non contiene il font "
                             "che se ne ricava: <font face=\"Mono\">font.bin</font> si costruisce in locale da una copia "
                             "che si ha già (per esempio quella distribuita con VICE). Le schermate di questo documento mostrano "
                             "il risultato; non contengono la ROM.")
