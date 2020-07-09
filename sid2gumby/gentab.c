#include <stdio.h>

int t[65537];

void f(unsigned int s) {
    double c=16777216/985248;           // PAL SID
    unsigned int p;

    p=889200.0F/(s/c)+0.5;             // pokey
    if (p>0xffff) p=0xffff;
//    printf("%04x --> %04x\n", s, p);
    t[s]=p;
}

void calc_min_run_point(unsigned int v) {
    unsigned int i, c, x;
    c=1;
    for (i=0x100; i<0x10000; i++) {
        if (t[i] != t[i-1]) {
            if (c<v) x=i;
            c=0;
        }
        c++;
    }
//    printf("%04x\n", x);
}

/*
        0000-       16-bits is enough
        1562-       15-bits ...
        1e4a-       14 bits
        2ac6-       13-bits
        3c98-       12-bits
        5584-       11-bits
        7960-       10-bits
        abe7-        9-bits
        f280-        8-bits

        boundaries at high-byte, be on the safe side:

        0000-15ff   16-bits index   size: 0x1600
        1600-1eff   15-bits index   size: 0x0480
        1f00-2aff   14-bits index   size: 0x0300
        2b00-3cff   13-bits index   size: 0x0240
        3d00-55ff   12-bits index   size: 0x0190
        5600-79ff   11-bits index   size: 0x0120
        7a00-abff   10-bits index   size: 0x00c8
        ac00-ffff    9-bits index   size: 0x00a8    (no 8-bits table)

        total size: 0x23e0 words --> ~18kB
 */

void print(char *n, unsigned int start, unsigned int end, unsigned int step) {
    unsigned int i, j;

    printf("L %s\n", n);
    for (j=0, i=start; i<=end; i+=step) {
        if (!j) printf("    .word");
        printf(" 0x%04x", t[i]);
        j++;
        if (j==8) {
            j=0;
            printf("\n");
        }
    }
    printf("\n");
}

int main(int argc, char **argv) {
    unsigned int i;

    for (i=0; i<0x10000; i+=1) f(i);
    t[0]=0xffff;

    /*
    calc_min_run_point(2);
    calc_min_run_point(4);
    calc_min_run_point(8);
    calc_min_run_point(16);
    calc_min_run_point(32);
    calc_min_run_point(64);
    calc_min_run_point(128);
    calc_min_run_point(256);
    */

    print("table_0000_16", 0x0000, 0x15ff, 1);
    print("table_1600_15", 0x1600, 0x1eff, 2);
    print("table_1f00_14", 0x1f00, 0x2aff, 4);
    print("table_2b00_13", 0x2b00, 0x3cff, 8);
    print("table_3d00_12", 0x3d00, 0x55ff, 16);
    print("table_5600_11", 0x5600, 0x79ff, 32);
    print("table_7a00_10", 0x7a00, 0xabff, 64);
    print("table_ac00_9",  0xac00, 0xffff, 128);

    return 0;
}
