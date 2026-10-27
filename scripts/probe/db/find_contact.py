import sqlite3, hashlib, os, glob
db=r"decrypted\contact\contact.db"
con=sqlite3.connect(db)
cur=con.cursor()
print("tables:", [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")][:20])
cur.execute("PRAGMA table_info(contact)")
print("contact cols:", [r[1] for r in cur.fetchall()])
for kw in ["demo", "示例"]:
    q="SELECT username,nick_name,remark FROM contact WHERE nick_name LIKE ? OR remark LIKE ? OR username LIKE ?"
    rows=cur.execute(q,(f"%{kw}%",f"%{kw}%",f"%{kw}%")).fetchall()
    print(f"\n== {kw}: {len(rows)}")
    for r in rows[:10]: print("   ", r)
con.close()
