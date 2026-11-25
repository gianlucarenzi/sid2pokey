# ch_stream_player.py - chapters 5 (the stream) and 6 (the 6502 player)
import os

import diagrams as D
from pdflib import (HERE, bullets, callout, chapter, code, excerpt, figure, flow, m, numbered, P, section, sub,
                    table)

REGNAMES = ["AUDF1", "AUDC1", "AUDF2", "AUDC2", "AUDF3", "AUDC3", "AUDF4", "AUDC4"]


def build(S):
    ch5(S)
    ch6(S)


def example_header():
    d = open(os.path.join(HERE, "examples", "commando.bin"), "rb").read()
    return d


def ch5(S):
    chapter(S, "Lo stream song.bin")
    P(S, "Lo stream è l'unica cosa che passa dal PC all'Atari. Deve essere piccolo (la memoria è poca), facile da "
         "decodificare in pochi cicli e verificabile. La scelta fatta è un <b>flusso LZ separato per ogni registro "
         "POKEY</b>: i valori di AUDF1 formano una sequenza, quelli di AUDC1 un'altra, e così via. Dentro una "
         "sequenza le ripetizioni sono frequentissime (un vibrato, un inviluppo, una nota che si ripete in ogni "
         "battuta), mentre mescolare i registri le nasconderebbe.")
    section(S, "Visione d'insieme")
    flow(S, D.StreamLayout(), "Figura 5.1 — Il file: un header di campi fissi, le tre stringhe, la tabella dei registri, "
                              "poi i flussi (i registri che non cambiano mai non ne hanno uno).")
    bullets(S, [
        "Ogni flusso contiene <b>un valore per record</b>: dopo la decodifica dei flussi di tutti i registri si ha lo "
        "stato completo del POKEY per quell'istante.",
        "Un quadro video contiene <b>K</b> record consecutivi (K da 1 a 4): il primo lo suona il VBI, gli altri i DLI.",
        "I registri costanti (tipico: il canale 4 inutilizzato, AUDC1 = 0 con la coppia a 16 bit) stanno solo nella "
        "tabella: il valore è lì, e non costano un flusso.",
        "Alla fine dello stream si azzerano tutti i decodificatori e il brano ricomincia: la prima decodifica "
        "riscrive ogni registro, quindi il ciclo è esatto.",
    ])
    section(S, "L'header", need=45)
    table(S, [
        ["Offset", "Byte", "Contenuto"],
        ["0", "1", "AUDCTL del POKEY 1"],
        ["1", "1", "frequenza video per cui è stato fatto: 50 o 60"],
        ["2-3", "2", "numero di quadri (little endian)"],
        ["4", "1", "record per quadro, K"],
        ["5", "1", "AUDCTL del POKEY 2 (0 se un solo POKEY)"],
        ["6", "1", "numero di POKEY: 1 o 2"],
        ["7-12", "6", "per ognuna delle 6 voci, il registro (0-15) che ne contiene il volume nei 4 bit bassi, o $FF"],
        ["13-44", "32", "titolo (ASCII, riempito di zeri)"],
        ["45-76", "32", "autore"],
        ["77-108", "32", "copyright"],
        ["109 …", "3 × N", "tabella dei registri: N = 8 con un POKEY, 16 con due; per ogni registro: tipo (0 costante, "
                              "1 flusso), poi il valore oppure l'offset a 16 bit del flusso dall'inizio del file"],
    ], [20, 14, 136], mono_cols=(0,), keep=False, caption="Tabella 5.1 — L'header di song.bin: 109 + 3 N byte.")
    d = example_header()
    vu = []
    for r in d[7:13]:
        vu.append("—" if r == 0xFF else "POKEY%d.%s" % (r // 8 + 1, REGNAMES[r % 8]))
    entries = []
    offs = []
    for r in range(8):
        t, a, b = d[109 + 3 * r:109 + 3 * r + 3]
        offs.append((a | b << 8) if t else None)
    ends = [o for o in offs if o is not None] + [len(d)]
    ends = sorted(ends)
    rows = [["Registro", "Tipo", "Valore o offset", "Byte del flusso"]]
    for r in range(8):
        t, a, b = d[109 + 3 * r:109 + 3 * r + 3]
        if t == 0:
            rows.append([REGNAMES[r], "costante", "$%02X" % a, "—"])
        else:
            off = a | b << 8
            nxt = min(e for e in ends if e > off)
            rows.append([REGNAMES[r], "flusso LZ", str(off), str(nxt - off)])
    sub(S, "Un esempio reale: Commando, 60 secondi")
    P(S, "I primi byte di <font face=\"Mono\">song.bin</font> per Commando di Rob Hubbard (un SID, "
         "AUDCTL $%02X): %d quadri, K = %d, %d POKEY; i VU meter leggono i registri %s. Il titolo è «%s»."
         % (d[0], d[2] | d[3] << 8, d[4], d[6], ", ".join(vu[:3]), d[13:45].rstrip(b"\0").decode()))
    table(S, rows, [34, 34, 46, 56], mono_cols=(0,), align="LLRR", caption=
          "Tabella 5.2 — La tabella dei registri dello stream di Commando (offset in byte dall'inizio del file); "
          "lo stream intero è di %d byte." % len(d))
    section(S, "I flussi LZ", need=70)
    P(S, "Ogni flusso è una sequenza di <b>gruppi</b>: un byte di flag e fino a otto token. I flag si leggono dal bit 7 "
         "verso il bit 0: <b>1 = letterale</b> (un byte, il valore stesso), <b>0 = match</b> (due byte).")
    flow(S, D.LzTokens(), "Figura 5.2 — Un gruppo: il byte di flag e i token che descrive.")
    P(S, "Un match copia da <b>3 a 130</b> valori dalla storia dello stesso registro, partendo da <b>1 a 512 valori "
         "indietro</b>. Sovrapposti: un match di offset 1 e lunghezza 100 ripete cento volte l'ultimo valore, ed è "
         "come si codificano i tratti costanti. Ecco come si codifica e si decodifica la sequenza "
         "<font face=\"Mono\">5 5 5 5 7</font>:")
    table(S, [
        ["Passo", "Flag", "Token (byte)", "Uscita", "Storia dopo il passo"],
        ["1", "1", "$05", "5", "5"],
        ["2", "0", "$01 $00  → offset 1, lunghezza 0 + 3 = 3", "5 5 5", "5 5 5 5"],
        ["3", "1", "$07", "7", "5 5 5 5 7"],
    ], [14, 12, 74, 26, 44], mono_cols=(2,), caption=
          "Tabella 5.3 — Lo stream di quel tratto è <font face=\"Mono\">A0 05 01 00 07</font>: il byte di flag "
          "$A0 = 1 0 1 + cinque bit inutilizzati.")
    callout(S, "NOTA", "Un match con offset 0 vale 512 indietro: nei due byte l'offset ha 9 bit, quindi 0 ne rappresenta "
                       "512 e 1 ne rappresenta 1. Il decodificatore calcola la posizione sorgente come "
                       "<font face=\"Mono\">(pos − offset) mod 512</font>.")
    code(S, excerpt("tools/sidconv.c", "static size_t lz_encode(", "dp[i] = best;") + "\n\t\tclen[i] = (short)bl;\n\t\tcoff[i] = (short)bestoff;\n\t}\n\t...",
         title="tools/sidconv.c — lz_encode(): parsing ottimo (per ogni posizione il costo minimo della coda)",
         size=6.9)
    P(S, "Il costo nel modello è di 9 bit per un letterale (1 di flag + 8) e 17 per un match (1 + 16): la "
         "programmazione dinamica parte dalla fine del flusso e per ogni posizione sceglie tra il letterale e il match "
         "che minimizza il costo totale. Il codificatore gira in meno di un decimo di secondo per un minuto di musica.")
    section(S, "Perché questo formato")
    P(S, "Prima di fissare il formato sono state misurate alternative su 31 brani (45 secondi ciascuno), con un modello di "
         "costo: i valori grezzi di ogni registro oppure le differenze tra record consecutivi, con finestre di 256, 512 e "
         "1024 valori. La scelta è ricaduta sui valori grezzi con finestra da 512.")
    table(S, [
        ["Schema", "Byte (31 brani)", "Rispetto al formato a maschera"],
        ["maschera + valori modificati (non compresso)", "238 181", "100 %"],
        ["LZ per registro, valori grezzi, finestra 256", "47 185", "19 %"],
        ["LZ per registro, valori grezzi, finestra <b>512</b>", "<b>37 666</b>", "<b>15 %</b>"],
        ["LZ per registro, valori grezzi, finestra 1024", "40 420", "16 %"],
        ["LZ per registro, differenze, finestra 256", "47 887", "20 %"],
        ["LZ per registro, differenze, finestra 512", "38 500", "16 %"],
        ["LZ per registro, differenze, finestra 1024", "41 005", "17 %"],
    ], [86, 34, 50], align="LRR", caption="Tabella 5.4 — Stime del modello di costo (non l'uscita reale del codificatore).")
    bullets(S, [
        "<b>I valori grezzi battono le differenze</b>: il decodificatore non deve accumulare nulla, ed è più semplice.",
        "<b>512 è il compromesso</b>: con 9 bit di offset restano 7 bit per la lunghezza (fino a 130); con finestre "
        "più grandi la lunghezza si accorcia e si perdono i tratti lunghi.",
        "<b>Un flusso per registro</b> permette a ognuno di ripetersi per conto suo: le note cambiano, l'inviluppo del "
        "volume no.",
    ])
    table(S, [
        ["Misura", "Risultato"],
        ["31 brani, 45 s: formato a maschera → LZ (uscita reale, ADSR esatto)", "238 336 → 39 766 byte (circa 6 volte)"],
        ["compressione per brano (ADSR lineare, misura precedente)", "da 3,8 a 13,3 volte; mediana 6,7"],
        ["87 brani, 60 s: dimensione dello stream", "mediana 1,7 KB, 95° percentile 3,3 KB, massimo 9,5 KB"],
        ["Commando, 60 s", "2207 byte (0,7 byte per quadro)"],
        ["brano a 4x, 5 minuti", "16 KB (circa 1,1 byte per record)"],
        ["brano a due SID (Double), 90 s", "7,4 KB (1,6 byte per quadro, 2 record per quadro)"],
    ], [92, 78], font=7.9, caption="Tabella 5.5 — Le dimensioni che si ottengono.")
    callout(S, "ATTENZIONE", "La compressione dipende dal brano: <i>Slanted</i> di Julian Jaymz (a due SID) produce circa 4,7 "
                             "byte per quadro, quattro volte un brano tipico, e in un 400/800 regge solo circa 80 secondi.")
    section(S, "La verifica incorporata")
    P(S, "Dopo aver scritto lo stream, il convertitore lo <b>decodifica di nuovo</b> con gli stessi passi del player "
         "(registro di flag con bit sentinella, buffer circolari da 512 valori, posizione sorgente "
         "<font face=\"Mono\">(pos − offset) mod 512</font>) e lo confronta con i record originali. Se un solo valore "
         "differisce il file non viene scritto e il programma si ferma con <font face=\"Mono\">internal error</font>. "
         "Sui 4370 brani di prova non è mai successo.")


def ch6(S):
    chapter(S, "Il player 6502")
    P(S, "Il player è il file <font face=\"Mono\">sp-common.asm</font> (circa 500 righe di ca65): decodifica lo "
         "stream e scrive i registri POKEY dagli interrupt. La schermata (capitolo 7) è un programma C che lo "
         "usa attraverso tre funzioni e qualche variabile.")
    section(S, "L'interfaccia")
    table(S, [
        ["Simbolo", "Direzione", "Significato"],
        ["initPlayer()", "C → asm", "silenzia i POKEY, legge l'header, individua il secondo POKEY, prepara i decodificatori"],
        ["startPlayer()", "C → asm", "installa il VBI (e per K &gt; 1 il gestore dei DLI); da qui la musica va da sola"],
        ["stopPlayer()", "C → asm", "ripristina i vettori dell'OS, silenzia, AUDCTL = 0"],
        ["play_k", "asm → C", "record per quadro (K)"],
        ["play_chips", "asm → C", "POKEY per cui è scritto lo stream: 1 o 2"],
        ["have_stereo", "asm → C", "$80 se il secondo POKEY risponde a $D210, altrimenti 0"],
        ["outbuf[16]", "asm → C", "i valori dell'ultimo record decodificato, per registro: i VU meter li leggono qui"],
        ["play_frames, play_left", "asm → C", "quadri nello stream, quadri ancora da suonare (per il tempo trascorso)"],
    ], [38, 26, 106], mono_cols=(0,), font=7.9, caption="Tabella 6.1 — Le funzioni e le variabili del player.")
    section(S, "La memoria")
    table(S, [
        ["Pagina zero", "Byte", "Uso"],
        ["sptr", "2", "puntatore al flusso compresso del registro che si sta decodificando"],
        ["wp, rp", "2 + 2", "puntatori di scrittura e di lettura nel buffer circolare (il byte basso è sempre 0)"],
        ["tmp, tmp2, tmp3", "3", "temporanei"],
        ["ri, reg", "2", "indice nell'elenco dei registri, registro in corso"],
    ], [38, 20, 112], mono_cols=(0,), font=7.9)
    table(S, [
        ["Variabili e buffer (BSS)", "Byte", "Uso"],
        ["ring", "8447", "16 buffer circolari da 512 valori + 255 byte per allinearli alla pagina"],
        ["start_lo/hi, st_lo/hi", "64", "inizio e puntatore corrente del flusso di ogni registro (16 + 16 + 16 + 16)"],
        ["fl, cnt, srcl, srch, rhi", "80", "registro di flag, valori rimasti nel match, posizione sorgente, pagina del buffer"],
        ["outbuf, reglist", "33", "i 16 valori del record; elenco dei registri che hanno un flusso (+ terminatore)"],
        ["altre", "16", "K, numero di POKEY, flag stereo, vettori salvati, contatori"],
    ], [50, 20, 100], mono_cols=(0,), font=7.9, align="LRL",
          caption="Tabella 6.2 — Circa 8,6 KB di RAM, quasi tutti buffer. Con un solo POKEY ne basterebbe la metà: oggi "
                  "i buffer sono sempre 16.")
    section(S, "La decodifica", need=80)
    P(S, "Per ogni record il player percorre l'elenco dei registri che hanno un flusso e ne decodifica <b>un valore</b>. "
         "I valori finiscono in <font face=\"Mono\">outbuf</font> e nel buffer circolare del registro; alla fine, tutti "
         "insieme, vanno ai registri POKEY. Scrivere tutto in una raffica fa cambiare nello stesso istante i canali e le "
         "due metà di una coppia a 16 bit.")
    code(S, excerpt("sp-common.asm", "; X = register.  Decode its next value", "jmp @copy"),
         title="sp-common.asm — decode: un valore di un registro (X = registro)", size=6.9)
    callout(S, "NOTA", "Il registro dei flag usa un <b>bit sentinella</b>: dopo aver letto il byte di flag, "
                       "<font face=\"Mono\">sec; rol a</font> mette il primo flag nel carry e un 1 in fondo. Ogni flag "
                       "successivo si legge con <font face=\"Mono\">asl</font>; quando il risultato è zero, "
                       "il byte è finito e se ne carica un altro. Non serve un contatore.")
    section(S, "Il vertical blank e il ciclo del brano")
    P(S, "Il player gira nel <b>vertical blank differito</b> (vettore 7 di <font face=\"Mono\">SETVBV</font>): il sistema "
         "operativo esegue prima il proprio lavoro (orologio, colori, tastiera) e poi chiama il nostro codice, che "
         "termina con un salto a <font face=\"Mono\">XITVBV</font>. All'inizio di ogni quadro si controlla il "
         "contatore dei quadri rimasti; a zero si azzerano i decodificatori e il brano ricomincia.")
    code(S, excerpt("sp-common.asm", "; Deferred VBI: first record of the frame.", "jmp XITVBV"),
         title="sp-common.asm — il VBI (vbim, per K > 1, abilita anche i DLI)", size=6.9)
    section(S, "Brani multispeed: i DLI", need=95)
    P(S, "Un brano a 2x, 3x o 4x chiama <font face=\"Mono\">play</font> più volte per quadro; l'Atari ha un solo VBI "
         "per quadro. Gli altri record si suonano da <b>interrupt di display list</b> (DLI), distribuiti a distanze uguali "
         "lungo il quadro. Il POKEY non è una soluzione: i suoi timer usano i divisori dei canali che servono per "
         "suonare.")
    flow(S, D.FrameTimeline(), "Figura 6.1 — Un quadro PAL (312 righe) dal VBI al successivo, per K da 1 a 4: il VBI suona il "
                               "primo record, i DLI (blu) gli altri; le linee tratteggiate sono le posizioni ideali.")
    P(S, "Il programma C cerca nella display list del sistema (così com'è: modo testo, 24 righe) le istruzioni la cui "
         "ultima scanline è più vicina ai punti che dividono il quadro in K parti uguali a partire dal VBI, e vi mette "
         "il bit di DLI. Alla fine le rimette a posto.")
    table(S, [
        ["Standard", "K", "DLI", "Punto ideale (riga)", "Istruzione scelta", "Scanline", "Errore"],
        ["PAL", "2", "1", "92", "riga di testo 7", "95", "3"],
        ["PAL", "3", "1", "40", "riga di testo 0", "39", "1"],
        ["PAL", "3", "2", "144", "riga di testo 13", "143", "1"],
        ["PAL", "4", "1", "14", "blank", "15", "1"],
        ["PAL", "4", "2", "92", "riga di testo 7", "95", "3"],
        ["PAL", "4", "3", "170", "riga di testo 16", "167", "3"],
        ["NTSC", "2", "1", "117", "riga di testo 10", "119", "2"],
        ["NTSC", "3", "1", "73", "riga di testo 4", "71", "2"],
        ["NTSC", "3", "2", "160", "riga di testo 15", "159", "1"],
        ["NTSC", "4", "1", "51", "riga di testo 1", "47", "4"],
        ["NTSC", "4", "2", "117", "riga di testo 10", "119", "2"],
        ["NTSC", "4", "3", "182", "riga di testo 18", "183", "1"],
    ], [20, 10, 12, 32, 42, 26, 28], align="LCCRLRR", font=7.8, keep=True,
          caption="Tabella 6.3 — Dove cadono i DLI nella display list standard. L'errore massimo è di 4 scanline "
                  "(circa 0,25 ms a 50 Hz): non si sente.")
    code(S, excerpt("sid2pokey.c", "static void patchDisplayList(", "dli_ins[dli_n++] = ins_p[best];") + "\n\t}\n}",
         title="sid2pokey.c — patchDisplayList(): sceglie le istruzioni a cui dare il DLI", size=6.8)
    callout(S, "TRAPPOLA", "<b>I DLI devono partire solo dopo il primo VBI.</b> I record di un quadro si suonano sempre nell'ordine "
                           "VBI, DLI, DLI, …: se i primi DLI scattano prima del primo VBI, lo stream si legge sempre "
                           "in ordine ma sfasato, e la fine dello stream non cade più a fine quadro: il player "
                           "legge byte che non sono dati. Per questo non si scrive NMIEN in "
                           "<font face=\"Mono\">startPlayer</font>: lo fa il VBI (<font face=\"Mono\">vbim</font>) a ogni "
                           "quadro. Inoltre <font face=\"Mono\">SETVBV</font> rimette NMIEN a $40 e spegnerebbe i DLI "
                           "appena abilitati.")
    sub(S, "L'NMI diretto sull'XL/XE")
    P(S, "Sul target XL/XE cc65 tiene la ROM dell'OS spenta e la riaccende, con un wrapper, per ogni interrupt. Un DLI "
         "passerebbe da lì e la ROM resterebbe accesa per tutto il gestore: l'ANTIC leggerebbe il font dalla ROM al "
         "posto di quello in RAM per decine di scanline (capitolo 7, \u00abLe trappole dello schermo\u00bb). Il player sostituisce allora il vettore NMI in RAM "
         "($FFFA) con un gestore proprio, che riconosce il DLI dal bit 7 di NMIST e lo serve senza toccare la ROM; "
         "il VBI passa al vettore originale.")
    code(S, excerpt("sp-common.asm", "nmi_dli:", "@other:") + "\n\tjmp (old_nmi)",
         title="sp-common.asm — nmi_dli: il DLI servito direttamente dal vettore NMI (solo atarixl)", size=6.9)
    section(S, "Due POKEY", need=90)
    P(S, "Con due POKEY i registri sono 16: i primi otto vanno a $D200, gli altri a $D210. La funzione "
         "<font face=\"Mono\">putreg</font> li instrada e scrive il secondo POKEY solo se <font face=\"Mono\">have_stereo</font> "
         "lo ha confermato.")
    callout(S, "TRAPPOLA", "Senza la scheda stereo, $D210-$D21F sono uno <b>specchio</b> del primo POKEY: scrivere il registro 8 "
                           "(AUDF1 del POKEY 2) sovrascrive AUDF1 del POKEY 1 e, scrivendo AUDCTL 2 a $D218, anche "
                           "l'AUDCTL del primo. Su un Atari normale un brano a due SID suonerebbe in modo scorretto, non "
                           "soltanto con un chip in meno.")
    P(S, "Il rilevamento sfrutta il registro RANDOM ($D20A, $D21A). Il player mette il POKEY 2 in funzionamento "
         "(<font face=\"Mono\">SKCTL = 3</font>) e <i>poi</i> il POKEY 1 in stato di inizializzazione "
         "(<font face=\"Mono\">SKCTL = 0</font>, i contatori polinomiali sono fermi e RANDOM legge $FF), quindi legge "
         "256 volte RANDOM2:")
    table(S, [
        ["Situazione", "Cosa legge a $D21A", "Esito"],
        ["scheda stereo vera", "valori che cambiano (il POKEY 2 gira)", "secondo POKEY presente"],
        ["Atari senza scheda", "sempre $FF: è lo specchio del POKEY 1, in inizializzazione", "assente: si suona solo SID 1"],
        ["atari800 con <font face=\"Mono\">-stereo</font>", "sempre $00: l'emulatore suona il secondo POKEY ma non ne implementa RANDOM",
         "presente (costante diversa da $FF)"],
    ], [42, 82, 46], font=7.9, caption="Tabella 6.4 — I tre casi che il rilevamento distingue.")
    code(S, excerpt("sp-common.asm", "detect_stereo:", "silence:", include_end=False).rstrip(),
         title="sp-common.asm — detect_stereo e putreg", size=6.9)
    callout(S, "ATTENZIONE", "Il caso «costante diversa da $FF» è un'euristica pensata per atari800: sull'hardware "
                             "reale non ho potuto provarla. Su una scheda vera RANDOM varia e il rilevamento è quello "
                             "ortodosso.")
    section(S, "I due target di cc65", need=80)
    table(S, [
        ["", "400/800 (<font face=\"Mono\">-t atari</font>)", "XL/XE (<font face=\"Mono\">-t atarixl</font>)"],
        ["ROM dell'OS durante il programma", "sempre accesa", "spenta; riaccesa dai wrapper per interrupt e chiamate all'OS"],
        ["SETVBV", "<font face=\"Mono\">$E45C</font> diretto", "un wrapper (da <font face=\"Mono\">atari.inc</font>): mai chiamare $E45C"],
        ["Il font", "in RAM, in un blocco riservato; CHBAS lo indica", "il font di ROM è già copiato a $E000: si modifica sul posto"],
        ["DLI", "dal vettore dell'OS (VDSLST)", "dal vettore NMI in RAM, senza accendere la ROM"],
        ["Memoria", "circa 20 KB di stream", "circa 24 KB di stream"],
        ["Define di compilazione", "<font face=\"Mono\">-DFONT_TOP</font> e memoria riservata", "(<font face=\"Mono\">__ATARIXL__</font>, definito dal target)"],
    ], [42, 62, 66], font=7.8, caption="Tabella 6.5 — Le differenze tra i due target.")
    callout(S, "TRAPPOLA", "Non chiamare <font face=\"Mono\">$E45C</font> direttamente sul target atarixl: la ROM è spenta e "
                           "lì c'è RAM. Il programma si pianta subito (era successo al primo tentativo: l'emulatore usciva dopo "
                           "due secondi e mezzo). Si usa il simbolo <font face=\"Mono\">SETVBV</font> di "
                           "<font face=\"Mono\">atari.inc</font>, che su atarixl è il wrapper.")
