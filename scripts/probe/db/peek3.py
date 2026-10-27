import sqlite3, hashlib, zstandard as zstd
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
t="Msg_"+hashlib.md5(b"10000000000@chatroom").hexdigest()
rows=cur.execute(f"SELECT local_id, local_type, WCDB_CT_message_content, message_content FROM {t} WHERE message_content LIKE '%songalbumurl%' LIMIT 3").fetchall()
for lid,lt,ct,c in rows:
    d=c
    if ct==4:
        d=zstd.ZstdDecompressor().decompress(d, max_output_size=1<<22)
    s=d.decode("utf-8","replace")
    print("local_id",lid,"type",lt,"&0xFFFF",lt & 0xFFFF,"ct",ct,"len",len(s))
    print(repr(s[:150]))
con.close()
