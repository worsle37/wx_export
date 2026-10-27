# -*- coding: utf-8 -*-
"""验证 hook 抓到的内存窗口里是否包含 passphrase / enc_key"""
import json, sys, os, collections, multiprocessing as mp
from hashlib import pbkdf2_hmac
from Crypto.Cipher import AES

HITS = r"<PROJECT>\wx_hits2.jsonl"
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ["TEMP"], "wxprobe.db")

page1 = open(DB, "rb", buffering=0).read(4096)
SALT = page1[:16]
C1 = page1[16:32]
IV = page1[4016:4032]
WANT = bytes(a ^ b for a, b in zip(b"SQLite format 3\x00", IV))


def work(cand):
    try:
        if AES.new(cand, AES.MODE_ECB).decrypt(C1) == WANT:
            return ("ENC_KEY", cand.hex())
    except Exception:
        return None
    enc = pbkdf2_hmac("sha512", cand, SALT, 256000, 32)
    if AES.new(enc, AES.MODE_ECB).decrypt(C1) == WANT:
        return ("PASSPHRASE", cand.hex(), enc.hex())
    return None


def looks_random(b):
    if len(set(b)) < 10:
        return False
    printable = sum(1 for x in b if 32 <= x < 127)
    return printable < 20


def main():
    dumps = []
    for line in open(HITS, encoding="utf-8"):
        try:
            m = json.loads(line)
        except Exception:
            continue
        p = m.get("payload") or {}
        if "hex" in p:
            dumps.append(bytes(p["hex"]))
    print("dumps:", len(dumps), flush=True)

    cands, seen = [], set()
    for buf in dumps:
        for off in range(0, len(buf) - 32 + 1, 4):
            c = buf[off:off + 32]
            if c in seen or not looks_random(c):
                continue
            seen.add(c); cands.append(c)
    print("candidates:", len(cands), flush=True)

    with mp.Pool(min(14, os.cpu_count())) as pool:
        for r in pool.imap_unordered(work, cands, chunksize=2):
            if r:
                print("FOUND:", r, flush=True)


if __name__ == "__main__":
    main()
