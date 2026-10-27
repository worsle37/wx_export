import sqlite3, hashlib, zstandard as zstd
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
t="Msg_"+hashlib.md5(b"10000000000@chatroom").hexdigest()
found=0
for lid,lt,ct,c in cur.execute(f"SELECT local_id, local_type, WCDB_CT_message_content, message_content FROM {t}"):
    d=c
    if ct==4:
        try: d=zstd.ZstdDecompressor().decompress(d, max_output_size=1<<22)
        except Exception: continue
    try: s=d.decode("utf-8","replace")
    except Exception: continue
    if "songalbumurl" in s:
        print("local_id",lid,"type",lt,"base",lt&0xFFFF,"preview",repr(s[:160]))
        found+=1
        if found>=2: break
con.close()
