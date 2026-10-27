import re, glob, time, hashlib
for f in sorted(glob.glob("mem/pid_*.bin")):
    d = open(f,"rb").read()
    for pat in (b"com.Tencent.WCDB.Config.Cipher", b"Config.Cipher", b"MMV1", b"com.tencent.wcdb"):
        n = d.count(pat)
        if n: print(f, pat.decode(), n)
t=time.time(); hashlib.pbkdf2_hmac("sha512", b"x"*32, b"y"*16, 256000, 32); print("pbkdf2 1x: %.3fs"%(time.time()-t))
