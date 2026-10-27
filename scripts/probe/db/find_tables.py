import sqlite3, hashlib
users={"示例会话C":"wxid_demo0002","group":"10000000000@chatroom"}
for k,u in users.items():
    print(k, u, "->", "Msg_"+hashlib.md5(u.encode()).hexdigest())
con=sqlite3.connect(r"decrypted\message\message_0.db")
cur=con.cursor()
tabs=[r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")]
print("Msg_ tables in message_0:", len(tabs))
for k,u in users.items():
    t="Msg_"+hashlib.md5(u.encode()).hexdigest()
    print(k, t, "exists:", t in tabs)
cur.execute("PRAGMA table_info("+tabs[0]+")")
print("cols:", [r[1] for r in cur.fetchall()])
conv="10000000000@chatroom"
t="Msg_"+hashlib.md5(conv.encode()).hexdigest()
if t in tabs:
    rows=cur.execute(f"SELECT local_id,local_type,real_sender_id,create_time,WCDB_CT_message_content,message_content FROM {t} ORDER BY create_time DESC LIMIT 3").fetchall()
    for r in rows: print([str(x)[:80] for x in r])
con.close()
