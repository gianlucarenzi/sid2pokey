# ch_psid_conv.py - chapters 3 (PSID) and 4 (sidconv)
import os
import textwrap

import diagrams as D
from pdflib import (HERE, bullets, callout, chapter, code, excerpt, figure, flow, m, numbered, P, section, sub,
                    table, read_text)

MONO = 'face="Mono"'


def mm_(s):
    return '<font face="Mono">%s</font>' % s


def verbose_example(name, only=None):
    """a saved 'sidconv -v' output, with the long lines wrapped"""
    out = []
    for l in open(os.path.join(HERE, "examples", name)).read().rstrip().split("\n"):
        l = l.replace("doc/examples/commando.bin", "song.bin").replace("doc/examples/double.bin", "song.bin")
        if only and not any(l.startswith(k) or k in l for k in only):
            continue
        out.extend(textwrap.wrap(l, 100, subsequent_indent="    ", drop_whitespace=False) or [""])
    return "\n".join(out)


def build(S):
    ch3(S)
    ch4(S)


def ch3(S):
    chapter(S, "Il formato PSID e i brani della HVSC")
    section(S, "L'header")
    P(S, "Un file PSID è un header seguito dai dati. L'header ha 118 byte nella versione 1 e 124 dalla versione 2; "
         "il campo <i>dataOffset</i> dice dove cominciano i dati. Tutti i numeri sono in ordine big endian, al "
         "contrario del 6502. La tabella riporta i campi e quali il convertitore usa.")
    table(S, [
        ["Offset", "Byte", "Campo", "Uso in sidconv"],
        ["$00", "4", "«PSID» o «RSID»", "RSID: avviso (è pensato per un C64 completo), ma si prova lo stesso"],
        ["$04", "2", "versione (1-4)", "decide se esistono i campi di v2/v3/v4"],
        ["$06", "2", "dataOffset ($76 o $7C)", "inizio dei dati"],
        ["$08", "2", "loadAddress", "0 = i primi due byte dei dati (little endian) sono l'indirizzo"],
        ["$0A", "2", "initAddress", "0 = brano pilotato da BASIC: non supportato"],
        ["$0C", "2", "playAddress", "0 = il brano installa un proprio IRQ (par. 4.3)"],
        ["$0E", "2", "songs", "numero di brani nel file"],
        ["$10", "2", "startSong", "brano predefinito (opzione <font face=\"Mono\">-s</font>)"],
        ["$12", "4", "speed", "un bit per brano: 0 = VBI, 1 = timer CIA (par. 4.4)"],
        ["$16", "32", "titolo", "mostrato nella schermata"],
        ["$36", "32", "autore", "mostrato nella schermata"],
        ["$56", "32", "copyright («released»)", "mostrato nella schermata"],
        ["$76", "2", "flags (v2+)", "bit 2-3: clock (01 PAL, 10 NTSC, 11 entrambi); gli altri non servono"],
        ["$7A", "1", "secondo SID (v3)", "indirizzo = $D000 + valore × 16 (par. 3.3)"],
        ["$7B", "1", "terzo SID (v4)", "come sopra; il terzo SID è ignorato"],
    ], [14, 11, 50, 95], mono_cols=(0,), caption="Tabella 3.1 — I campi dell'header PSID.", font=7.8)
    callout(S, "NOTA", "Le stringhe dell'header sono ASCII o Latin-1, lunghe al più 32 caratteri e riempite di zeri. "
                       "Il convertitore le copia nello stream (96 byte) e la schermata le disegna: i caratteri fuori "
                       "dall'intervallo $20-$7A diventano un punto interrogativo.")
    section(S, "La frequenza di play")
    P(S, "Il bit di <i>speed</i> del brano scelto dice solo se il codice è chiamato dal quadro video "
         "(bit 0) o da un timer (bit 1); la frequenza vera la sceglie il brano stesso, programmando il timer A della "
         "CIA 1 (registri $DC04/$DC05) o l'interrupt di raster del VIC. Per questo il convertitore non si fida del solo "
         "bit: esegue <font face=\"Mono\">init</font> e poi guarda cosa ha programmato (tabella 4.2). I brani "
         "<b>multispeed</b> sono quelli con una frequenza di play multipla del quadro: 100, 150, 200 Hz.")
    section(S, "Due e tre SID")
    P(S, "La versione 3 dell'header aggiunge l'indirizzo di un secondo SID, la 4 quello di un terzo. L'indirizzo è "
         "un byte, in unità di 16 byte sopra $D000: sono validi $42-$7E (pari) e $E0-$FE (pari), cioè "
         "$D420-$D7E0 e $DE00-$DFE0. Con più chip, ognuno risponde solo ai suoi 32 byte; con un solo SID il chip "
         "risponde a tutto $D400-$D7FF (specchiato ogni 32 byte), com'è sul C64.")
    table(S, [
        ["Nella HVSC (56 665 file)", "File", "Note"],
        ["header versione 2", "56 401", "un solo SID"],
        ["header versione 3", "240", "fino a due SID"],
        ["header versione 4", "24", "fino a tre SID: tutti con tre SID"],
        ["con un secondo SID", "264", "$D420: 159, $D500: 85, $DE00: 14, $D440: 3, $D4A0, $D520, $D5A0: uno ciascuno"],
        ["con un terzo SID", "24", "convertiti usando solo i primi due"],
    ], [52, 22, 96], caption="Tabella 3.2 — I brani a più SID della raccolta usata per le prove.")
    callout(S, "ATTENZIONE", "Nove voci (tre SID) non entrano negli otto canali di due POKEY. Il convertitore usa i "
                             "primi due SID e lo scrive: <font face=\"Mono\">warning: the tune has 3 SIDs; only the first "
                             "two are converted</font>.")
    section(S, "Brani che non si possono convertire")
    P(S, "Su un campione di 4370 brani della HVSC (un file ogni dodici della cartella <font face=\"Mono\">MUSICIANS</font>) "
         "se ne convertono 4292, il 98,2 %. Gli altri 78 si dividono così; ogni rifiuto è accompagnato da un messaggio "
         "che dice perché.")
    table(S, [
        ["Motivo", "Brani", "Perché non si può"],
        ["guidati da un gestore NMI", "28", "di solito riproducono campioni digitali con il timer della CIA 2 e l'NMI"],
        ["il loop principale fa il lavoro", "26", "<font face=\"Mono\">play</font> = 0 senza un IRQ: servirebbe un C64 intero"],
        ["BASIC (init = 0)", "19", "partono da un programma BASIC"],
        ["chiamano il KERNAL", "2", "il KERNAL emulato contiene solo le uscite dall'interrupt"],
        ["non ritornano", "2", "la routine non finisce entro 2 milioni di istruzioni"],
        ["JAM", "1", "l'opcode che blocca la CPU"],
    ], [52, 18, 100], caption="Tabella 3.3 — I 78 brani rifiutati su 4370. Altri brani si convertono ma restano muti "
                              "(in genere campioni digitali): il convertitore lo avverte.")


def ch4(S):
    chapter(S, "Il convertitore sidconv")
    P(S, "<font face=\"Mono\">tools/sidconv.c</font> è un programma C da circa 1300 righe più "
         "<font face=\"Mono\">tools/cpu6502.h</font>, il core 6502. Prende un file SID e scrive uno stream "
         "(<font face=\"Mono\">song.bin</font>) che il player legge. Le sezioni che seguono ripercorrono le "
         "quattro fasi della figura 1.1.")
    section(S, "L'emulatore 6502")
    P(S, "Il core esegue un'istruzione alla volta senza contare i cicli: serve solo a far girare "
         "<font face=\"Mono\">init</font> e <font face=\"Mono\">play</font> e a osservare cosa scrivono nel SID. "
         "Ha due limiti di sicurezza (50 milioni di istruzioni per <font face=\"Mono\">init</font>, 2 milioni per "
         "<font face=\"Mono\">play</font>) per non restare bloccato in un loop.")
    table(S, [
        ["Gruppo", "Opcode", "Note"],
        ["ufficiali", "151", "ADC e SBC anche in modo decimale; JMP indiretto con il bug del cambio di pagina"],
        ["non documentati stabili", "84", "LAX, SAX, SLO, RLA, SRE, RRA, DCP, ISC, ANC, ALR, SBX, SBC $EB, NOP a 2 e 3 byte"],
        ["non documentati instabili", "9", "ARR, XAA, LXA, AHX (2 forme), TAS, SHX, SHY, LAS: modello di VICE"],
        ["JAM", "12", "non implementati: la CPU vera si blocca, il convertitore si ferma con un messaggio"],
    ], [42, 18, 110], caption="Tabella 4.1 — Gli opcode del core (256 in tutto).")
    callout(S, "VERIFICATO", "Il test <font face=\"Mono\">tests/opcodes</font> costruisce un programma C64 con 588 casi "
                             "degli opcode instabili (registri, flag, stack pointer, comportamento al cambio di pagina, "
                             "ARR anche in decimale), lo esegue nel core e in VICE x64sc 3.10 e confronta ogni "
                             "risultato: tutti identici. Le costanti «magiche» sono quelle di VICE: "
                             "XAA usa $EF, LXA usa $EE. Sui chip veri variano.")
    callout(S, "NOTA", "Il core gira solo sul PC. Il codice che gira sull'Atari usa solo istruzioni documentate del "
                       "6502 (<font face=\"Mono\">cl65</font> compila per <font face=\"Mono\">--cpu 6502</font>) ed "
                       "è uguale sul 400/800 e sull'XL/XE: sono tutti 6502C, e gli XL/XE non hanno opcode in più "
                       "(quelli sono del 65C02/65816 delle schede acceleratrici).")

    section(S, "Un C64 minimo attorno al core", need=88)
    P(S, "Il brano si aspetta un C64: la memoria, un po' di I/O, i vettori del KERNAL. Il convertitore ne "
         "emula lo stretto necessario.")
    table(S, [
        ["Elemento", "Come è emulato"],
        ["memoria", "64 KB piatti, azzerati; il brano è caricato all'indirizzo dichiarato"],
        ["porta CPU ($01)", "valore iniziale dato dall'indirizzo di init: &lt; $A000 → $37; &lt; $D000 → $36; "
                            "≥ $E000 → $35; altrimenti $34. Il bit 1 (HIRAM) decide se il KERNAL è visibile"],
        ["KERNAL", "una ROM minima a $E000-$FFFF, visibile sopra la RAM del brano quando HIRAM = 1"],
        ["uscite dall'IRQ", "$EA31 e $EA34 → $EA81; $EA7B → $EA7E (legge $DC0D); $EA81: PLA TAY PLA TAX PLA RTI; $EA87: RTS"],
        ["ogni altro byte del KERNAL", "l'opcode illegale $02: se il brano lo esegue, il messaggio dice <i>chiama il KERNAL a $xxxx, non emulato</i>"],
        ["vettori", "$0314 = $EA31 (IRQ), $0316 = $FE66 (BRK), $0318 = $FE47 (NMI); in ROM NMI $FE43, RESET $FCE2, IRQ $FF48"],
        ["SID", "le scritture a $D400-$D418 sono registrate; $D41B restituisce un valore pseudocasuale, $D41C zero"],
        ["VIC", "$D012 aumenta di 7 a ogni lettura (così le attese di raster finiscono); $D019 = $81 se l'IRQ di raster è abilitato"],
        ["CIA 1", "il latch del timer A ($DC04/05) e la maschera ($DC0D) sono registrati; $DC00/01 = $FF (nessun tasto)"],
    ], [38, 132], font=7.8, caption="Tabella 4.2 — L'ambiente C64 emulato.")
    sub(S, "Brani con un proprio gestore IRQ (play = 0)")
    P(S, "Se l'indirizzo di play è zero, dopo <font face=\"Mono\">init</font> il brano ha installato un gestore: nel "
         "vettore $0314 se il KERNAL è visibile, in $FFFE se la RAM copre la ROM. Il convertitore lo chiama una volta per "
         "quadro, come lo chiamerebbe un C64: mette sullo stack l'indirizzo di ritorno e il registro di stato e, con il "
         "KERNAL visibile, anche A, X e Y, come fa lo stub a $FF48. Se <font face=\"Mono\">init</font> non ritorna ma ha "
         "installato un gestore, si assume che il programma sia fermo in un loop principale e si continua con il "
         "solo gestore.")
    section(S, "La temporizzazione")
    table(S, [
        ["Condizione", "Frequenza di play"],
        ["play ≠ 0, bit speed = 0 (VBI)", "50,125 Hz (PAL) o 59,826 Hz (NTSC)"],
        ["play ≠ 0, bit speed = 1, timer programmato da init", "clock SID / (latch + 1)"],
        ["play ≠ 0, bit speed = 1, timer non programmato", "60 Hz"],
        ["play = 0, IRQ del timer A della CIA 1 abilitato", "clock SID / (latch + 1)"],
        ["play = 0, IRQ di raster abilitato", "come il VBI"],
    ], [92, 78], caption="Tabella 4.3 — Come si ricava la frequenza con cui il brano va chiamato.")
    P(S, "Il convertitore chiama <font face=\"Mono\">play</font> a quella frequenza per il tempo richiesto e poi "
         "<b>ricampiona nel tempo reale</b> sui quadri dell'Atari: per il record <i>j</i> del quadro <i>n</i> usa la "
         "chiamata numero <font face=\"Mono\">floor(((n + j/K) / f_atari) × f_play)</font>. In questo modo il tempo "
         "del brano non cambia con lo standard video. <b>K</b> è il rapporto arrotondato, limitato a 1-4: un brano a 2x "
         "ha due record per quadro; oltre 4x alcune chiamate si perdono.")
    section(S, "Il modello delle voci")
    P(S, "Dopo ogni chiamata il convertitore legge i registri del SID e calcola, per ogni voce, tre cose.")
    bullets(S, [
        "<b>La frequenza</b>: Fn × clock / 2<super>24</super>. Un Fn nullo, il bit di test o una forma d'onda "
        "assente rendono la voce muta.",
        "<b>La forma d'onda</b>: rumore (bit 7) oppure «altro»; sul POKEY l'altro diventa onda quadra.",
        "<b>Il volume</b>: il livello dell'inviluppo (0-255) per il volume generale (0-15), ridotto a 4 bit con "
        "<font face=\"Mono\">(livello × volume + 127) / 255</font>.",
    ])
    sub(S, "L'inviluppo come lo fa il chip")
    P(S, "Il generatore di inviluppo del SID ha un contatore a 8 bit e un contatore di velocità che avanza a ogni ciclo "
         "di clock. Quando il contatore di velocità raggiunge il periodo dello stato (attacco, decadimento o rilascio) "
         "l'inviluppo può fare un passo. In attacco sale di uno a ogni scatto (rampa lineare); in decadimento e "
         "rilascio scende di uno ogni <i>p</i> scatti, dove <i>p</i> cresce al diminuire del livello. È questo che "
         "dà il decadimento rapido seguito da una lunga coda dei suoni SID.")
    table(S, [
        ["Il livello scende sotto", "255", "93", "54", "26", "14", "6"],
        ["il passo avviene ogni (scatti)", "1", "2", "4", "8", "16", "30"],
    ], [52, 20, 20, 20, 20, 20, 18], align="LCCCCCC", caption="Tabella 4.4 — Il contatore esponenziale.")
    rates = [(9, 2.3, 2, 7.0, 6), (32, 8.3, 8, 24.6, 24), (63, 16.3, 16, 48.4, 48), (95, 24.7, 24, 73.0, 72),
             (149, 38.6, 38, 114.4, 114), (220, 56.9, 56, 168.9, 168), (267, 69.1, 68, 204.9, 204),
             (313, 81.1, 80, 240.2, 240), (392, 101.5, 100, 300.8, 300), (977, 252.9, 250, 749.8, 750),
             (1954, 505.8, 500, 1499.4, 1500), (3126, 809.1, 800, 2398.7, 2400), (3907, 1011.2, 1000, 2997.9, 3000),
             (11720, 3033.3, 3000, 8993.1, 9000), (19532, 5055.3, 5000, 14987.3, 15000),
             (31251, 8088.4, 8000, 23979.5, 24000)]

    def fmt(v):
        return ("%.1f" % v).replace(".", ",") if v < 1000 else ("%.0f" % v)
    rows = [["Indice", "Periodo (cicli)", "Attacco 0→255: modello", "scheda", "Rilascio 255→ 0: modello", "scheda"]]
    for i, (per, a, ad, r, rd) in enumerate(rates):
        rows.append([str(i), str(per), fmt(a) + " ms", str(ad) + " ms", fmt(r) + " ms", str(rd) + " ms"])
    table(S, rows, [16, 28, 38, 22, 44, 22], align="CRRRRR", font=7.6, keep=False,
          caption="Tabella 4.5 — I sedici ritmi dell'inviluppo: tempi del modello e valori della scheda tecnica del SID.")
    callout(S, "VERIFICATO", "Il modello è stato confrontato con i tempi della scheda tecnica per tutti e sedici i "
                             "ritmi: attacco e rilascio sono entro il 4 % (entro il 2 % dal ritmo 4 in su). Il "
                             "ritmo 0 dà 2,3 ms contro i 2 ms della scheda perché la scheda arrotonda: "
                             "255 × 9 cicli sono 2,33 ms. A ritmo 9 il livello arriva a metà dopo 126 ms su 750 "
                             "(il 17 % del tempo: una rampa lineare ne userebbe il 50 %).")
    callout(S, "ATTENZIONE", "Il difetto del chip noto come <i>ADSR delay bug</i> (un contatore di velocità oltre il "
                             "nuovo periodo deve prima riavvolgersi, con un ritardo fino a 32 ms) non è modellato.")
    code(S, excerpt("tools/sidconv.c", "static void voice_step(", "env_step(e, s * 17);") + "\n\t\t}\n\t}\n}",
         title="tools/sidconv.c — il passo dell'inviluppo per una chiamata di play")
    section(S, "La mappatura su POKEY", need=60)
    sub(S, "La frequenza: il divisore più vicino")
    P(S, "Per una voce a frequenza <i>f</i> e un canale con clock <i>clk</i> il divisore è "
         "<i>N + d = clk / (2 f)</i>, con d = 1 per i canali a 8 bit e d = 7 per la coppia a 16 bit a 1,79 MHz. Si "
         "arrotonda, si limita a 0-255 (o 0-65535) e si calcola l'errore in centesimi di tono. Se la nota è troppo "
         "bassa per il divisore, la frequenza si <b>raddoppia</b> fino a che ci sta: la nota suona alcune ottave sopra, e "
         "nel costo conta 1200 centesimi per ottava.")
    code(S, excerpt("tools/sidconv.c", "static quant_t quantize(", "return q;") + "\n}",
         title="tools/sidconv.c — quantize(): il divisore e l'errore")
    callout(S, "NOTA", "Per il <b>rumore</b> il divisore usa 8 volte la frequenza: il registro a scorrimento del SID avanza a "
                       "16 volte la frequenza della nota, mentre il polinomio del POKEY avanza una volta per periodo del "
                       "divisore, cioè a due volte la frequenza dell'onda quadra equivalente.")
    sub(S, "Le disposizioni dei canali")
    P(S, "Le tre voci di un SID possono stare sui quattro canali di un POKEY in molti modi. Il convertitore ne prova "
         "otto e tiene quella con l'errore medio minore, pesato per il volume (il rumore non conta: non ha un'altezza).")
    flow(S, D.Layouts(), "Figura 4.1 — Due delle disposizioni: tre canali a 8 bit, oppure una voce sulla coppia a 16 bit.")
    table(S, [
        ["#", "Disposizione", "AUDCTL", "Canali"],
        ["1", "3 canali a 8 bit, clock 64 kHz", "$00", "voce 1→1, 2→2, 3→3; il 4 è libero"],
        ["2", "3 canali a 8 bit, clock 15 kHz", "$01", "come sopra"],
        ["3-4", "voce 1 sulla coppia a 16 bit; le altre a 64 kHz (3) o 15 kHz (4)", "$50 / $51", "voce 1 → 1+2; voce 2 → 3; voce 3 → 4"],
        ["5-6", "voce 2 sulla coppia a 16 bit", "$50 / $51", "voce 2 → 1+2; voce 1 → 3; voce 3 → 4"],
        ["7-8", "voce 3 sulla coppia a 16 bit", "$50 / $51", "voce 3 → 1+2; voce 1 → 3; voce 2 → 4"],
    ], [12, 78, 22, 58], mono_cols=(2,), caption="Tabella 4.6 — Le otto disposizioni candidate (opzione <font face=\"Mono\">-m</font> per limitarle).")
    P(S, "Con la coppia a 16 bit il canale 1 resta muto (AUDC1 = 0) e il divisore usa AUDF1 come parte bassa e AUDF2 come "
         "parte alta; il volume e la distorsione stanno in AUDC2. Con i bit 6 e 4 di AUDCTL il clock è 1,79 MHz; il "
         "bit 0 sceglie 15 kHz per i canali a 8 bit.")
    code(S, verbose_example("commando_verbose.txt"),
         title="Esempio: sidconv -v su Commando di Rob Hubbard (errore medio di ogni disposizione, in centesimi)",
         size=6.9)
    callout(S, "NOTA", "Con tre canali a 64 kHz l'errore medio è di 726 centesimi: i bassi, sotto i 124 Hz, "
                       "sono ripiegati di ottave. La disposizione scelta (voce 1 sulla coppia a 16 bit, le altre a "
                       "15 kHz) lo porta a 9 centesimi.")
    section(S, "Due SID, due POKEY")
    P(S, "Con un secondo SID il convertitore ripete la scelta per ciascun chip: <b>SID 1 va sul POKEY 1</b> (registri 0-7) "
         "e <b>SID 2 sul POKEY 2</b> (registri 8-15), ognuno con il proprio layout e il proprio AUDCTL. Uno può usare "
         "la coppia a 16 bit e l'altro tre canali. L'opzione <font face=\"Mono\">-S 1</font> converte solo il primo.")
    code(S, verbose_example("double_verbose.txt", only=("PSID", "using", "frames")),
         title="Esempio: un brano a due SID (Double, JVD e Udo Gorissen)", size=6.9)
    section(S, "Le opzioni e i messaggi", need=100)
    table(S, [
        ["Opzione", "Significato", "Predefinito"],
        ["-o file", "stream di uscita", "song.bin"],
        ["-s n", "brano del file (da 1)", "quello iniziale del file"],
        ["-t secondi", "durata da convertire (un SID non ha una lunghezza)", "60"],
        ["-p pal|ntsc", "standard video dell'Atari di destinazione", "pal"],
        ["-c pal|ntsc|auto", "clock per cui il brano è scritto", "auto (dai flag; altrimenti PAL)"],
        ["-m auto|plain|bass16", "disposizione dei canali: tutte, solo a 3 canali, solo con coppia a 16 bit", "auto"],
        ["-k n", "record per quadro, da 1 a 4", "dal ritmo del brano"],
        ["-S n", "chip SID da convertire, 1 o 2", "tutti (al massimo 2)"],
        ["-d", "stampa i registri POKEY di ogni record (hex) su stdout", ""],
        ["-v", "stampa titolo, indirizzi, frequenza, errori delle disposizioni", ""],
    ], [40, 94, 36], mono_cols=(0,), font=7.8, caption="Tabella 4.7 — La riga di comando di sidconv.")
    table(S, [
        ["Messaggio", "Significato"],
        ["warning: RSID files expect a real C64 environment", "si prova lo stesso, ma può fallire"],
        ["init address is 0: C64 BASIC tune, not supported", "il brano parte da un programma BASIC"],
        ["play address is 0 and the tune is driven by an NMI handler", "player di campioni digitali: non supportato"],
        ["play address is 0 but init did not install an IRQ handler", "il loop principale fa tutto: non supportato"],
        ["the tune calls the KERNAL at $xxxx, which is not emulated", "usa una routine del KERNAL diversa dalle uscite dall'IRQ"],
        ["JAM opcode $xx at $xxxx", "la CPU vera si bloccherebbe qui"],
        ["routine at $xxxx did not return", "oltre il limite di istruzioni (probabile loop infinito)"],
        ["warning: the tune has 3 SIDs; only the first two are converted", "nove voci non entrano in otto canali"],
        ["warning: the converted tune is silent", "nessun suono: se c'è un NMI, probabilmente campioni digitali"],
        ["warning: stream larger than 20 KB", "non entra in un 400/800 (un XL/XE regge circa 24 KB)"],
        ["internal error: stream verification failed", "bug del convertitore: lo stream riletto non coincide"],
    ], [86, 84], font=7.6, caption="Tabella 4.8 — I messaggi principali.")
