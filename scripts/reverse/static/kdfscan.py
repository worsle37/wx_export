import pefile, struct
DLL=r"C:\Program Files\Tencent\Weixin\4.1.15.13\Weixin.dll"
pe=pefile.PE(DLL, fast_load=True)
raw=open(DLL,"rb").read()
secs=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress,s.SizeOfRawData,s.PointerToRawData) for s in pe.sections]
def rva(p):
    for n,va,rsz,praw in secs:
        if praw<=p<praw+rsz: return n, p-praw+va
    return None,None
t=[s for s in secs if s[0]==".text"][0]
tex=raw[t[3]:t[3]+t[2]]; tva=t[1]
# immediate 256000 little endian
pat=b"\x00\xe8\x03\x00"
locs=[]; i=0
while True:
    i=tex.find(pat,i)
    if i<0: break
    locs.append(tva+i); i+=1
print("256000 immediate hits:", len(locs), [hex(x) for x in locs[:20]])
# 相关字符串
for s in (b"PBKDF2", b"pbkdf2", b"hmac_sha512", b"cipher_page_size", b"cipher_plaintext_header_size", b"kdf_iter"):
    p=raw.find(s); print(s.decode(), "->", hex(rva(p)[1]) if p>=0 else "none")
