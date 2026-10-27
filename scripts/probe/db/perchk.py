import sqlite3, glob, os
t="Msg_demo"
for p in sorted(glob.glob(r"decrypted\message\message_[0-9]*.db")):
    con=sqlite3.connect(p)
    has=con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
    if has:
        n,mn,mx=con.execute(f"SELECT COUNT(*),MIN(create_time),MAX(create_time) FROM {t}").fetchone()
        ids=con.execute(f"SELECT MIN(local_id),MAX(local_id) FROM {t}").fetchone()
        import time
        print(os.path.basename(p), n, "local_id", ids, "range", time.strftime('%Y-%m-%d',time.localtime(mn)), time.strftime('%Y-%m-%d',time.localtime(mx)))
    con.close()
