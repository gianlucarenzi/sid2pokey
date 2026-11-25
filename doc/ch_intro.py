# ch_intro.py - cover, how to read, chapters 1 (overview) and 2 (hardware)
import datetime
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import NextPageTemplate, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

import diagrams as D
from pdflib import (BLUE, BODY_W, INK, MARGIN_X, ST, bullets, callout, chapter, code, esc, figure, flow, m,
                    numbered, P, section, sub, table)


def git_short():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=D.__file__.rsplit("/", 2)[0],
                                       text=True).strip()
    except Exception:
        return "?"


def cover(S):
    ind = MARGIN_X
    S.append(Spacer(1, 38 * mm))
    S.append(Paragraph("SID → POKEY", ParagraphStyle("t1", fontName="Sans-Bold", fontSize=44, leading=48,
                                                          textColor=colors.white, leftIndent=ind)))
    S.append(Spacer(1, 4 * mm))
    S.append(Paragraph("Costruire un SID player per gli Atari 8-bit",
                       ParagraphStyle("t2", fontName="Sans-Bold", fontSize=20, leading=25,
                                      textColor=colors.HexColor("#C9CEFF"), leftIndent=ind)))
    S.append(Spacer(1, 8 * mm))
    S.append(Paragraph("Dal file PSID allo schermo: il convertitore, il formato dello stream, il player 6502,<br/>"
                       "l'interfaccia con il font C64 e i VU meter, e uno skeleton da cui partire.",
                       ParagraphStyle("t3", fontName="Sans", fontSize=11.2, leading=16, textColor=colors.white,
                                      leftIndent=ind, rightIndent=ind)))
    S.append(Spacer(1, 11 * mm))
    from pdflib import IMG
    import os
    from reportlab.platypus import Image, Table, TableStyle
    from PIL import Image as PI
    path = os.path.join(IMG, "ui_dual_xe.png")
    w, h = PI.open(path).size
    wp = 112 * mm
    im = Image(path, width=wp, height=wp * h / w)
    t = Table([[im]], colWidths=[wp + 6])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, BLUE), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    t.hAlign = "LEFT"
    S.append(Table([[None, t]], colWidths=[ind, wp + 10], style=TableStyle(
        [("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)])))
    S.append(Spacer(1, 30 * mm))
    meta = ParagraphStyle("meta", fontName="Sans", fontSize=8.6, leading=12.5, textColor=INK, leftIndent=ind,
                          rightIndent=ind)
    S.append(Paragraph("<b>Repository</b>  github.com/gianlucarenzi/sid2pokey  —  commit %s, più lo skeleton "
                       "e questa documentazione<br/><b>Versione del documento</b>  %s<br/>"
                       "<b>Target</b>  Atari 400, 800, 600XL, 800XL, 130XE (PAL e NTSC), con uno o due POKEY<br/>"
                       "<b>Strumenti</b>  cc65 2.19, gcc, make, Python 3, atari800 7.x (VICE solo per la ROM dei "
                       "caratteri C64 e per i test)" % (git_short(), datetime.date.today().isoformat()), meta))
    S.append(NextPageTemplate("body"))
    S.append(PageBreak())


def toc(S):
    S.append(Paragraph("Indice", ST["h1x"]))
    t = TableOfContents()
    t.levelStyles = [ST["toc1"], ST["toc2"]]
    t.dotsMinLevel = 0
    S.append(t)
    S.append(PageBreak())


def how_to_read(S):
    S.append(Paragraph("Come leggere questo documento", ST["h1"]))
    P(S, "Il documento spiega come si costruisce un player per file SID su un Atari a 8 bit, e lo fa seguendo il "
         "progetto <b>sid2pokey</b>: un convertitore per PC (<font face=\"Mono\">tools/sidconv</font>), un formato di "
         "stream compresso, un player in assembly 6502 che gira negli interrupt e una schermata in stile C64. "
         "Ogni numero e ogni tabella viene da una misura o dal codice; quando una cosa non è stata verificata lo "
         "dico.")
    P(S, "I capitoli 1-3 danno il contesto, i capitoli 4-7 descrivono i componenti uno per uno, il capitolo 8 "
         "contiene lo <b>skeleton</b>: il player più piccolo possibile, con tutti i file, da costruire e far "
         "girare per capire il meccanismo prima di passare a quello completo. I capitoli 9 e 10 raccolgono le verifiche "
         "e le trappole in cui si cade più facilmente.")
    sub(S, "Riquadri")
    callout(S, "NOTA", "Informazione di contesto: serve per capire, non per agire.")
    callout(S, "CONSIGLIO", "Un modo di procedere che ha dato buoni risultati.")
    callout(S, "ATTENZIONE", "Un limite o una scelta che ha conseguenze: conviene saperlo prima di cominciare.")
    callout(S, "TRAPPOLA", "Un errore reale, in cui si cade facilmente: il sintomo, la causa e il rimedio.")
    callout(S, "VERIFICATO", "Qualcosa che è stato provato su un emulatore o confrontato con un riferimento "
                              "indipendente, con il risultato.")
    sub(S, "Convenzioni")
    table(S, [
        ["Notazione", "Significato"],
        ["$D200", "numero esadecimale (come in assembly 6502)"],
        ["AUDF1 … AUDC4", "gli otto registri audio del POKEY, in questo ordine (indice 0-7)"],
        ["POKEY 1 / POKEY 2", "il chip a $D200 e il secondo chip della scheda stereo, a $D210"],
        ["SID 1 / SID 2", "il primo e il secondo chip SID di un brano a due SID"],
        ["record", "i valori dei registri POKEY per un istante della musica (una chiamata di <font face=\"Mono\">play</font>)"],
        ["frame", "un quadro video: 49,86 Hz in PAL, 59,92 Hz in NTSC; contiene da 1 a 4 record"],
        ["K", "numero di record per frame (1 = normale, 2-4 = brani multispeed)"],
        ["400/800, XL/XE", "i due target di compilazione: <font face=\"Mono\">atari</font> e <font face=\"Mono\">atarixl</font>"],
    ], [38, 132], mono_cols=(0,))


def ch1(S):
    chapter(S, "Panoramica")
    section(S, "Il problema: un file SID non contiene audio")
    P(S, "Un file <b>SID</b> (formato PSID, o RSID per i brani che pretendono un C64 completo) contiene un pezzo di "
         "<b>codice 6502</b> e i suoi dati: la musica è suonata da quel codice, che il C64 esegue una volta per "
         "quadro video (50 Hz in PAL) scrivendo nei 25 registri del chip SID, che sintetizza il suono. Nel file ci sono "
         "l'indirizzo di caricamento, quello della routine <font face=\"Mono\">init</font> (prepara un brano) e "
         "quello della routine <font face=\"Mono\">play</font> (da chiamare a ogni quadro), più titolo, autore e "
         "copyright. Non c'è nessuna forma d'onda da riprodurre.")
    P(S, "L'Atari ha un altro chip, il <b>POKEY</b>: quattro canali a 8 bit con un divisore di frequenza, una "
         "distorsione a polinomi e un volume a 4 bit. Non ha inviluppi, filtri, forme d'onda triangolari o a dente "
         "di sega. Un SID player per Atari deve quindi <b>tradurre</b> quello che il SID fa in quello che il POKEY "
         "sa fare, e farlo nel tempo di un quadro video su una CPU a 1,79 MHz.")
    section(S, "Due strade")
    P(S, "Ci sono due modi di affrontare il problema. Il primo è portare il codice del brano sull'Atari e "
         "farlo girare là; il secondo è farlo girare sul PC una volta sola, registrare cosa scrive nel SID "
         "e portare sull'Atari solo il risultato tradotto.")
    table(S, [
        ["", "A. Eseguire il codice SID sull'Atari", "B. Convertire sul PC (questo progetto)"],
        ["Idea", "Il brano viene caricato com'è; le scritture a $D400 sono deviate in un'area di memoria; "
                 "una routine al VBI traduce quei valori in AUDF/AUDC.",
         "Un emulatore 6502 sul PC esegue <font face=\"Mono\">init</font> e <font face=\"Mono\">play</font>, "
         "registra i registri SID a ogni chiamata e li traduce una volta per tutte."],
        ["Lavoro per brano", "Ogni brano va rilocato e le sue scritture a $D400 corrette a mano o con strumenti "
                             "dedicati (è la strada di sid2gumby).",
         "Nessuno: un solo comando converte qualunque brano che l'emulatore sa eseguire."],
        ["Memoria sull'Atari", "Il codice originale (fino a decine di KB) più il traduttore e le tabelle di frequenza.",
         "Solo lo stream compresso: circa 1,5 KB al minuto per un brano tipico."],
        ["Qualità della traduzione", "Limitata dal tempo di CPU disponibile in un quadro; l'ADSR va "
                                         "approssimato in poche istruzioni.",
         "Libera: la traduzione costa tempo solo sul PC (ADSR esatto, scelta dei canali per errore minimo)."],
        ["Interattività", "Il brano può reagire a eventi (rari nei SID).",
         "Nessuna: si suona quello che è stato registrato. Un brano è lungo quanto si converte."],
        ["Brani non supportati", "Quelli che non si lasciano rilocare.",
         "Quelli che campionano la voce ($D418), guidati da NMI, o che pretendono un C64 intero."],
    ], [30, 70, 70], font=7.9)
    callout(S, "NOTA", "Il repository contiene anche <font face=\"Mono\">sid2gumby/</font>, il progetto di Ivo van "
                       "Poorten (GPL 3) da cui questo è nato: è un buon esempio della strada A. sid2pokey "
                       "percorre la strada B.")
    section(S, "L'architettura", need=118)
    flow(S, D.Architecture(), "Figura 1.1 — Il flusso dei dati: il lavoro pesante si fa sul PC, l'Atari riceve uno "
                              "stream compresso e lo decodifica mentre suona.")
    numbered(S, [
        "<b>Emulatore 6502.</b> Carica il brano in una memoria da 64 KB, chiama <font face=\"Mono\">init</font> e poi "
        "<font face=\"Mono\">play</font> al ritmo giusto, e intercetta le scritture ai registri SID.",
        "<b>Modello SID.</b> Per ogni voce calcola frequenza, forma d'onda e volume, con l'inviluppo ADSR del chip vero.",
        "<b>Mappatura POKEY.</b> Sceglie su quali canali mettere le tre voci (otto disposizioni candidate, vince "
        "quella con l'errore di intonazione minore) e calcola divisori e distorsione.",
        "<b>Compressione.</b> Scrive uno stream con un flusso LZ per ogni registro POKEY che cambia, e lo rilegge con "
        "lo stesso algoritmo del player per essere sicuro che sia identico.",
        "<b>Player 6502.</b> Una routine al vertical blank (e, per i brani multispeed, agli interrupt di display "
        "list) decodifica lo stream e scrive i registri POKEY.",
        "<b>Schermata.</b> Un programma C disegna titolo, autore e un VU meter per voce, leggendo i valori che il "
        "player ha appena decodificato.",
    ])
    section(S, "Cosa si ottiene")
    table(S, [
        ["Funzione", "Stato"],
        ["Un SID (3 voci) su un POKEY", "completo"],
        ["Due SID (PSID v3) su due POKEY (scheda stereo), un SID per chip", "completo; il terzo SID è ignorato con avviso"],
        ["Brani multispeed (2x, 3x, 4x per quadro)", "completo fino a 4x; oltre, ricampionato a 4"],
        ["Brani con un proprio gestore IRQ (<font face=\"Mono\">play</font> = 0)", "completo se il gestore è un IRQ"],
        ["Coppia a 16 bit a 1,79 MHz per i bassi", "automatica, per ciascun chip"],
        ["Inviluppo ADSR del SID (contatore di velocità + esponenziale)", "come reSID, senza l'ADSR delay bug"],
        ["Compressione dello stream", "circa 6 volte rispetto a un formato a differenze"],
        ["Opcode 6502 non documentati, anche instabili", "tutti tranne i 12 JAM, confrontati con VICE"],
        ["Schermata C64 con titolo, autore, VU meter, tempo", "400/800 e XL/XE"],
        ["Filtro, ring modulation, sync, modulazione di impulso", "non modellati"],
        ["Campioni digitali ($D418), brani guidati da NMI, BASIC", "non supportati: il convertitore lo dice"],
    ], [118, 52])
    section(S, "Requisiti e avvio rapido")
    table(S, [
        ["Strumento", "A cosa serve", "Note"],
        ["cc65 (cl65, ca65, ld65)", "compila il player e la schermata", "provato con 2.19"],
        ["gcc, make", "compila <font face=\"Mono\">sidconv</font> e <font face=\"Mono\">mkfont</font> per il PC", ""],
        ["Python 3", "skeleton (<font face=\"Mono\">dump2raw.py</font>), test degli opcode", "solo libreria standard"],
        ["atari800 7.x", "prova del player; il registratore dei POKEY", "servono le ROM dell'OS (400/800 e XL/XE)"],
        ["Una raccolta SID (HVSC)", "i brani da convertire", ""],
        ["ROM dei caratteri C64", "il font della schermata", "VICE: <font face=\"Mono\">chargen-901225-01.bin</font>; facoltativa"],
        ["VICE x64sc", "solo per rigenerare il riferimento del test degli opcode", "facoltativo"],
    ], [42, 78, 50], font=7.9)
    P(S, "Dalla cartella del progetto, per convertire un brano e vederlo suonare su un XL/XE emulato con due POKEY:")
    code(S, "make -B song.bin SID=~/Music/C64Music/MUSICIANS/H/Hubbard_Rob/Commando.sid DURATION=60\n"
            "make            # target atarixl (XL/XE): produce sid2pokey.com\n"
            "make build      # lancia atari800 con -stereo\n"
            "\n"
            "make MACH=atari # lo stesso per un 400/800 (48 KB)", title="Avvio rapido")
    callout(S, "ATTENZIONE", "<font face=\"Mono\">make</font> non riconverte <font face=\"Mono\">song.bin</font> quando "
                             "cambiano solo <font face=\"Mono\">SONG</font>, <font face=\"Mono\">DURATION</font> o "
                             "<font face=\"Mono\">VIDEO</font>: dipende solo dal file SID. Usa "
                             "<font face=\"Mono\">make -B song.bin ...</font> per forzarlo.")
    callout(S, "ATTENZIONE", "La ROM dei caratteri C64 è di Commodore: il font si costruisce in locale "
                             "(<font face=\"Mono\">font.bin</font>) e non fa parte del repository. Senza la ROM la "
                             "build continua con il font Atari (capitolo 7).")


def ch2(S):
    chapter(S, "Il quadro hardware: SID e POKEY")
    section(S, "Il chip SID")
    P(S, "Il SID (6581/8580) ha tre voci indipendenti, un filtro e un volume generale. Ogni voce ha un "
         "accumulatore di fase a 24 bit: a ogni ciclo di clock vi si somma il valore a 16 bit dei registri di frequenza, "
         "e la frequenza prodotta è")
    P(S, "<b>f = Fn × clock / 2<super>24</super></b>,  con clock = 985 248 Hz (PAL) o 1 022 727 Hz (NTSC).")
    P(S, "La forma d'onda si sceglie con quattro bit del registro di controllo (triangolo, dente di sega, impulso, "
         "rumore, anche combinati). Ogni voce ha un inviluppo ADSR a 8 bit; il rumore è un registro a scorrimento "
         "che avanza al ritmo dell'accumulatore.")
    table(S, [
        ["Registro", "Voce 1", "Voce 2", "Voce 3", "Contenuto"],
        ["frequenza (lo, hi)", "$D400-01", "$D407-08", "$D40E-0F", "Fn, 16 bit"],
        ["larghezza d'impulso", "$D402-03", "$D409-0A", "$D410-11", "12 bit"],
        ["controllo", "$D404", "$D40B", "$D412", "bit 7 rumore, 6 impulso, 5 dente, 4 triangolo, 3 test, 0 gate"],
        ["attacco / decadimento", "$D405", "$D40C", "$D413", "AD: attacco (alto), decadimento (basso)"],
        ["sustain / rilascio", "$D406", "$D40D", "$D414", "SR: livello di sustain (alto), rilascio (basso)"],
        ["generali", "$D415-18", "", "", "filtro, risonanza, modo e <b>volume</b> ($D418, bit 0-3)"],
    ], [34, 20, 20, 20, 76], mono_cols=(1, 2, 3))
    section(S, "Il chip POKEY")
    P(S, "Il POKEY ha quattro canali. Ognuno ha un divisore a 8 bit (AUDFn) e un registro di controllo (AUDCn) con "
         "tre bit di distorsione, un bit di «volume solo» e quattro bit di volume. Il registro AUDCTL ($D208) "
         "sceglie il clock dei canali e permette di <b>unire due canali in un divisore a 16 bit</b>.")
    table(S, [
        ["Base di clock", "Frequenza (PAL)", "Divisore", "Frequenza prodotta", "Gamma utile"],
        ["64 kHz (CPU/28)", "63 337 Hz", "N + 1, N ≤ 255", "f = clk / (2 (N+1))", "da 124 Hz a 31 kHz"],
        ["15 kHz (CPU/114)", "15 556 Hz", "N + 1, N ≤ 255", "f = clk / (2 (N+1))", "da 30 Hz a 7,8 kHz"],
        ["1,79 MHz, 16 bit", "1 773 447 Hz", "N + 7, N ≤ 65535", "f = clk / (2 (N+7))", "da 13,5 Hz a 126 kHz"],
    ], [34, 30, 33, 41, 32])
    P(S, "Ci sono due vincoli che guidano tutte le scelte successive: a 64 kHz le note basse (sotto circa 124 Hz) "
         "non si raggiungono, e a 15 kHz le note alte hanno una risoluzione di mezzo tono o peggio. La coppia a 16 bit a "
         "1,79 MHz risolve entrambi i problemi, ma consuma due canali.")
    table(S, [
        ["AUDCTL", "Effetto"],
        ["bit 0", "tutti i canali sul clock a 15 kHz invece di 64 kHz"],
        ["bit 1 / bit 2", "filtro passa-alto del canale 1 (clock dal canale 3) / del canale 2 (dal 4)"],
        ["bit 3", "canale 4 collegato al 3: divisore a 16 bit, uscita sul 4"],
        ["bit 4", "canale 2 collegato all'1: divisore a 16 bit, uscita sul 2 (AUDF1 = parte bassa, AUDF2 = alta)"],
        ["bit 5 / bit 6", "canale 3 / canale 1 sul clock della CPU (1,79 MHz)"],
        ["bit 7", "polinomio a 9 bit invece di 17"],
    ], [28, 142], mono_cols=(0,), caption="Tabella 2.1 — Il registro AUDCTL. Il progetto usa i bit 0, 4 e 6: $00, $01, $50 e $51.")
    table(S, [
        ["AUDCn bit 7-5", "Distorsione", "Uso nel progetto"],
        ["000", "polinomi a 5 e 17 bit", ""],
        ["100", "polinomio a 17 bit (rumore)", "forma d'onda rumore del SID: $8x"],
        ["101", "onda quadra pura", "tutte le altre forme d'onda: $Ax"],
        ["110", "polinomio a 4 bit", "non usata: cambia l'intonazione (periodo 15)"],
    ], [34, 66, 70], mono_cols=(0,), caption="Tabella 2.2 — La distorsione (selezione). Il bit 4 è «volume solo», i bit 3-0 il volume.")
    section(S, "Confronto e cosa va approssimato")
    table(S, [
        ["", "SID", "POKEY", "Come lo gestisce il convertitore"],
        ["Voci / canali", "3 voci", "4 canali (o 2 a 16 bit)", "8 disposizioni candidate per chip"],
        ["Forme d'onda", "triangolo, dente, impulso, rumore", "quadra o rumore", "rumore → $8x, il resto → $Ax"],
        ["Volume", "ADSR a 8 bit × volume a 4 bit", "4 bit per canale", "livello × volume / 255, arrotondato"],
        ["Intonazione", "accumulatore a 24 bit", "divisore a 8 o 16 bit", "divisore più vicino; ottave ripiegate se serve"],
        ["Filtro, ring, sync, PWM", "sì", "no", "ignorati"],
        ["Campioni digitali", "via volume ($D418)", "solo volume-only", "non supportati"],
    ], [28, 44, 40, 58], font=7.9)
    section(S, "Le costanti di tempo")
    table(S, [
        ["Grandezza", "PAL", "NTSC", "Note"],
        ["clock CPU/POKEY dell'Atari", "1 773 447 Hz", "1 789 773 Hz", ""],
        ["righe per quadro", "312", "262", "114 cicli per riga"],
        ["frequenza di quadro dell'Atari", "49,861 Hz", "59,923 Hz", "clock / (righe × 114)"],
        ["clock del SID", "985 248 Hz", "1 022 727 Hz", ""],
        ["frequenza di <font face=\"Mono\">play</font> sul C64", "50,125 Hz", "59,826 Hz", "clock / (312 × 63), clock / (263 × 65)"],
    ], [58, 32, 32, 48])
    callout(S, "ATTENZIONE", "Un brano scritto per PAL (50,125 Hz) suonato su un Atari NTSC (59,92 Hz) va troppo veloce "
                             "del 20 %. Il convertitore ricampiona nel tempo reale (opzione <font face=\"Mono\">-p</font>) "
                             "e il programma avverte se lo stream e la macchina non hanno la stessa frequenza.")
    section(S, "Il secondo POKEY")
    P(S, "Le schede stereo per Atari aggiungono un secondo POKEY a <b>$D210-$D21F</b> (uno solo scrive "
         "AUDF1 a $D210, AUDCTL a $D218). Senza la scheda quegli indirizzi sono uno <b>specchio</b> del primo chip: una "
         "scrittura a $D210 finisce in AUDF1 del POKEY 1. Per questo il player non scrive mai nel secondo POKEY senza "
         "averne verificato la presenza (capitolo 6).")
    figure(S, "ui_dual_xe.png", "Figura 2.1 — Un brano a due SID sull'XE emulato con due POKEY: due gruppi di "
                                "tre VU meter, uno per chip.", width_mm=96)
