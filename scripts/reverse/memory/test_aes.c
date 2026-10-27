#define main scan_main
#include "scan_key.c"
#undef main

/* NIST AES-256 ECB 测试向量验证 */
int main(void) {
    uint8_t key[32], pt[16], ct[16], out[16];
    for (int i = 0; i < 32; i++) key[i] = (uint8_t)i;
    uint8_t P[16] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xaa,0xbb,0xcc,0xdd,0xee,0xff};
    uint8_t C[16] = {0x8e,0xa2,0xb7,0xca,0x51,0x67,0x45,0xbf,0xea,0xfc,0x49,0x90,0x4b,0x49,0x60,0x89};
    AES256KEY ks;
    expand256(key, &ks);
    __m128i r = dec_block(&ks, _mm_loadu_si128((const __m128i *)C));
    _mm_storeu_si128((__m128i *)out, r);
    printf("expect: ");
    for (int i = 0; i < 16; i++) printf("%02x", P[i]);
    printf("\ngot   : ");
    for (int i = 0; i < 16; i++) printf("%02x", out[i]);
    printf("\n%s\n", memcmp(out, P, 16) == 0 ? "AES-256 DEC OK" : "AES-256 DEC FAIL");
    (void)pt; (void)ct;
    return memcmp(out, P, 16) == 0 ? 0 : 1;
}
