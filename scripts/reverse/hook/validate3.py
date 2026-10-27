# -*- coding: utf-8 -*-
"""验证第二轮抓到的候选：先当 enc_key 试，再当 passphrase 做 PBKDF2"""
import json, os, sys, multiprocessing as mp
from hashlib import pbkdf2_hmac
from Crypto.Cipher import AES

HITS = r"<PROJECT>\wx_hits3.jsonl"
DB = os.path.join(os.environ["TEMP"], "wxprobe.db")
page1 = open(DB, "rb", buffering=0).read(4096)
SALT, C1, IV = page1[:16], page1[16:32], page1[4016:4032]
WANT = bytes(a ^ b for a, b in zip(b"SQLite format 3\x00", IV))


def work(c):
    try:
        if AES.new(c, AES.MODE_ECB).decrypt(C1) == WANT:
            return ("ENC_KEY", c.hex())
    except Exception:
        pass
    enc = pbkdf2_hmac("sha512", c, SALT, 256000, 32)
    if AES.new(enc, AES.MODE_ECB).decrypt(C1) == WANT:
        return ("PASSPHRASE", c.hex(), enc.hex())
    return None


def main():
    seen, cands = set(), []
    for line in open(HITS, encoding="utf-8"):
        try:
            m = json.loads(line)
        except Exception:
            continue
        if "hex" not in m:
            continue
        c = bytes(m["hex"])
        if len(c) != 32 or c in seen:
            continue
        if len(set(c)) < 14:
            continue
        seen.add(c); cands.append(c)
    print("unique candidates:", len(cands), flush=True)
    with mp.Pool(min(14, os.cpu_count())) as pool:
        for i, r in enumerate(pool.imap_unordered(work, cands, chunksize=4)):
            if r:
                print("FOUND:", r, flush=True)
            if i % 2000 == 0:
                print("  ...", i, flush=True)


if __name__ == "__main__":
    main()
