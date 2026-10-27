import sqlite3, hashlib
con=sqlite3.connect(r"decrypted\message\message_0.db"); cur=con.cursor()
for u in ["wxid_demo0002","10000000000@chatroom"]:
    t="Msg_"+hashlib.md5(u.encode()).hexdigest()
    n,=cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
    types=cur.execute(f"SELECT local_type, COUNT(*) FROM {t} GROUP BY local_type ORDER BY 2 DESC LIMIT 8").fetchall()
    ct=cur.execute(f"SELECT WCDB_CT_message_content, COUNT(*) FROM {t} GROUP BY 1").fetchall()
    rng=cur.execute(f"SELECT MIN(create_time), MAX(create_time) FROM {t}").fetchone()
    print(u, "rows", n, "types", types, "ct", ct, "range", rng)
cur.execute("SELECT rowid,user_name,is_group FROM Name2Id LIMIT 5")
print("Name2Id sample", cur.execute("SELECT rowid,user_name,is_group FROM Name2Id LIMIT 5").fetchall())
con.close()
