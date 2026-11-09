#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define N 4096
static double re[N], im[N];
static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}
int main(int argc, char **argv) {
    int repeat = argc > 1 ? atoi(argv[1]) : 8;
    if (repeat < 1 || repeat > 100000)
        return 2;
    double start = now(), checksum = 0;
    for (int r = 0; r < repeat; r++) {
        for (int i = 0; i < N; i++) {
            re[i] = sin(i * 0.013 + r * 0.001);
            im[i] = 0;
        }
        for (unsigned i = 1, j = 0; i < N; i++) {
            unsigned bit = N >> 1;
            for (; j & bit; bit >>= 1)
                j ^= bit;
            j ^= bit;
            if (i < j) {
                double t = re[i];
                re[i] = re[j];
                re[j] = t;
            }
        }
        for (int len = 2; len <= N; len *= 2) {
            double angle = -6.2831853071795864769 / len;
            for (int i = 0; i < N; i += len) {
                double wr = 1, wi = 0, cr = cos(angle), ci = sin(angle);
                for (int j = 0; j < len / 2; j++) {
                    int u = i + j, v = u + len / 2;
                    double vr = re[v] * wr - im[v] * wi, vi = re[v] * wi + im[v] * wr;
                    re[v] = re[u] - vr;
                    im[v] = im[u] - vi;
                    re[u] += vr;
                    im[u] += vi;
                    double next = wr * cr - wi * ci;
                    wi = wr * ci + wi * cr;
                    wr = next;
                }
            }
        }
        for (int i = 0; i < N; i++)
            checksum += re[i] * re[i] + im[i] * im[i];
    }
    double elapsed = now() - start;
    printf("{\"checksum\":%.17g,\"seconds\":%.9f}\n", checksum, elapsed);
    return !isfinite(checksum);
}
