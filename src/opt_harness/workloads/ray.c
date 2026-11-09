#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef struct {
    double x, y, z;
} Vec;
static Vec sub(Vec a, Vec b) {
    return (Vec){a.x - b.x, a.y - b.y, a.z - b.z};
}
static Vec cross(Vec a, Vec b) {
    return (Vec){a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
static double dot(Vec a, Vec b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}
static double hit(Vec o, Vec d, Vec a, Vec b, Vec c) {
    Vec e1 = sub(b, a), e2 = sub(c, a), p = cross(d, e2);
    double det = dot(e1, p);
    if (fabs(det) < 1e-10)
        return 0;
    double inv = 1 / det;
    Vec t = sub(o, a);
    double u = dot(t, p) * inv;
    if (u < 0 || u > 1)
        return 0;
    Vec q = cross(t, e1);
    double v = dot(d, q) * inv;
    if (v < 0 || u + v > 1)
        return 0;
    double distance = dot(e2, q) * inv;
    return distance > 1e-10 ? distance : 0;
}
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
    for (int r = 0; r < repeat; r++)
        for (int i = 0; i < 200000; i++) {
            Vec o = {(i % 997) / 997.0, (i % 991) / 991.0, -1 - r * 0.0001};
            checksum +=
                hit(o, (Vec){0.01, 0.02, 1}, (Vec){0, 0, 0}, (Vec){1, 0, 0}, (Vec){0, 1, 0});
        }
    double elapsed = now() - start;
    printf("{\"checksum\":%.17g,\"seconds\":%.9f}\n", checksum, elapsed);
    return !isfinite(checksum);
}
