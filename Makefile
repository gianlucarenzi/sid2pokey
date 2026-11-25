# Makefile
CL ?= cl65
MACH ?= atarixl
TARGET ?= sid2pokey
TARGETFILENAME ?= $(TARGET).com
EMULATOR ?= atari800
ATRFOLDER ?= ~/ATARI/ATR
ROM ?= ~/ATARI/ATARIXL.ROM
ROMSWITCH ?= -xlxe_rom
MACHINE ?= xe
# second POKEY in the emulator, needed by dual SID tunes (harmless otherwise)
STEREO ?= -stereo
DEFINES ?= RETROBIT

# SID -> POKEY conversion (see tools/sidconv.c)
HOSTCC ?= gcc
SIDCONV = tools/sidconv
SID ?= $(HOME)/Music/C64Music/MUSICIANS/H/Hubbard_Rob/Commando.sid
SONG ?= 1
DURATION ?= 60
VIDEO ?= pal

ifeq ($(MACH),atari)
	ROM = ~/ATARI/ATARIOSB.ROM
	ROMSWITCH = -osb_rom
	MACHINE =
	DEFINES += -DATARI800 \
	
endif

EMUSWITCHES = \
	-win-width 800 \
	-win-height 600 \
	$(ROMSWITCH) $(ROM) \
	-$(MACHINE) \
	-scanlines 50 \
	-scanlinesint \
	$(STEREO) \
	$(TARGETFILENAME)

C_SOURCES = \
	sid2pokey.c \
#	fonts.c \

OPTFLAGS = -Oi

ASM_SOURCES = \
	sp-common.asm \
	sp-data.asm \


all: $(TARGET)

$(SIDCONV): tools/sidconv.c tools/cpu6502.h
	$(HOSTCC) -O2 -Wall -o $@ tools/sidconv.c -lm

# song.bin is not rebuilt when only SONG/DURATION/VIDEO change: use "make -B song.bin"
song.bin: $(SIDCONV) $(SID)
	$(SIDCONV) -v -s $(SONG) -t $(DURATION) -p $(VIDEO) -o $@ $(SID)

$(TARGET): sid2pokey.c sp-common.asm sp-data.asm song.bin
	$(CL) $(OPTFLAGS) -t $(MACH) -D$(DEFINES) $(C_SOURCES) $(ASM_SOURCES) -o $(TARGETFILENAME)

build: $(TARGET)
	$(EMULATOR) $(EMUSWITCHES)

atr: $(TARGET)
	cp $(TARGETFILENAME) $(ATRFOLDER)/build/mypdos-406.ar0
	dir2atr -a -b MyPicoDos406 $(ATRFOLDER)/$(TARGET).atr $(ATRFOLDER)/build

clean:
	rm -f *.o $(TARGETFILENAME) song.bin $(SIDCONV)
