import sqlite3, hashlib, zstandard as zstd
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
t="Msg_"+hashlib.md5(b"wxid_demo0002").hexdigest()
for lt,ct,content,ctime in cur.execute(f"SELECT local_type,WCDB_CT_message_content,message_content,create_time FROM {t} WHERE (local_type&65535)=49 AND create_time BETWEEN 1767773000 AND 1767773300 LIMIT 6"):
    d=content
    if ct==4:
        try: d=zstd.ZstdDecompressor().decompress(d, max_output_size=1<<22)
        except Exception as e: d=b"<decompress fail>"
    print(lt, ct, ctime, repr(d[:120]))
con.close()
