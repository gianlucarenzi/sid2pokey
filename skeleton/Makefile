# Makefile of the skeleton: make SID=tune.sid
CL65     ?= cl65
SIDCONV  = ../tools/sidconv
SID      ?= tune.sid
SONG     ?= 1
DURATION ?= 60

player.com: main.c player.s data.s song.raw
	$(CL65) -t atari -Oi -o $@ main.c player.s data.s

# one POKEY (-S 1), three plain channels (-m plain), one record per frame (-k 1)
song.raw: $(SID) $(SIDCONV) dump2raw.py
	$(SIDCONV) -m plain -S 1 -k 1 -s $(SONG) -t $(DURATION) -d -o song.bin $(SID) > dump.txt
	python3 dump2raw.py dump.txt song.bin $@

$(SIDCONV):
	$(MAKE) -C .. tools/sidconv

clean:
	rm -f player.com *.o song.raw song.bin dump.txt
