import sqlite3, hashlib, zstandard as zstd, re
TAG = re.compile(r"<(\w+)>(.*?)</\1>", re.S)
s = '<msg><appmsg appid="wxDEMO0000000000" sdkver="0"><title>示例文件.zip</title><des></des><action></action><type>6</type></appmsg></msg>'
print("fields:", {k:v for k,v in TAG.findall(s)})
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
t="Msg_"+hashlib.md5(b"wxid_demo0002").hexdigest()
row=cur.execute(f"SELECT local_type,WCDB_CT_message_content,message_content FROM {t} WHERE (local_type&65535)=49 LIMIT 1").fetchone()
lt,ct,c=row
d=zstd.ZstdDecompressor().decompress(c, max_output_size=1<<22) if ct==4 else c
txt=d.decode("utf-8","replace")
print("local_type:", lt, "&0xFFFF =", lt & 0xFFFF)
print("fields from row:", {k:v[:30] for k,v in TAG.findall(txt)})
con.close()
