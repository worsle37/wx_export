/*
 * scan_key.c — 微信 4.x SQLCipher 主密钥内存枚举器
 *
 * 原理：SQLCipher（raw-key 模式）页 1 的第 2 个 16 字节块 C1 用密钥 K 解密后
 *       XOR IV 必须等于明文头 "SQLite format 3\0"。
 *       因此 AES_dec(K, C1) == "SQLite format 3\0" ^ IV 是一个 128 位精确判据。
 *       对内存中每个 32 字节对齐/非对齐窗口做一次 AES-256 单块解密即可判定，
 *       假阳性概率 2^-128。
 *
 * 用法：scan_key.exe <mem_dump.bin> <encrypted_db_file> [stride]
 *       encrypted_db_file 需可读（可用 FileShare.ReadWrite 先复制一份）。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <wmmintrin.h>
#include <emmintrin.h>

#define PAGE 4096
#define RESERVED_SET 4
static const int RESERVED[RESERVED_SET] = {80, 48, 64, 32};

typedef struct { __m128i k[15]; } AES256KEY;

static inline __m128i keyassist_sbox(__m128i a, __m128i b) {
    __m128i t;
    b = _mm_shuffle_epi32(b, 0xff);
    t = _mm_slli_si128(a, 4); a = _mm_xor_si128(a, t);
    t = _mm_slli_si128(t, 4); a = _mm_xor_si128(a, t);
    t = _mm_slli_si128(t, 4); a = _mm_xor_si128(a, t);
    return _mm_xor_si128(a, b);
}
static inline __m128i keyassist_plain(__m128i a, __m128i b) {
    __m128i t;
    b = _mm_shuffle_epi32(b, 0xaa);
    t = _mm_slli_si128(a, 4); a = _mm_xor_si128(a, t);
    t = _mm_slli_si128(t, 4); a = _mm_xor_si128(a, t);
    t = _mm_slli_si128(t, 4); a = _mm_xor_si128(a, t);
    return _mm_xor_si128(a, b);
}

static inline void expand256(const uint8_t *uk, AES256KEY *ks) {
    __m128i t1 = _mm_loadu_si128((const __m128i *)uk);
    __m128i t3 = _mm_loadu_si128((const __m128i *)(uk + 16));
    __m128i t2;
    ks->k[0] = t1; ks->k[1] = t3;
    int idx = 2;
    /* rcon 必须是编译期常量（aeskeygenassist 的立即数约束），故展开 */
    #define RSTEP(rc) \
        t2 = _mm_aeskeygenassist_si128(t3, rc); \
        t1 = keyassist_sbox(t1, t2); ks->k[idx++] = t1; \
        if (idx <= 14) { \
            t2 = _mm_aeskeygenassist_si128(t1, 0x00); \
            t3 = keyassist_plain(t3, t2); ks->k[idx++] = t3; \
        }
    RSTEP(0x01) RSTEP(0x02) RSTEP(0x04) RSTEP(0x08)
    RSTEP(0x10) RSTEP(0x20) RSTEP(0x40)
    #undef RSTEP
}

static inline __m128i dec_block(const AES256KEY *ks, __m128i c) {
    c = _mm_xor_si128(c, ks->k[14]);
    for (int i = 13; i >= 1; i--)
        c = _mm_aesdec_si128(c, _mm_aesimc_si128(ks->k[i]));
    return _mm_aesdeclast_si128(c, ks->k[0]);
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s dump.bin enc.db [stride]\n", argv[0]); return 2; }
    int stride = argc > 3 ? atoi(argv[3]) : 4;

    uint8_t page1[PAGE];
    FILE *fd = fopen(argv[2], "rb");
    if (!fd) { perror("open db"); return 2; }
    if (fread(page1, 1, PAGE, fd) != PAGE) { fprintf(stderr, "short read\n"); return 2; }
    fclose(fd);

    __m128i c1 = _mm_loadu_si128((const __m128i *)(page1 + 16));
    const uint8_t target[16] = {'S','Q','L','i','t','e',' ','f','o','r','m','a','t',' ','3',0};
    __m128i want[RESERVED_SET];
    for (int i = 0; i < RESERVED_SET; i++) {
        const uint8_t *iv = page1 + PAGE - RESERVED[i];
        uint8_t x[16];
        for (int j = 0; j < 16; j++) x[j] = target[j] ^ iv[j];
        want[i] = _mm_loadu_si128((const __m128i *)x);
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("open dump"); return 2; }
    fseek(f, 0, SEEK_END);
    long long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = (uint8_t *)malloc((size_t)sz);
    if (!buf) { fprintf(stderr, "oom\n"); return 2; }
    if (fread(buf, 1, (size_t)sz, f) != (size_t)sz) { fprintf(stderr, "short dump read\n"); return 2; }
    fclose(f);

    long long limit = sz - 32;
    long long matches = 0;
    for (long long o = 0; o <= limit; o += stride) {
        __m128i p;
        {   /* 快速预筛：全零/明显可打印的窗口跳过（密钥是随机字节） */
            uint64_t a, b;
            memcpy(&a, buf + o, 8); memcpy(&b, buf + o + 8, 8);
            if ((a | b) == 0) continue;
        }
        AES256KEY ks;
        expand256(buf + o, &ks);
        p = dec_block(&ks, c1);
        for (int i = 0; i < RESERVED_SET; i++) {
            if (_mm_movemask_epi8(_mm_cmpeq_epi8(p, want[i])) == 0xffff) {
                printf("MATCH offset=%lld reserved=%d key=", o, RESERVED[i]);
                for (int j = 0; j < 32; j++) printf("%02x", buf[o + j]);
                printf("\n");
                fflush(stdout);
                matches++;
            }
        }
    }
    fprintf(stderr, "scanned %.1f MB, stride=%d, matches=%lld\n", sz / 1048576.0, stride, matches);
    free(buf);
    return 0;
}
