import sqlite3, os
con=sqlite3.connect(r"decrypted\session\session.db"); con.text_factory=bytes; cur=con.cursor()
cols=[r[1] for r in cur.execute("PRAGMA table_info(SessionTable)")] if cur.execute("SELECT name FROM sqlite_master WHERE name='SessionTable'").fetchone() else []
print("session cols:", cols[:12])
if cols:
    q="SELECT * FROM SessionTable WHERE username LIKE ?"
    rows=cur.execute(q, (b"%l7p2s61kqmv222%",)).fetchall()
    print("session rows:", len(rows))
    for r in rows[:2]:
        d=dict(zip(cols, r))
        for k in ("username","last_timestamp","summary","unread_count","sort_timestamp"):
            v=d.get(k)
            if isinstance(v,bytes): v=v.decode("utf-8","replace")
            print("   ",k,"=",str(v)[:80])
con.close()
# 各 db 的 Msg_ 表数量 + 是否存在该 md5
import hashlib
t="Msg_"+hashlib.md5(b"wxid_demo0001").hexdigest()
print("looking for", t)
for p in [r"decrypted\message\message_0.db", r"decrypted\message\message_1.db", r"decrypted\message\message_2.db"]:
    if os.path.exists(p):
        c=sqlite3.connect(p)
        n=c.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'").fetchone()[0]
        has=c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
        print(p, "Msg_ tables:", n, "has target:", bool(has))
        c.close()
