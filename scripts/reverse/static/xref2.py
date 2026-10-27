import pefile, struct
DLL=r"C:\Program Files\Tencent\Weixin\4.1.15.13\Weixin.dll"
pe=pefile.PE(DLL, fast_load=True)
raw=open(DLL,"rb").read()
secs=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress,s.SizeOfRawData,s.PointerToRawData) for s in pe.sections]
t=[s for s in secs if s[0]==".text"][0]; tex=raw[t[3]:t[3]+t[2]]; tva=t[1]
def str_rvas(s):
    out=[]; p=raw.find(s)
    while p>=0:
        for n,va,rsz,praw in secs:
            if praw<=p<praw+rsz: out.append(p-praw+va)
        p=raw.find(s,p+1)
    return out
def xrefs(rva):
    hits=[]
    for pre in (0x48,0x4C):
        for op in (0x8D,0x8B):
            needle=bytes([pre,op]); i=0
            while True:
                i=tex.find(needle,i)
                if i<0: break
                modrm=tex[i+2]
                if (modrm & 0xC7)==0x05:
                    disp=struct.unpack_from("<i",tex,i+3)[0]
                    if tva+i+7+disp==rva: hits.append(tva+i)
                i+=1
    return hits
for s in (b"kdf_iter", b"cipher_page_size", b"com.Tencent.WCDB.Config.Cipher"):
    for r in str_rvas(s)[:2]:
        h=xrefs(r)
        print(s.decode(), hex(r), "->", [hex(x) for x in h][:6])
        for x in h[:3]:
            off=x-tva; back=max(0,off-0x600); seg=tex[back:off]; cand=None
            for j in range(len(seg)-4,-1,-1):
                if seg[j:j+4]==b"\xCC\xCC\xCC\xCC": cand=tva+back+j+4; break
            print("   func~", hex(cand) if cand else "?")
