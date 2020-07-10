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
DEFINES ?= RETROBIT

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
	$(TARGETFILENAME)

C_SOURCES = \
	sid2pokey.c \
#	fonts.c \

OPTFLAGS = -Oi

ASM_SOURCES = \
	sp-common.asm \


all: $(TARGET)

$(TARGET): sid2pokey.c
	$(CL) $(OPTFLAGS) -t $(MACH) -D$(DEFINES) $(C_SOURCES) $(ASM_SOURCES) -o $(TARGETFILENAME)

build: $(TARGET)
	$(EMULATOR) $(EMUSWITCHES)

atr: $(TARGET)
	cp $(TARGETFILENAME) $(ATRFOLDER)/build/mypdos-406.ar0
	dir2atr -a -b MyPicoDos406 $(ATRFOLDER)/$(TARGET).atr $(ATRFOLDER)/build

clean:
	rm *.o
	rm $(TARGETFILENAME)
