# ch_ui.py - chapter 7: the screen, the font, the VU meters
import diagrams as D
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, section, sub, table)


def build(S):
    chapter(S, "La schermata, il font e i VU meter")
    P(S, "La schermata è un programma C (<font face=\"Mono\">sid2pokey.c</font>, circa 500 righe) che non suona nulla: "
         "disegna e legge. La musica è degli interrupt; il programma, ogni quadro, guarda i valori che il player "
         "ha appena decodificato e muove le barre.")
    section(S, "Com'è fatta")
    figure(S, "ui_single_xe.png", "Figura 7.1 — Un SID, XL/XE: titolo, autore e copyright dal file; tre VU meter; stato.",
           width_mm=128)
    table(S, [
        ["Righe", "Contenuto"],
        ["0", "barra del titolo in video inverso: «SID 2 POKEY» e «C64 MUSIC ON ATARI»"],
        ["1", "vuota; qui compare l'avviso se lo stream e la macchina hanno frequenze di quadro diverse"],
        ["2-6", "riquadro: titolo, autore, copyright (32 caratteri ciascuno)"],
        ["8-21", "riquadro «VOICES»: 9 righe di barre (9-17), i numeri delle voci (18), le didascalie dei POKEY (19), una riga libera (20) e il bordo (21)"],
        ["22", "stato: 1 o 2 POKEY, frequenza di quadro, velocità (1X-4X), tempo trascorso"],
        ["23", "«PLAYING / STOPPED — PRESS ANY KEY» in video inverso"],
    ], [20, 150], mono_cols=(0,), caption="Tabella 7.1 — Le 24 righe da 40 colonne.")
    P(S, "I VU meter sono <b>tre</b> con un POKEY, a colonne larghe 6 caratteri, e <b>sei</b> con due POKEY, a colonne di 4 "
         "caratteri divise in due gruppi (figura 2.1). I numeri 1-3 sono le voci del SID, le didascalie dicono su quale "
         "chip.")
    section(S, "I colori")
    P(S, "Il modo testo dell'Atari ha due colori: lo sfondo (COLOR2) e il testo, che prende la <b>tinta</b> dello sfondo e la "
         "<b>luminanza</b> di COLOR1; il bordo (COLOR4) è a parte. Il C64 ha lo stesso schema (bordo azzurro, sfondo blu, "
         "testo azzurro), quindi basta scegliere una tinta e tre luminanze.")
    table(S, [
        ["Registro (ombra)", "Indirizzo", "Valore", "Effetto"],
        ["COLOR4", "$02C8", "$7A", "bordo: tinta 7, luminanza 10 (azzurro)"],
        ["COLOR2", "$02C6", "$74", "sfondo: tinta 7, luminanza 4 (blu scuro)"],
        ["COLOR1", "$02C5", "$0C", "luminanza del testo: 12 (la tinta è quella dello sfondo)"],
    ], [38, 24, 18, 90], mono_cols=(0, 1, 2), caption="Tabella 7.2 — I colori della schermata (tinta predefinita $70, "
                                                      "cambiabile con <font face=\"Mono\">-DUI_HUE=$..</font>).")
    figure(S, "colors.png", "Figura 7.2 — Le tre tinte provate: $60 (viola), $70 (blu: la più simile al C64, scelta), "
                            "$80 (blu-verde).", width_mm=162)
    callout(S, "NOTA", "I colori si scrivono nei registri <b>ombra</b> del sistema operativo, che li copia nei registri "
                       "hardware a ogni vertical blank. Con due soli colori non si possono dare colori diversi alle barre senza "
                       "DLI, che il player usa già per i brani multispeed.")
    section(S, "Il font C64")
    P(S, "La ROM dei caratteri del C64 ha 4096 byte: due set da 256 glifi (il secondo metà è il negativo del primo, "
         "che sull'Atari fa da solo il bit 7 del codice). Il set 1 ha maiuscole e grafica, il set 2 minuscole e maiuscole. "
         "<font face=\"Mono\">tools/mkfont</font> ne ricava il font dell'Atari: 128 glifi da 8 byte nell'ordine dei "
         "<b>codici schermo interni</b> dell'Atari, che non sono quelli dell'ASCII.")
    table(S, [
        ["Codice Atari", "Glifo", "Preso dal C64"],
        ["$00-$1F", "spazio ! \" # … ? (cifre e punteggiatura)", "codici schermo 32-63 (set 1)"],
        ["$20", "@", "codice 0"],
        ["$21-$3A", "A-Z", "set 2, codici 65-90 (le maiuscole del set minuscolo)"],
        ["$3B-$3F", "[ £ ] ↑ ←", "codici 27-31"],
        ["$40-$5F", "grafica (le forme PETSCII)", "set 1, codici 64-95"],
        ["$60", "grafica", "codice 96"],
        ["$61-$7A", "a-z", "set 2, codici 1-26"],
        ["$7B-$7F", "grafica", "codici 123-127"],
    ], [28, 80, 62], mono_cols=(0,), font=7.9, caption="Tabella 7.3 — Dall'ordine del C64 a quello dell'Atari. L'ASCII "
                                                        "$20-$5F diventa il codice meno $20; $60-$7A resta uguale.")
    figure(S, "font_map.png", "Figura 7.3 — I 128 glifi di font.bin, per codice schermo Atari (la ROM del C64 è di "
                              "Commodore: il file si costruisce in locale e non è nel repository).", width_mm=150)
    sub(S, "I glifi che il programma disegna da sé")
    P(S, "Le cornici e le barre non dipendono dal font di base: il programma sovrascrive alcuni codici con glifi suoi, "
         "così la schermata funziona anche senza la ROM del C64 (figura 7.5).")
    items = []
    for k in range(1, 8):
        items.append(("$%02X" % (0x47 + k), [0xFF if r >= 8 - k else 0 for r in range(8)]))
    flow(S, D.GlyphGrid(items, per_row=7, px=3.6, title="Barre: i k pixel in basso (codici $48-$4E)"), "")
    items = []
    for k in range(1, 8):
        items.append(("$%02X" % (0x50 + k), [0xFF if r == k else 0 for r in range(8)]))
    flow(S, D.GlyphGrid(items, per_row=7, px=3.6, title="Marcatore del picco: una riga (codici $51-$57)"), "")
    frame = [("$40", [0, 0, 0, 0xFF, 0xFF, 0, 0, 0]), ("$5D", [0x18] * 8),
             ("$60", [0, 0, 0, 0x1F, 0x1F, 0x18, 0x18, 0x18]), ("$7B", [0, 0, 0, 0xF8, 0xF8, 0x18, 0x18, 0x18]),
             ("$7C", [0x18, 0x18, 0x18, 0x1F, 0x1F, 0, 0, 0]), ("$7D", [0x18, 0x18, 0x18, 0xF8, 0xF8, 0, 0, 0])]
    flow(S, D.GlyphGrid(frame, per_row=7, px=3.6, title="Cornici: linea orizzontale, verticale e i quattro angoli"),
         "Figura 7.4 — I 20 glifi definiti dal programma; sono copie delle forme del C64 e vanno nei codici che "
         "l'Atari usa per la grafica di controllo.")
    figure(S, "ui_nofont_xe.png", "Figura 7.5 — La stessa schermata senza la ROM del C64: il font di base è quello Atari, "
                                  "cornici e barre sono identiche.", width_mm=118)
    section(S, "Dove sta il font", need=110)
    P(S, "Il font deve stare in RAM, perché va modificato, e il registro che lo indica (CHBAS) vuole una pagina "
         "allineata a 1 KB. Come ci si arriva dipende dal modello.")
    flow(S, D.MemoryMaps(), "Figura 7.6 — La memoria dei due target (schema semplificato).")
    bullets(S, [
        "<b>XL/XE (target atarixl).</b> cc65 spegne la ROM dell'OS e ha già copiato il font di ROM in RAM a $E000, dove "
        "l'ANTIC lo cerca: basta sovrascriverlo <b>sul posto</b>. CHBAS resta $E0.",
        "<b>400/800 (target atari).</b> La ROM è sempre accesa e non si modifica. Il linker riserva <b>2 KB</b> in cima "
        "alla RAM libera (<font face=\"Mono\">-Wl -D,__RESERVED_MEMORY__=0x800</font>); il programma prende dentro quel blocco il "
        "kilobyte allineato e punta CHBAS lì. Il blocco è di 2 KB perché il confine di 1 KB cade da qualche parte "
        "nel mezzo.",
    ])
    code(S, excerpt("sid2pokey.c", "static void install_font(void)", "CHBAS = (unsigned char) ((unsigned) font >> 8);") + "\n}",
         title="sid2pokey.c — install_font()", size=6.9)
    table(S, [
        ["Passo", "400/800", "XL/XE"],
        ["indirizzo del font", "(MEMTOP + 1 − $400) &amp; $FC00", "$E000"],
        ["base di partenza", "copia del font di ROM a $E000", "il font già in RAM"],
        ["font C64", "copiato sul blocco, se font.bin non è vuoto", "copiato sul posto, se font.bin non è vuoto"],
        ["glifi propri", "scritti sul blocco", "scritti sul posto"],
        ["CHBAS ($02F4)", "pagina del blocco", "$E0 (invariato)"],
    ], [40, 66, 64], mono_cols=(), font=7.8, caption="Tabella 7.4 — Le stesse operazioni sui due modelli.")
    section(S, "I VU meter", need=80)
    P(S, "Una barra rappresenta il <b>volume del canale POKEY</b> che suona quella voce SID. Il convertitore scrive nell'header, "
         "per ogni voce, il registro AUDC che ne contiene il volume (nei 4 bit bassi): quello del canale della voce, oppure "
         "AUDC2/AUDC4 della coppia a 16 bit. Il programma legge quel valore da <font face=\"Mono\">outbuf</font>, "
         "il buffer in cui il player lascia i valori dell'ultimo record.")
    table(S, [
        ["Volume POKEY", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"],
        ["Livello (0-63)", "0", "4", "8", "13", "17", "21", "25", "29", "34", "38", "42", "46", "50", "55", "59", "63"],
    ], [26] + [9.0] * 16, align="L" + "C" * 16, font=7.2,
          caption="Tabella 7.5 — Dal volume al livello della barra: 9 celle da 7 livelli.")
    bullets(S, [
        "<b>Segmenti.</b> Ogni cella contiene 7 pixel pieni e uno vuoto (il filo tra due segmenti): una barra intera "
        "sono 9 celle, 63 livelli. Una cella parziale usa il glifo con k pixel in basso.",
        "<b>Caduta.</b> Il livello sale subito al nuovo valore e scende di 3 livelli per quadro: da pieno a zero in circa "
        "21 quadri (0,4 s).",
        "<b>Picco.</b> Un marcatore sottile segue il massimo, resta fermo 24 quadri (circa mezzo secondo) e poi scende di 1 "
        "livello per quadro. Se cade nella stessa cella della cima della barra non si disegna.",
    ])
    code(S, excerpt("sid2pokey.c", "static void vu_update(void)", "draw_bar(v);") + "\n\t}\n}",
         title="sid2pokey.c — vu_update(): volume, caduta e picco di ogni voce", size=6.9)
    section(S, "Tastiera, tempo e stati")
    bullets(S, [
        "<b>Un quadro alla volta.</b> Il programma aspetta il cambio del byte basso dell'orologio del sistema (RTCLOK, "
        "$0014), che il VBI incrementa; azzera ogni volta ATRACT ($004D) per evitare lo «attract mode» dei colori.",
        "<b>Tempo.</b> (quadri − quadri rimasti) / 50 o 60: i contatori sono quelli del player, quindi il tempo ricomincia da "
        "zero quando il brano riparte.",
        "<b>Stati.</b> Un tasto ferma il brano (barre a zero, «STOPPED»), il successivo lo fa ripartire dall'inizio. "
        "Il programma non ritorna mai al DOS: senza un DOS l'XL/XE ricomincerebbe il boot e riempirebbe lo schermo di "
        "<font face=\"Mono\">BOOT ERROR</font>.",
        "<b>Tastiera.</b> Si legge CH ($02FC), dove il sistema lascia l'ultimo tasto («nessuno» = $FF), e si "
        "consuma dopo il rilascio (SKSTAT, $D20F, bit 2).",
    ])
    figure(S, "ui_stopped_xe.png", "Figura 7.7 — Dopo uno stop: barre a zero, «STOPPED», il tempo resta dov'era.",
           width_mm=118)
    code(S, excerpt("sid2pokey.c", "static unsigned char key_pressed(void)", "CH = 0xFF;") + "\n}",
         title="sid2pokey.c — la tastiera, letta da CH", size=7)
    section(S, "Le trappole dello schermo", need=70)
    P(S, "Su XL/XE la ROM dell'OS è spenta e cc65 la riaccende per ogni chiamata al sistema o interrupt; l'ANTIC, in "
         "quei momenti, legge il font dalla ROM. Tre difetti reali sono venuti da qui o da una chiamata al sistema "
         "operativo.")
    figure(S, "pitfall_dli_band.png", "Figura 7.8 — Prima: una banda di caratteri Atari (cuori e frecce) a metà schermo, sui "
                                      "brani multispeed.", width_mm=112)
    callout(S, "TRAPPOLA", "<b>La banda di caratteri vecchi.</b> Il DLI passava dal vettore dell'OS, e il wrapper di cc65 teneva "
                           "la ROM accesa per tutto il gestore (circa 35 scanline con 16 registri): l'ANTIC leggeva il font di "
                           "ROM per quelle righe. <i>Rimedio</i>: sul target atarixl il DLI è servito direttamente dal "
                           "vettore NMI (capitolo 6), senza accendere la ROM.")
    figure(S, "pitfall_rom_font.png", "Figura 7.9 — Prima: da fermo, tutta la schermata con il font Atari (cuori al posto "
                                      "delle cornici).", width_mm=112)
    callout(S, "TRAPPOLA", "<b>Il font che torna Atari da fermo.</b> L'attesa del tasto con <font face=\"Mono\">cgetc()</font> "
                           "è una chiamata al sistema che si blocca: la ROM resta accesa finché non si preme un tasto. "
                           "<i>Rimedio</i>: attendere con un ciclo che legge CH; niente chiamate al sistema dopo l'avvio "
                           "(neppure <font face=\"Mono\">clrscr()</font>, sostituito da un <font face=\"Mono\">memset</font> "
                           "sullo schermo).")
    figure(S, "pitfall_key_echo.png", "Figura 7.10 — Prima: la riga del titolo nei tre stati (suono, fermo, di nuovo "
                                      "suono): nel secondo manca un carattere, la «I» di SID.", width_mm=112)
    callout(S, "TRAPPOLA", "<b>L'eco dei tasti.</b> <font face=\"Mono\">cgetc()</font> legge attraverso il gestore dello "
                           "schermo, che scrive il carattere digitato alla posizione del cursore, in alto a sinistra: "
                           "ogni tasto bucava la barra inversa del titolo (il tasto stesso, in video normale). "
                           "<i>Rimedio</i>: leggere CH direttamente.")
    callout(S, "VERIFICATO", "Con tasti veri inviati a atari800 (barra spaziatrice e Invio, che per il gestore dello schermo "
                             "è il più insidioso) il riquadro del titolo e la riga 0 restano identici pixel per pixel "
                             "tra suono, pausa e ripartenza, sul 400/800 e sull'XL/XE. Prima la riga 0 cambiava di 168 pixel.")
    callout(S, "NOTA", "Resta una cosa non eliminata: l'interrupt della tastiera dell'OS gira con la ROM accesa per un paio di "
                       "scanline. Una pressione può far vibrare un istante una scanline; non lascia segni.")
