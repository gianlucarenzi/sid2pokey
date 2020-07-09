#! /bin/sh

for i in wisdom omahd mom toas warhawk cybernoid2  cybernoid  comets commando delta ik jt42 lightforce monty mythm freeze sanxion ; do
    export SONG=$i
    echo Building $i...
    ./shasm65.sh -v -osid2gumby-$i.xex sid2gumby.sh65 || exit 1
done
