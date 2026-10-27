# -*- coding: utf-8 -*-
"""
微信 4.1.10+ 「零驻留」版本密钥提取尝试：
在 com.Tencent.WCDB.Config.Cipher 字符串附近枚举候选 passphrase，
用 PBKDF2-HMAC-SHA512(pass, db_salt, 256000) 派生 enc_key，
再用 AES-256-CBC 解页 1 首块，与 "SQLite format 3\\0" 比对判定。
"""
import struct, sys, os, multiprocessing as mp
from hashlib import pbkdf2_hmac
from Crypto.Cipher import AES

DB = sys.argv[1]
DUMP = sys.argv[2]
WIN = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x1000
STRIDE = 4

with open(DB, "rb", buffering=0) as f:
    page1 = f.read(4096)
SALT = page1[:16]
C1 = page1[16:32]
IV = page1[4016:4032]
WANT = bytes(a ^ b for a, b in zip(b"SQLite format 3\x00", IV))


def check(pass_bytes):
    enc = pbkdf2_hmac("sha512", pass_bytes, SALT, 256000, 32)
    if AES.new(enc, AES.MODE_ECB).decrypt(C1) == WANT:
        return (pass_bytes.hex(), enc.hex())
    return None


def main():
    data = open(DUMP, "rb").read()
    marker = b"com.Tencent.WCDB.Config.Cipher"
    hits, st = [], 0
    while True:
        i = data.find(marker, st)
        if i < 0:
            break
        hits.append(i); st = i + 1
    print("marker hits:", [hex(h) for h in hits], flush=True)

    # 结构提示：附近是否出现 256000 / 4096（kdf_iter / page_size）
    for h in hits[:3]:
        lo, hi = max(0, h - 0x400), min(len(data), h + 0x400)
        seg = data[lo:hi]
        it = struct.pack("<i", 256000)
        pos = [lo + j for j in range(len(seg)) if seg[j:j+4] == it]
        print(f"hit {hex(h)}: 256000@ {[hex(p) for p in pos]}", flush=True)

    cands, seen = [], set()
    for h in hits:
        lo, hi = max(0, h - WIN), min(len(data), h + WIN)
        for j in range(lo, hi - 32, STRIDE):
            c = bytes(data[j:j + 32])
            if c in seen:
                continue
            seen.add(c); cands.append(c)
    print("candidates:", len(cands), flush=True)

    with mp.Pool(min(14, os.cpu_count())) as pool:
        for r in pool.imap_unordered(check, cands, chunksize=4):
            if r:
                print("PASSPHRASE FOUND:", r[0], "enc_key:", r[1], flush=True)


if __name__ == "__main__":
    main()
