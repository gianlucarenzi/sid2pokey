#! /bin/mksh

# shasm65 -- NMOS 6502 Assembler for bash, zsh and mksh
# Copyright (C) 2009 by Ivo van Poorten <ivop@free.fr>

if test -n "$ZSH_VERSION" ; then
    set -o KSH_ARRAYS -o NO_BAD_PATTERN -o NO_BANG_HIST -o NO_BG_NICE -o NO_EQUALS -o NO_FUNCTION_ARGZERO -o GLOB_SUBST -o NO_GLOBAL_EXPORT -o NO_HUP -o INTERACTIVE_COMMENTS -o NO_MULTIOS -o NO_NOMATCH -o NO_NOTIFY -o POSIX_BUILTINS -o RM_STAR_SILENT -o SH_FILE_EXPANSION -o SH_GLOB -o SH_OPTION_LETTERS -o SH_WORD_SPLIT
fi

_fatal() { echo "$0: error: $@" >&2 ; exit 1 ; }

_input=() ; _out=a.xex ; _vflag=0

while test $# != 0; do
    case $1 in
        -h|--help|-help|-\?) cat << __EOF__

shasm65 -- NMOS 6502 Assembler for bash, zsh and mksh
Copyright (C) 2009 by Ivo van Poorten <ivop@free.fr>

Version 0.91

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Options:
    -oFILE      specify output filename [default: $_out]
    -v          enable verbose mode [default: off]

__EOF__
                exit 0 ;;
        -o*)    _out=${1:2} ;;
        -v)     _vflag=1 ;;
        -*)     _fatal "unknown option: $1" ;;
        *)      _input[${#_input[*]}]=$(test -f "$1" && find . -name "$1") ||
                                      _fatal "$1: file not found" ;;
    esac
    shift
done

test ${#_input} = 0 && _fatal "no input files"

_blockends=() ; _size=0 ; _here=0 ; _blockcount=0 ; _org=0

_octal=(0{0,1,2,3}{0,1,2,3,4,5,6,7}{0,1,2,3,4,5,6,7})
_screen=(`seq 64 95` `seq 0 63` `seq 96 127`)

_fatal2()  { j=$1 ; shift ; _fatal "$_i: $j: line ${BASH_LINENO[1]}: $@" ; }
_output()  { for i in $@ ; do echo -en "\\$i" >> $_out ; done ; }
_pass1()   { test $_pass = 1 ; }
_pass2()   { test $_pass = 2 ; }
_verbose() { test $_vflag = 1 ; }
lsb()      { test -n "$1" && echo $(( $1 &  0xff )) || echo 0; }
msb()      { test -n "$1" && echo $(( $1 >> 0x08 )) || echo 0; }
L()        { eval $1=$_here ; }

_blockstats() {
    _verbose && {
        test -n "$3" && echo -ne "\tsave " >&2 || echo -ne "   assembled " >&2
#        echo "block: $1 - $2 ("$(( $2 - $1 + 1))")" >&2
        printf "block: %04x - %04x (%04x)\n" $1 $2 $(($2-$1+1)) >&2
    }
}

.org() {
    _end=$(( $_org + $_size - 1 ))
    _pass1 && {
        _blockends[$_blockcount]=$_end
        test $_size != 0 && _blockstats $_org $_end
    }
    _org=$(($1)) ; _here=$_org
    test -z "$2" && _load= || _load=$(($2))
    test -z "$_load" && _load=$_org
    _size=0
    _blockcount=$(( $_blockcount + 1 ))
    _pass2 && {
        _blockend=${_blockends[$_blockcount]}
        _blockstats $_org $_blockend
        test $_blockend = $(( $_org - 1 )) && return
        test $_load != $_org && _blockend=$(($_blockend - $_org + $_load))
        _output ${_octal[255]} ${_octal[255]}                   \
                ${_octal[`lsb $_load`]} ${_octal[`msb $_load`]}   \
                ${_octal[`lsb $_blockend`]}    \
                ${_octal[`msb $_blockend`]}
        _blockstats $_load $_blockend 1
    }
}

_relative="bcc:0220 bcs:0260 beq:0360 bmi:0060
           bne:0320 bpl:0020 bvc:0120 bvs:0160"

for i in $_relative ; do
    j=${i%%:*}      # mnemonic
    k=${i#*:}       # opcode
    eval "$j"'() {
        let $((_size+=2)) ; let $((_here+=2))
        _a=$(( $1 - $_here ))
        test "$_a" -lt 0 && _a=$(( $_a + 256 ))
        test "$_a" -gt 255 && _fatal2 '"$j"' "branch too far"
        _pass2 && {
            test $# != 1 && _fatal2 '"$j"' "takes one operand"
            _output '"$k"' ${_octal[$_a]}
        }
    }'
done

_implied="brk:0000 clc:0030 cld:0330 cli:0130 clv:0270 dex:0312 dey:0210
          inx:0350 iny:0310 nop:0352 pha:0110 php:0010 pla:0150 plp:0050
          rti:0100 rts:0140 sec:0070 sed:0370 sei:0170 tax:0252 tay:0250
          tsx:0272 txa:0212 txs:0232 tya:0230"
_accum="asl:0012 rol:0052 lsr:0112 ror:0152"

for t in 1 2 ; do
    case $t in 1) u=$_implied ; v= ;; 2) u=$_accum ; v=.a ;; esac
    for i in $u ; do
        j=${i%%:*} ; k=${i#*:}
        eval "$j$v"'() {
        test $# != 0 && _fatal2 '"$j$v"' "does not take an operand"
            let $((_size++)) ; let $((_here++))
            _pass2 && _output '"$k"'
        }'
    done
done

_zp="bit:0044::     cpx:0344::     cpy:0304::
     adc:0145:0165: and:0045:0065: asl:0006:0026: cmp:0305:0325: dec:0306:0326:
     eor:0105:0125: inc:0346:0366: lda:0245:0265: ldy:0244:0264: lsr:0106:0126:
     ora:0005:0025: rol:0046:0066: ror:0146:0166: sbc:0345:0365: sta:0205:0225:
     sty:0204:0224: ldx:0246::0266 stx:0206::0226"

for i in $_zp ; do
    j=${i%%:*} ; n=${i#*:} ; k=${n%%:*} ; n=${n#*:} ; m=${n%%:*} ; n=${n#*:}
    eval "$j"'.z() {
        let $((_size+=2)) ; let $((_here+=2))
        _pass2 && {
            test $# != 1 && _fatal2 '"$j"'.z "takes one operand"
            _a=${1%%,*}
            case $1 in
                *,x) _b='"$m"' ;;
                *,y) _b='"$n"' ;;
                *,*) _fatal2 '"$j"'.z "invalid operand" ;;
                *)   _b='"$k"' ;;
            esac
            _a=$(($_a))
            test $_a -gt 255 && _fatal2 '"$j"'.z "can only access zero-page"
            test -z "$_b" && _fatal2 '"$j"'.z "addressing mode unavailable"
            _output $_b ${_octal[$_a]}
        }
    }'
done

_indxy="adc:0141:0161 and:0041:0061 cmp:0301:0321 eor:0101:0121
        lda:0241:0261 ora:0001:0021 sbc:0341:0361 sta:0201:0221"

for i in $_indxy ; do
    j=${i%%:*} ; m=${i#*:} ; k=${m%%:*} ; m=${m#*:}
    eval "$j"'.i() {
        let $((_size+=2)) ; let $((_here+=2))
        _pass2 && {
            test $# != 1 && _fatal2 '"$j"'.i "takes one operand"
            case $1 in
                \[*,x\]) _b='"$k"' ; _a=${1%%,*} ;;
                \[*\],y) _b='"$m"' ; _a=${1%%]*} ;;
                *) _fatal2 '"$j"'.i "invalid operand" ;;
            esac
            _a=$((${_a:1}))
            test $_a -gt 255 && _fatal2 '"$j"'.i "only zero-page indeces"
            _output $_b ${_octal[$_a]}
        }
    }'
done

_imm="adc:0151 and:0051 cmp:0311 cpx:0340 cpy:0300 eor:0111 lda:0251 ldx:0242
      ldy:0240 ora:0011 sbc:0351"

for i in $_imm ; do
    j=${i%%:*} ; k=${i#*:}
    eval "$j"'.() {
        let $((_size+=2)) ; let $((_here+=2))
        _pass2 && {
            test $# != 1 && _fatal2 '"$j"'. "takes one operand"
            case $1 in
                *,*|*\[*|*\]*) _fatal2 '"$j"'. "invalid operand" ;;
            esac
            _a=$(($1))
            test $_a -gt 255 && _fatal2 '"$j"'. "operand > 255"
            _output '"$k"' ${_octal[$_a]}
        }
    }'
done

_abs="adc:0155:0175:0171 and:0055:0075:0071 asl:0016:0036:
      bit:0054::         cmp:0315:0335:0331 cpx:0354::
      dec:0316:0336:     eor:0115:0135:0131 inc:0356:0376:
      jmp:0114::         jsr:0040::         lda:0255:0275:0271
      ldx:0256::0276     ldy:0254:0274:     lsr:0116:0136:
      ora:0015:0035:0031 rol:0056:0076:     ror:0156:0176:
      sbc:0355:0375:0371 sta:0215:0235:0231 stx:0216::          sty:0214::"

for i in $_abs ; do
    j=${i%%:*} ; n=${i#*:} ; k=${n%%:*} ; n=${n#*:} ; m=${n%%:*} ; n=${n#*:}
    eval "$j"'() {
        let $((_size+=3)) ; let $((_here+=3))
        _pass2 && {
            test $# != 1 && _fatal2 '"$j"' "takes one operand"
            _a=${1%%,*}
            case $1 in
                *,x) _b='"$m"' ;;
                *,y) _b='"$n"' ;;
                *,*) _fatal2 '"$j"' "invalid operand" ;;
                *)   _b='"$k"' ;;
            esac
            _a=$(($_a))
            test $_a -gt 65535 && _fatal2 '"$j"'.z "operand out of range"
            test -z "$_b" && _fatal2 '"$j"' "addressing mode unavailable"
            _output $_b ${_octal[`lsb $_a`]} ${_octal[`msb $_a`]}
        }
    }'
done

jmp.i() {
    let $((_size+=3)) ; let $((_here+=3))
    _pass2 && {
        test $# != 1 && _fatal2 'jmp.i' "takes one operand"
        _a=${1%%]*} ; _a=$((${_a:1}))
        _output 0154 ${_octal[`lsb $_a`]} ${_octal[`msb $_a`]}
    }
}

.byte() {
    let $((_size += $#)) ; let $((_here += $#))
    _pass2 && for _i in $@ ; do _output ${_octal[$_i]} ; done
}

.word() {
    let $((_size += $#+$#)) ; let $((_here += $#+$#))
    _pass2 && {
        for _i in $@ ; do
            _d=$(($_i))
            _output ${_octal[`lsb $_d`]} ${_octal[`msb $_d`]}
        done
    }
}

.ascii() {
    for _i in "$@" ; do
        _j=`echo -en "$_i"`
        let $((_size += ${#_j})) ; let $((_here += ${#_j}))
        _pass2 && echo -en "$_i" >> $_out
    done
}

.screen() {
    for _i in "$@" ; do
        _j=`echo -en "$_i"`
        let $((_size += ${#_j})) ; let $((_here += ${#_j}))
        _pass2 && {
            for _k in `seq 0 $((${#_j}-1))` ; do
                _c=`printf "%d" "'${_j:$_k:1}'"`
                _output ${_octal[${_screen[$_c]}]}
            done
        }
    done
}

.space() {
    _spcsize=$(($1)) ; _fill=$(($2))
    let $((_size += $_spcsize)) ; let $((_here += $_spcsize))
    _pass2 && for i in `seq 1 $_spcsize` ; do _output ${_octal[$_fill]} ; done
}

.align() {
    _mod=$(($1 - $_here % $1))
    test $_mod = "$1" && return || .space $_mod 0
}

.binary() {
    _s=`stat -c '%s' "$1"`
    let $((_size += $_s)) ; let $((_here += $_s))
    _pass2 && cat "$1" >> $_out
}

_pass=1 && echo 'pass 1:' >&2
for _i in ${_input[*]} ; do . $_i ; done
.org 0 # close last block

_blockcount=0
cat /dev/null >$_out
_pass=2 && echo 'pass 2:' >&2
for _i in ${_input[*]} ; do . $_i ; done

echo 'done' >&2
