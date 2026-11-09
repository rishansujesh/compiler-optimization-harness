#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define N 128
static double a[N][N], b[N][N], c[N][N];
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }
int main(int argc, char **argv) {
    int repeat = argc > 1 ? atoi(argv[1]) : 8;
    if (repeat < 1 || repeat > 100000) return 2;
    for (int i=0;i<N;i++) for(int j=0;j<N;j++) { a[i][j]=(i+j)%17/17.0; b[i][j]=(i*3+j)%13/13.0; }
    double start=now(), checksum=0;
    for(int r=0;r<repeat;r++) {
        a[0][0] = r * 0.000001; /* Each repetition has distinct, observed work. */
        for(int i=0;i<N;i++) for(int j=0;j<N;j++) {
            double sum=0; for(int k=0;k<N;k++) sum+=a[i][k]*b[k][j]; c[i][j]=sum;
        }
        for(int i=0;i<N;i++) for(int j=0;j<N;j++) checksum+=c[i][j];
    }
    double elapsed=now()-start;
    printf("{\"checksum\":%.17g,\"seconds\":%.9f}\n",checksum,elapsed);
    return !isfinite(checksum);
}
