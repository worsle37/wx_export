import sqlite3, hashlib
for db in [r"decrypted\message\message_0.db", r"decrypted\message\message_1.db", r"decrypted\message\message_2.db"]:
    con=sqlite3.connect(db); cur=con.cursor()
    print("==", db)
    print(" Name2Id cols:", [r[1] for r in cur.execute("PRAGMA table_info(Name2Id)")])
    tabs=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")]
    for u in ["wxid_demo0002","10000000000@chatroom"]:
        t="Msg_"+hashlib.md5(u.encode()).hexdigest()
        if t in tabs:
            n,=cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
            print("  ", u, n)
    con.close()
