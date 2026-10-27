import sqlite3, hashlib, zstandard as zstd
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
for label,u in [("demo","wxid_demo0002"),("group","10000000000@chatroom")]:
    t="Msg_"+hashlib.md5(u.encode()).hexdigest()
    print("=====",label)
    for lt,ct,content in cur.execute(f"SELECT local_type, WCDB_CT_message_content, message_content FROM {t} WHERE (local_type & 65535)=49 LIMIT 3"):
        d=content
        if ct==4: d=zstd.ZstdDecompressor().decompress(d, max_output_size=1<<22)
        print("[49]", d.decode("utf-8","replace")[:260].replace("\n"," "))
    for lt,ct,content in cur.execute(f"SELECT local_type, WCDB_CT_message_content, message_content FROM {t} WHERE (local_type & 65535)=3 LIMIT 2"):
        d=content
        if ct==4: d=zstd.ZstdDecompressor().decompress(d, max_output_size=1<<22)
        print("[3]", d.decode("utf-8","replace")[:200].replace("\n"," "))
con.close()
