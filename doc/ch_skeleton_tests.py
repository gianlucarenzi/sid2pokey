# ch_skeleton_tests.py - chapters 8 (the skeleton), 9 (verification), 10 (traps)
from pdflib import (bullets, callout, chapter, code, excerpt, figure, flow, numbered, P, read_text, section, sub,
                    table)


def build(S):
    ch8(S)
    ch9(S)
    ch10(S)


def ch8(S):
    chapter(S, "Lo skeleton: il player più piccolo")
    P(S, "Prima di leggere il player completo conviene costruire e far girare il più piccolo possibile. La cartella "
         "<font face=\"Mono\">skeleton/</font> contiene un player che usa solo un POKEY, un record per quadro e uno stream "
         "senza compressione: ci sono tutti gli ingredienti (il convertitore, un formato, un'interruzione che scrive i "
         "registri, un programma C che la installa) e nient'altro. Si legge in dieci minuti e si può far crescere "
         "un passo alla volta (par. 8.8).")
    section(S, "Cosa c'è e cosa non c'è")
    table(S, [
        ["File", "Righe", "Ruolo"],
        ["player.s", "~110", "la routine del vertical blank: legge lo stream e scrive AUDF1…AUDC4"],
        ["data.s", "8", "incorpora lo stream nel binario (<font face=\"Mono\">.incbin</font>)"],
        ["main.c", "~22", "avvia il player, aspetta un tasto, lo ferma"],
        ["dump2raw.py", "~33", "trasforma l'uscita di <font face=\"Mono\">sidconv -d</font> nello stream dello skeleton"],
        ["Makefile", "20", "converte, costruisce <font face=\"Mono\">player.com</font>"],
    ], [34, 18, 118], mono_cols=(0,), caption="Tabella 8.1 — I cinque file dello skeleton.")
    table(S, [
        ["Lo skeleton ha", "Non ha (vedi il progetto completo)"],
        ["un POKEY, tre canali (<font face=\"Mono\">-m plain</font>)", "coppie a 16 bit, secondo POKEY (capitoli 4 e 6)"],
        ["un record per quadro (<font face=\"Mono\">-k 1</font>)", "brani multispeed e DLI (capitolo 6)"],
        ["stream a maschera + valori modificati, senza compressione", "flussi LZ per registro (capitolo 5)"],
        ["una riga di testo", "font C64, VU meter, titolo e autore (capitolo 7)"],
        ["istruzioni 6502 documentate; gira su 400/800 e XL/XE", "gestione dei due target, rilevamento stereo"],
    ], [85, 85], font=7.9, caption="Tabella 8.2 — La portata dello skeleton.")
    section(S, "Passo 1: gli strumenti")
    P(S, "Servono cc65 e un compilatore C. Il convertitore si costruisce dalla radice del progetto; dallo skeleton basta "
         "<font face=\"Mono\">make</font>, che lo fa da sé.")
    code(S, "cd skeleton\ncl65 --version            # cc65 2.19 o simile\nmake -C .. tools/sidconv  # il convertitore (gcc)",
         title="Passo 1")
    section(S, "Passo 2: convertire un brano")
    P(S, "<font face=\"Mono\">sidconv</font> con l'opzione <font face=\"Mono\">-d</font> stampa i registri POKEY di ogni "
         "record, in esadecimale. Per lo skeleton si chiede un solo chip (<font face=\"Mono\">-S 1</font>), disposizione "
         "semplice (<font face=\"Mono\">-m plain</font>) e un record per quadro (<font face=\"Mono\">-k 1</font>, i brani "
         "multispeed vengono ridotti).")
    code(S, "../tools/sidconv -m plain -S 1 -k 1 -t 60 -d -o song.bin tune.sid > dump.txt", title="Passo 2")
    code(S, open(__import__("os").path.join(__import__("pdflib").HERE, "examples", "dump_excerpt.txt")).read().rstrip(),
         title="Un estratto di dump.txt (Commando): numero del quadro, poi AUDF1 AUDC1 AUDF2 AUDC2 AUDF3 AUDC3 AUDF4 AUDC4")
    P(S, "Ogni riga è lo stato dei registri in quell'istante. I valori di AUDC hanno la distorsione nel nibble "
         "alto ($A = onda quadra) e il volume nel basso. <font face=\"Mono\">song.bin</font> è lo stream "
         "del progetto completo: lo skeleton ne usa solo il primo byte, l'AUDCTL scelto dal convertitore.")
    section(S, "Passo 3: dal dump allo stream dello skeleton")
    P(S, "Lo stream dello skeleton è il più semplice che abbia senso: per ogni quadro un byte di <b>maschera</b> e "
         "i valori dei registri che sono cambiati.")
    table(S, [
        ["Posizione", "Contenuto"],
        ["byte 0", "AUDCTL"],
        ["byte 1-2", "numero di quadri (16 bit, little endian)"],
        ["poi, per ogni quadro", "un byte di maschera; il bit <i>n</i> a 1 vuol dire che il registro $D200 + <i>n</i> cambia "
                                 "e il suo nuovo valore è uno dei byte che seguono, in ordine"],
    ], [38, 132], caption="Tabella 8.3 — Il formato dello skeleton. Il primo quadro scrive sempre tutti i registri.")
    code(S, read_text("skeleton/dump2raw.py").rstrip(), title="skeleton/dump2raw.py", size=7)
    section(S, "Passo 4: il player")
    P(S, "Il player è una sola routine, <font face=\"Mono\">vbi</font>, chiamata dal vertical blank differito. Le "
         "funzioni <font face=\"Mono\">playerInit</font>, <font face=\"Mono\">playerStart</font> e "
         "<font face=\"Mono\">playerStop</font> sono quelle che il programma C chiama.")
    code(S, read_text("skeleton/player.s").rstrip(), title="skeleton/player.s", size=6.9)
    sub(S, "I punti da capire")
    numbered(S, [
        "<b>SETVBV</b> ($E45C) installa una routine: il registro A dice quale vettore (6 = immediato, 7 = differito), "
        "X:Y l'indirizzo. Il differito gira dopo il lavoro dell'OS e deve finire con <b>XITVBV</b>.",
        "Il contatore <font face=\"Mono\">left</font> conta i quadri rimasti; a zero si torna all'inizio "
        "(<font face=\"Mono\">rewind</font>): il brano è un ciclo.",
        "La maschera si consuma con <font face=\"Mono\">lsr</font>: il bit 0 va nel carry, e se è a 1 si legge un byte "
        "e lo si scrive in <font face=\"Mono\">AUDF1 + X</font>.",
        "<font face=\"Mono\">silence</font> mette a zero gli otto registri e AUDCTL: serve all'inizio e alla fine.",
        "L'indirizzo dei registri ($D200) è l'unica cosa hardware: il resto è un lettore di stream.",
    ])
    section(S, "Passo 5: il programma C e il Makefile", need=95)
    code(S, read_text("skeleton/main.c").rstrip(), title="skeleton/main.c", size=7)
    code(S, read_text("skeleton/data.s").rstrip() + "\n", title="skeleton/data.s", size=7)
    code(S, read_text("skeleton/Makefile").rstrip(), title="skeleton/Makefile", size=7)
    section(S, "Passo 6: costruire e far girare", need=70)
    code(S, "make SID=~/Music/C64Music/MUSICIANS/H/Hubbard_Rob/Commando.sid DURATION=20\n"
            "atari800 -atari -osb_rom ~/ATARI/ATARIOSB.ROM -run player.com   # 400/800\n"
            "atari800 -xe -xlxe_rom ~/ATARI/ATARIXL.ROM -run player.com      # XL/XE (anche questo binario)",
         title="Passo 6")
    figure(S, "skeleton_screen.png", "Figura 8.1 — Lo skeleton in esecuzione: una riga di testo, la musica va da sola.",
           width_mm=112)
    table(S, [
        ["Misura", "Valore"],
        ["player.com (codice + libreria cc65 + stream)", "7174 byte"],
        ["stream di 20 s di Commando, senza compressione", "3982 byte (circa 200 byte al secondo)"],
        ["lo stesso con il formato LZ del progetto completo", "676 byte (5,9 volte meno)"],
    ], [92, 78], caption="Tabella 8.4 — Cosa ci si guadagna passando al formato compresso.")
    callout(S, "VERIFICATO", "Lo skeleton è stato fatto girare su atari800, sia come 400/800 che come XL/XE, "
                             "registrando i registri POKEY a ogni quadro: 475 su 475 (400/800) e 428 su 428 (XE) quadri "
                             "identici al dump di partenza.")
    callout(S, "NOTA", "Lo skeleton è compilato con <font face=\"Mono\">-t atari</font> e gira anche su un XL/XE, dove "
                       "la ROM dell'OS resta accesa. Il target <font face=\"Mono\">atarixl</font> del progetto completo "
                       "la spegne per avere più memoria, e questo cambia come si chiamano il sistema e gli interrupt.")
    section(S, "Come farlo crescere", need=80)
    table(S, [
        ["Aggiunta", "Cosa cambia", "Dove si vede nel progetto", "Capitolo"],
        ["più qualità nei bassi", "togliere <font face=\"Mono\">-m plain</font>: coppia a 16 bit; l'AUDCTL cambia", "layout in <font face=\"Mono\">sidconv</font>", "4"],
        ["brani multispeed", "K record per quadro, DLI nella display list", "<font face=\"Mono\">patchDisplayList</font>, <font face=\"Mono\">vbim</font>", "6"],
        ["più musica nella stessa memoria", "stream LZ per registro, buffer circolari", "<font face=\"Mono\">decode</font>, <font face=\"Mono\">lz_encode</font>", "5, 6"],
        ["due SID", "16 registri, secondo POKEY, rilevamento", "<font face=\"Mono\">putreg</font>, <font face=\"Mono\">detect_stereo</font>", "6"],
        ["titolo, autore, VU meter", "header con le stringhe, <font face=\"Mono\">outbuf</font> letto dal C", "<font face=\"Mono\">sid2pokey.c</font>", "7"],
        ["font C64", "<font face=\"Mono\">mkfont</font>, CHBAS, memoria riservata", "<font face=\"Mono\">install_font</font>", "7"],
    ], [34, 62, 52, 22], font=7.8, caption="Tabella 8.5 — Una strada di crescita.")
    callout(S, "CONSIGLIO", "Aggiungi <b>una cosa alla volta</b> e dopo ognuna rifai il confronto dei registri con l'emulatore "
                            "(capitolo 9): quando qualcosa si rompe, l'ultima modifica è la causa. È così che è stato "
                            "fatto il player completo.")


def ch9(S):
    chapter(S, "Verifica e test")
    P(S, "Il suono non si verifica a occhio, ma si può verificare quasi tutto il resto: i registri che il POKEY riceve, "
         "l'intonazione, gli opcode, le schermate. Il metodo è sempre lo stesso: confrontare ciò che un emulatore "
         "indipendente vede con ciò che il convertitore ha deciso.")
    section(S, "I cinque modi di verificare")
    table(S, [
        ["Cosa", "Come", "Riferimento"],
        ["i registri POKEY, quadro per quadro", "atari800 registra i registri a ogni quadro (<font face=\"Mono\">-pokeyrec</font>); "
                                                 "si confronta con <font face=\"Mono\">sidconv -d</font>", "il convertitore"],
        ["gli opcode 6502 non documentati", "588 casi eseguiti nel core e in VICE", "VICE x64sc 3.10"],
        ["l'intonazione", "toni sintetici registrati in WAV, picco della FFT", "la formula del divisore"],
        ["la schermata", "screenshot e confronto pixel per pixel (<font face=\"Mono\">compare -metric AE</font>) tra gli stati",
         "la schermata stessa"],
        ["la regressione sulla raccolta", "conversione di migliaia di brani HVSC; il verificatore dello stream gira a ogni conversione",
         "(nessun errore interno)"],
    ], [42, 88, 40], font=7.9, caption="Tabella 9.1 — I cinque controlli.")
    section(S, "Il confronto dei registri")
    P(S, "atari800 sa registrare i registri del POKEY a intervalli regolari. Con l'intervallo uguale a un quadro "
         "(312 righe in PAL) si ottiene una riga per quadro; con 312/K se ne ottengono K, e così si vedono anche i record "
         "suonati dai DLI.")
    code(S, "atari800 -xe -xlxe_rom ATARIXL.ROM -pal -stereo -pokeyrec -pokeyrec-stereo -pokeyrec-ascii \\\n"
            "         -pokeyrec-interval 156 -pokeyrec-file pr.txt -run sid2pokey.com", title="Registrare i registri (K = 2, due POKEY)")
    bullets(S, [
        "Il formato ASCII dà per ogni campione 18 cifre esadecimali: gli otto registri AUDF1…AUDC4 e AUDCTL; con "
        "<font face=\"Mono\">-pokeyrec-stereo</font> altre 18 per il secondo POKEY.",
        "Il campione parte quando l'emulatore parte: la riga corrispondente al primo record si trova cercando "
        "l'<b>allineamento</b> con il massimo numero di righe uguali (di solito qualche decina di campioni dopo, per l'avvio "
        "dell'OS).",
        "Se i campioni cadono mentre il player sta scrivendo, la riga contiene metà del record nuovo e metà del vecchio. "
        "Per questo il player scrive tutti i registri in una <b>raffica</b> alla fine della decodifica: con la scrittura registro "
        "per registro, a NTSC 2x l'8 % delle righe risultava a metà, e dopo la correzione zero.",
        "Con un intervallo che non è un divisore esatto del quadro (NTSC, K = 3 o 4: 262/3 e 262/4) il campionamento "
        "deriva. Per quei casi si registra una riga per quadro e si controlla che a ogni quadro si veda lo stesso record "
        "(838 quadri su 838).",
    ])
    code(S, "rows = [l.strip() for l in open('pr.txt') if len(l.strip()) == 36]      # 2 POKEY: 2 x 18 cifre\n"
            "p1 = [r[0:16] for r in rows];  p2 = [r[18:34] for r in rows]           # solo AUDF/AUDC, non AUDCTL\n"
            "exp = [l.split(':')[1].split() for l in open('dump.txt')]               # sidconv -d\n"
            "e1 = [''.join(x[:8]).lower() for x in exp]; e2 = [''.join(x[8:16]).lower() for x in exp]\n"
            "best = max(range(len(rows) - 200), key=lambda o: sum(p1[o + i] == e1[i] for i in range(200)))\n"
            "print(sum(p1[best + i] == e1[i] for i in range(len(e1))), 'record uguali su', len(e1))",
         title="Il confronto in Python (schema)", size=7)
    section(S, "Provare senza finestre: Xvfb")
    P(S, "Per i test automatici l'emulatore gira su un <b>display virtuale</b> (Xvfb): non compare nessuna finestra e si "
         "possono catturare le schermate con <font face=\"Mono\">import -window</font>. I tasti si inviano con "
         "<font face=\"Mono\">xdotool key</font>, che usa l'estensione XTEST: arrivano alla finestra sotto il puntatore, "
         "quindi il puntatore va spostato nella finestra dell'emulatore.")
    code(S, "Xvfb :77 -screen 0 1024x768x24 &\n"
            "export DISPLAY=:77\n"
            "atari800 -xe -xlxe_rom ATARIXL.ROM -pal -stereo -run sid2pokey.com &\n"
            "WID=$(xdotool search --pid $! | head -1)\n"
            "xdotool mousemove --window $WID 336 240      # il puntatore nella finestra\n"
            "xdotool key space                           # un tasto vero\n"
            "import -window $WID stopped.png", title="Una prova con un tasto, su un display virtuale")
    callout(S, "TRAPPOLA", "Nelle prove con la tastiera le lettere <font face=\"Mono\">a d w s</font> sono i tasti del joystick 1 "
                           "nella configurazione di atari800, e le altre lettere arrivano come eventi di testo che, senza un "
                           "window manager, non raggiungono l'emulatore. Si usano la barra spaziatrice e Invio: non è un "
                           "difetto del player, ma un test fatto con un tasto che non arriva è un test che non prova nulla.")
    callout(S, "NOTA", "Durante questo lavoro, per un certo periodo, atari800 usciva da solo con codice 0 meno di un secondo "
                       "dopo l'avvio sul desktop reale (riceveva una richiesta di chiusura della finestra), con qualunque "
                       "programma e anche con una configurazione vuota; su Xvfb viveva normalmente. La causa non è stata "
                       "trovata. Se succede, un display virtuale permette di continuare a provare.")
    section(S, "L'intonazione")
    P(S, "Per controllare le formule dei divisori sono stati costruiti stream sintetici con un solo tono (nessun SID): un "
         "tono a 16 bit a 110 Hz, uno a 55 Hz con il bit 15 kHz di AUDCTL attivo, uno a 8 bit a 64 kHz (440 Hz) e uno a "
         "15 kHz (220 Hz). Registrati in WAV da atari800 e misurati con la FFT:")
    table(S, [
        ["Tono", "AUDCTL", "Atteso (Hz)", "Misurato (Hz)", "Differenza"],
        ["16 bit a 1,79 MHz, N = 8054", "$50", "110,002", "110,000", "−0,0 cent"],
        ["8 bit a 64 kHz, N = 71", "$00", "439,843", "439,854", "+0,0 cent"],
        ["8 bit a 15 kHz, N = 34", "$01", "222,237", "222,229", "−0,1 cent"],
        ["16 bit con il bit 15 kHz attivo", "$51", "55,001", "55,011", "+0,3 cent"],
    ], [64, 20, 28, 30, 28], align="LCRRR", mono_cols=(1,), caption="Tabella 9.2 — Le formule dei divisori contro l'audio dell'emulatore.")
    section(S, "I risultati", need=110)
    table(S, [
        ["Prova", "Esito"],
        ["registri, 1x, 2x, 3x, 4x PAL, Atari 800 e XE", "tutti i record identici al convertitore"],
        ["registri, 2x NTSC (800); 3x e 4x NTSC con un campione per quadro", "identici; 838 quadri su 838 in fase"],
        ["due SID su due POKEY (2x e 4x, layout diversi sui due chip)", "1396/1396 e 2792/2792 su entrambi i POKEY, AUDCTL compresi"],
        ["due SID su un Atari senza secondo POKEY", "il POKEY 1 riceve esattamente SID 1 e mantiene il suo AUDCTL"],
        ["ritorno all'inizio dello stream (3 s suonati per 14 s)", "1473/1473 (4x), 372/372 (1x), 641/641 (XE 2x)"],
        ["stop e ripartenza con tasti veri", "294/294 su entrambi i POKEY; 1109 campioni a zero tra le due riproduzioni"],
        ["schermata, suono / pausa / ripartenza (spazio e Invio)", "0 pixel di differenza, 400/800 e XL/XE"],
        ["opcode non documentati contro VICE", "588 casi su 588 identici"],
        ["conversione di 4370 brani HVSC (1 ogni 12 di MUSICIANS)", "4292 convertiti, nessun errore interno"],
        ["conversione dei 264 file HVSC con un secondo SID", "261 convertiti"],
    ], [86, 84], font=7.9, caption="Tabella 9.3 — I risultati principali.")
    section(S, "Cosa non è stato verificato")
    bullets(S, [
        "<b>Come suona.</b> Nessuna prova all'orecchio è documentata qui: il giudizio sui bassi, sulle code degli inviluppi, "
        "sulla separazione stereo è di chi ascolta.",
        "<b>L'hardware reale.</b> Tutto è stato provato su emulatore. In particolare il rilevamento del secondo POKEY "
        "con «costante diversa da $FF» vale per atari800; su una scheda stereo vera dovrebbe variare RANDOM.",
        "<b>Il difetto dell'ADSR</b> (<i>delay bug</i>) e i filtri del SID non sono modellati, quindi non c'è nulla da "
        "confrontare.",
        "<b>I brani con campioni digitali</b>, guidati da NMI o da BASIC: non supportati.",
    ])


def ch10(S):
    chapter(S, "Trappole e risoluzione dei problemi")
    P(S, "Ogni riga di questa tabella è un problema incontrato davvero costruendo il progetto: il sintomo, "
         "la causa, il rimedio.")
    table(S, [
        ["Sintomo", "Causa", "Rimedio"],
        ["su XL/XE l'emulatore esce dopo pochi secondi", "chiamata diretta a $E45C con la ROM spenta (target atarixl)",
         "usare il simbolo <font face=\"Mono\">SETVBV</font> di <font face=\"Mono\">atari.inc</font>"],
        ["a fine brano si sentono suoni casuali", "i DLI sono partiti prima del primo VBI: record sfasati",
         "abilitare i DLI dal VBI (<font face=\"Mono\">vbim</font>), non in <font face=\"Mono\">startPlayer</font>"],
        ["i DLI non scattano", "<font face=\"Mono\">SETVBV</font> rimette NMIEN a $40", "scrivere NMIEN dopo SETVBV"],
        ["un brano a due SID suona male su un Atari normale", "$D210+ specchiano il POKEY 1: le scritture lo sporcano",
         "rilevare il secondo POKEY prima di scriverlo"],
        ["«No second POKEY» su atari800 con -stereo", "l'emulatore non implementa RANDOM del POKEY 2 (legge 0)",
         "costante diversa da $FF = presente"],
        ["banda di caratteri Atari a metà schermo", "il DLI passa da una chiamata che accende la ROM dell'OS",
         "servire il DLI dal vettore NMI in RAM"],
        ["da fermo tornano i glifi Atari", "<font face=\"Mono\">cgetc()</font> bloccante: la ROM resta accesa", "attendere il tasto leggendo CH"],
        ["la riga del titolo si buca premendo i tasti", "<font face=\"Mono\">cgetc()</font> fa l'eco del tasto sullo schermo",
         "leggere CH, consumare dopo il rilascio"],
        ["una pagina di BOOT ERROR all'uscita (XL/XE)", "<font face=\"Mono\">main</font> ritorna a un DOS inesistente", "non ritornare mai"],
        ["il brano va troppo veloce o lento", "PAL/NTSC non coincidono con lo stream", "<font face=\"Mono\">-p pal|ntsc</font>; il programma avverte"],
        ["«stream larger than 20 KB», o overflow al link", "il programma e i 16 buffer occupano circa 17 KB",
         "<font face=\"Mono\">-t</font> più corto, <font face=\"Mono\">-S 1</font>, oppure target XL/XE (circa 24 KB)"],
        ["il brano è muto", "campioni digitali via NMI o $D418: il modello a tre voci non li vede", "non supportato: l'avviso lo dice"],
        ["i bassi suonano tre ottave sopra", "divisore a 64 kHz: sotto 124 Hz la nota non si raggiunge",
         "lasciare <font face=\"Mono\">-m auto</font>: usa la coppia a 16 bit"],
        ["<font face=\"Mono\">make</font> non riconverte il brano", "<font face=\"Mono\">song.bin</font> dipende solo dal file SID",
         "<font face=\"Mono\">make -B song.bin ...</font>"],
        ["i test con le lettere non fanno nulla", "a d w s sono il joystick; le altre arrivano come testo", "provare con spazio e Invio"],
    ], [52, 66, 52], font=7.6, keep=False, caption="Tabella 10.1 — Sintomi, cause, rimedi.")
    callout(S, "CONSIGLIO", "Quando una prova dà un risultato che non capisci, confrontala prima con il dump di "
                            "<font face=\"Mono\">sidconv -d</font>: dice se il difetto è nella conversione (i registri attesi "
                            "sono già sbagliati) o nel player (i registri attesi sono giusti, quelli registrati no).")
