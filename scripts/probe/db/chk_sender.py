import sqlite3, hashlib
con=sqlite3.connect(r"decrypted\message\message_0.db"); con.text_factory=bytes; cur=con.cursor()
t="Msg_"+hashlib.md5(b"wxid_demo0002").hexdigest()
print("sender ids:", cur.execute(f"SELECT real_sender_id, COUNT(*) FROM {t} GROUP BY 1").fetchall())
n2i={r[0]:(r[1].decode(errors="replace")) for r in cur.execute("SELECT rowid,user_name FROM Name2Id")}
for sid,_ in cur.execute(f"SELECT real_sender_id, COUNT(*) FROM {t} GROUP BY 1"):
    print(sid, "->", n2i.get(sid))
